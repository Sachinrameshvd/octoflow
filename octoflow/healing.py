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
from octoflow.logging_config import get_logger
from octoflow.errors import BudgetExceeded

logger = get_logger("healing")


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
        except Exception as e:
            logger.debug("Failed parsing package.json for test script in %s: %s", ws, e)  # best-effort: malformed package.json

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


def extract_failure_signature(parsed_failures: List[Dict[str, Any]], raw_output: str) -> Tuple[Tuple[str, str], ...]:
    """Extract a normalized tuple signature of (test_id, error_type) pairs."""
    if not parsed_failures:
        tail = raw_output.strip().splitlines()[-1] if raw_output.strip() else "unknown"
        return (("suite", tail[:120]),)
    sig_items = []
    for f in parsed_failures:
        test_id = f"{f.get('file', '')}::{f.get('test_name', '') or ''}"
        err = f.get("error", "").strip()
        m = re.match(r"^([A-Za-z0-9_]+(?:Error|Exception))", err)
        if m:
            err_type = m.group(1)
        elif ":" in err:
            err_type = err.split(":", 1)[0].strip()
        else:
            err_type = err.split()[0] if err else "Error"
        sig_items.append((test_id, err_type))
    return tuple(sorted(sig_items))


def count_failing_tests(parsed_failures: List[Dict[str, Any]], raw_output: str) -> int:
    """Count unique failing tests from parsed failures or raw output."""
    if parsed_failures:
        unique_ids = {f"{f.get('file', '')}::{f.get('test_name', '') or ''}" for f in parsed_failures}
        return len(unique_ids)
    m = re.search(r"(\d+)\s+failed", raw_output)
    if m:
        return int(m.group(1))
    return 1 if raw_output.strip() else 0


def self_heal_workspace(
    workspace_dir: str = ".",
    max_attempts: Optional[int] = None,
    custom_cmd: Optional[List[str]] = None,
    config: Optional[OctoFlowConfig] = None,
    budget_tracker: Optional[Any] = None,
) -> Dict[str, Any]:
    """Execute autonomous closed-loop test repair with budget and repetition enforcement.

    1. Executes detected test suite.
    2. If tests pass, returns immediately with success.
    3. If tests fail, parses traceback and deploys Arm 5 (QA) and Arm 2 (Backend)
       to formulate a targeted patch.
    4. Validates patch AST before writing to prevent syntax degradation.
    5. Re-runs tests in a closed loop until 100% pass, max attempts reached,
       repetition detected, or failing count fails to decrease over 2 iterations.
    """
    ws = Path(workspace_dir).resolve()
    fw_info = detect_test_framework(str(ws))
    fw_name = fw_info[0] if fw_info else "pytest"
    cmd = custom_cmd or (fw_info[1] if fw_info else ["pytest", "-q"])

    sandbox = WorkspaceSandbox(str(ws))
    if budget_tracker is not None:
        sandbox.set_budget_tracker(budget_tracker)

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
            "stop_reason": "all_passed",
            "history": [],
            "final_output": full_log,
        }

    cfg = config or OctoFlowConfig(workspace_dir=str(ws))
    limit = max_attempts if max_attempts is not None else (cfg.budget.max_heal_iterations if hasattr(cfg, "budget") else 5)

    initial_failures = parse_pytest_failures(full_log)
    initial_sig = extract_failure_signature(initial_failures, full_log)
    initial_count = count_failing_tests(initial_failures, full_log)

    signature_history: List[Tuple[Tuple[str, str], ...]] = []
    iterations_without_decrease: int = 0
    prev_failing_count: int = initial_count
    stop_reason: str = "max_iterations_reached"
    attempts_used: int = 0

    for attempt in range(1, limit + 1):
        attempts_used = attempt
        if budget_tracker is not None:
            try:
                budget_tracker.check_wall_time()
                budget_tracker.check_heal_iteration()
            except BudgetExceeded as be:
                stop_reason = "budget_exceeded"
                return {
                    "success": False,
                    "attempts": attempt - 1,
                    "framework": fw_name,
                    "repaired_files": repaired_files,
                    "message": f"Healing stopped: budget limit exceeded: {be.limit_name}",
                    "stop_reason": stop_reason,
                    "history": history,
                    "final_output": full_log,
                }

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
        if budget_tracker is not None:
            try:
                budget_tracker.check_wall_time()
                budget_tracker.check_llm_call()
            except BudgetExceeded as be:
                stop_reason = "budget_exceeded"
                return {
                    "success": False,
                    "attempts": attempt - 1,
                    "framework": fw_name,
                    "repaired_files": repaired_files,
                    "message": f"Healing stopped: budget limit exceeded: {be.limit_name}",
                    "stop_reason": stop_reason,
                    "history": history,
                    "final_output": full_log,
                }
        resp = provider.generate(repair_prompt, system_prompt="You are an expert autonomous bug repair agent.")
        if budget_tracker is not None:
            budget_tracker.record_tokens(resp.total_tokens)

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
            try:
                sandbox.write_file(target_to_repair, patched_code)
                if target_to_repair not in repaired_files:
                    repaired_files.append(target_to_repair)
            except BudgetExceeded as be:
                stop_reason = "budget_exceeded"
                return {
                    "success": False,
                    "attempts": attempt,
                    "framework": fw_name,
                    "repaired_files": repaired_files,
                    "message": f"Healing stopped: budget limit exceeded: {be.limit_name}",
                    "stop_reason": stop_reason,
                    "history": history,
                    "final_output": full_log,
                }

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
                "stop_reason": "all_passed",
                "history": history,
                "final_output": full_log,
            }

        # Evaluate termination conditions
        current_failures = parse_pytest_failures(full_log)
        current_sig = extract_failure_signature(current_failures, full_log)
        current_count = count_failing_tests(current_failures, full_log)
        signature_history.append(current_sig)

        # Condition (b): same failing-test signature repeats twice in healing attempts
        if signature_history.count(current_sig) >= 2:
            stop_reason = "repetition_detected"
            break

        # Condition (c): total failing count does not decrease over 2 iterations
        if current_count >= prev_failing_count:
            iterations_without_decrease += 1
        else:
            iterations_without_decrease = 0
        prev_failing_count = current_count

        if iterations_without_decrease >= 2:
            stop_reason = "no_progress"
            break

    return {
        "success": False,
        "attempts": attempts_used,
        "framework": fw_name,
        "repaired_files": repaired_files,
        "message": f"Healing stopped ({stop_reason}): reached termination condition on attempt {attempts_used}.",
        "stop_reason": stop_reason,
        "history": history,
        "final_output": full_log,
    }
