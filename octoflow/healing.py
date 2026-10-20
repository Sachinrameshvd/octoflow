"""OctoFlow Closed-Loop Self-Healing Test Engine.

Automatically detects test runners (pytest, npm test, cargo test, go test),
intercepts stack traces, diagnoses failing assertions via Arm 5 (QA) & Arm 2 (Backend),
applies preflight-validated AST patches, and iterates in a closed loop until 100% green.
"""

import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from octoflow.config import OctoFlowConfig
from octoflow.tools import WorkspaceSandbox


def detect_test_framework(workspace_dir: str) -> Optional[Tuple[str, List[str]]]:
    """Detect workspace testing framework and execution command."""
    ws = Path(workspace_dir).resolve()

    if (ws / "pytest.ini").exists() or (ws / "tests").exists() or (ws / "pyproject.toml").exists() or (ws / "setup.py").exists():
        return ("pytest", ["pytest", "-q"])

    pkg_json = ws / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if "scripts" in data and "test" in data["scripts"]:
                return ("npm", ["npm", "test"])
        except Exception:
            pass

    if (ws / "Cargo.toml").exists():
        return ("cargo", ["cargo", "test"])

    if (ws / "go.mod").exists():
        return ("go", ["go", "test", "./..."])

    return None


def run_test_suite(workspace_dir: str, cmd: Optional[List[str]] = None, timeout: int = 60) -> Tuple[int, str, str]:
    """Execute test suite and capture exit code, stdout, and stderr."""
    ws = Path(workspace_dir).resolve()
    if not cmd:
        fw_info = detect_test_framework(str(ws))
        cmd = fw_info[1] if fw_info else ["pytest", "-q"]

    try:
        res = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Test run timed out after {timeout}s"
    except Exception as e:
        return 1, "", str(e)


def parse_pytest_failures(output: str) -> List[Dict[str, Any]]:
    """Parse failing test files, functions, lines, and error messages from pytest output."""
    failures = []
    lines = output.splitlines()

    current_failure = None
    for line in lines:
        # Match lines like "FAILED tests/test_auth.py::test_login - AssertionError: ..."
        m_failed = re.search(r"FAILED\s+([^\s:]+)::([^\s\-]+)\s*-\s*(.*)", line)
        if m_failed:
            failures.append({
                "file": m_failed.group(1),
                "test_name": m_failed.group(2),
                "error": m_failed.group(3).strip(),
                "line_no": None,
            })
            continue

        # Match line numbers like "tests/test_auth.py:42: AssertionError"
        m_line = re.search(r"([^\s:]+\.py):(\d+):\s*(.*Error.*)", line)
        if m_line:
            failures.append({
                "file": m_line.group(1),
                "test_name": None,
                "error": m_line.group(3).strip(),
                "line_no": int(m_line.group(2)),
            })

    return failures


def self_heal_workspace(
    workspace_dir: str = ".",
    max_attempts: int = 3,
    custom_cmd: Optional[List[str]] = None,
    config: Optional[OctoFlowConfig] = None,
) -> Dict[str, Any]:
    """Execute autonomous closed-loop test repair.

    1. Executes detected test suite.
    2. If tests pass, returns immediately with success.
    3. If tests fail, parses traceback and deploys Arm 5 (QA) and Arm 2 (Backend)
       to formulate a targeted patch.
    4. Validates patch AST before writing to prevent syntax degradation.
    5. Re-runs tests in a closed loop until 100% pass or max attempts exhausted.
    """
    ws = Path(workspace_dir).resolve()
    fw_info = detect_test_framework(str(ws))
    fw_name = fw_info[0] if fw_info else "pytest"
    cmd = custom_cmd or (fw_info[1] if fw_info else ["pytest", "-q"])

    sandbox = WorkspaceSandbox(str(ws))
    history: List[Dict[str, Any]] = []
    repaired_files: List[str] = []

    # Initial Run
    rc, stdout, stderr = run_test_suite(str(ws), cmd)
    full_log = stdout + "\n" + stderr

    if rc == 0:
        return {
            "success": True,
            "attempts": 0,
            "framework": fw_name,
            "repaired_files": [],
            "message": "All workspace tests are currently passing. Zero healing required.",
            "history": [],
            "final_output": full_log,
        }

    cfg = config or OctoFlowConfig(workspace_dir=str(ws))

    for attempt in range(1, max_attempts + 1):
        parsed_failures = parse_pytest_failures(full_log)
        failure_summary = parsed_failures[0] if parsed_failures else {
            "file": "tests", "test_name": "suite", "error": full_log[-300:]
        }

        target_file_rel = failure_summary.get("file", "")
        # Heuristic to find implementation file vs test file
        impl_candidates = []
        if target_file_rel.startswith("tests/test_") or target_file_rel.startswith("tests/"):
            base_name = Path(target_file_rel).name.replace("test_", "")
            for candidate in ws.rglob(base_name):
                if "tests" not in str(candidate):
                    impl_candidates.append(str(candidate.relative_to(ws)))

        target_to_repair = impl_candidates[0] if impl_candidates else target_file_rel
        target_path = ws / target_to_repair

        if not target_path.is_file():
            py_files = list(ws.glob("tests/*.py")) or list(ws.glob("*.py"))
            if py_files:
                target_path = py_files[0]
                target_to_repair = str(target_path.relative_to(ws))

        file_content = target_path.read_text(encoding="utf-8") if (target_path.exists() and target_path.is_file()) else ""

        # Formulate repair prompt for Arm 2 (Backend) and Arm 5 (QA)
        repair_prompt = f"""You are Arm 2 (Backend Logic) and Arm 5 (QA) of the OctoFlow Swarm.
A unit test failure occurred in the workspace:

Framework: {fw_name}
Failing File: {target_file_rel}
Error Details: {failure_summary.get('error', 'Assertion or runtime error')}
Target Implementation to Repair: {target_to_repair}

Existing Implementation:
```python
{file_content}
```

Task:
Fix the implementation so the test passes.
Output ONLY the complete, corrected python code for {target_to_repair}.
Do not include conversational filler or markdown notes around the code.
"""

        from octoflow.provider import get_llm_provider
        provider = get_llm_provider(cfg, tier="frontier")
        resp = provider.generate(repair_prompt, system_prompt="You are an expert autonomous bug repair agent.")

        # Extract code from response
        patched_code = resp.content.strip()
        if "```python" in patched_code:
            patched_code = patched_code.split("```python", 1)[1].split("```", 1)[0].strip()
        elif "```" in patched_code:
            patched_code = patched_code.split("```", 1)[1].split("```", 1)[0].strip()

        # Pre-flight syntax validation before writing to protect workspace
        is_valid_ast = True
        if target_to_repair.endswith(".py"):
            try:
                ast.parse(patched_code)
            except SyntaxError:
                is_valid_ast = False

        if is_valid_ast and patched_code:
            sandbox.write_file(target_to_repair, patched_code)
            if target_to_repair not in repaired_files:
                repaired_files.append(target_to_repair)

        # Re-run tests to check if healed
        rc, stdout, stderr = run_test_suite(str(ws), cmd)
        full_log = stdout + "\n" + stderr

        history.append({
            "attempt": attempt,
            "target_file": target_to_repair,
            "failure": failure_summary,
            "ast_valid": is_valid_ast,
            "pass_after_repair": (rc == 0),
        })

        if rc == 0:
            return {
                "success": True,
                "attempts": attempt,
                "framework": fw_name,
                "repaired_files": repaired_files,
                "message": f"Autonomous healing succeeded on attempt {attempt}. 100% of tests passing.",
                "history": history,
                "final_output": full_log,
            }

    return {
        "success": False,
        "attempts": max_attempts,
        "framework": fw_name,
        "repaired_files": repaired_files,
        "message": f"Healing loop reached max attempts ({max_attempts}) without resolving all failures.",
        "history": history,
        "final_output": full_log,
    }
