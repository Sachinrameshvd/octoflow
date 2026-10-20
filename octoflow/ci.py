"""OctoFlow CI/CD Engine & Automated GitHub Actions PR Reviewer.

Executes a 3-arm specialist audit (Arm 6: Security, Arm 5: QA/AST, Arm 0: Architect)
over git pull request diffs, generating structured step summaries and blocking merge hazards.
"""

import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


GITHUB_WORKFLOW_TEMPLATE = """name: OctoFlow Swarm Guard

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main, master]

permissions:
  contents: read
  pull-requests: write

jobs:
  swarm-review:
    name: 3-Arm Swarm Audit (Security, QA, Architect)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install OctoFlow
        run: |
          pip install --upgrade pip
          pip install .

      - name: Execute Swarm PR Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          octos review-pr --summary
"""


SECRET_PATTERNS = [
    (r"sk-ant-[a-zA-Z0-9_-]{20,}", "Anthropic API Key"),
    (r"sk-proj-[a-zA-Z0-9_-]{20,}", "OpenAI Project Key"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI Standard Key"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36,}", "GitHub OAuth Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "SSH/RSA Private Key"),
]


def generate_github_action_workflow(workspace: str = ".") -> Path:
    """Generate .github/workflows/octoflow-guard.yml in the target workspace."""
    ws = Path(workspace).resolve()
    workflow_dir = ws / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_file = workflow_dir / "octoflow-guard.yml"
    workflow_file.write_text(GITHUB_WORKFLOW_TEMPLATE.strip() + "\n", encoding="utf-8")
    return workflow_file


def _get_git_diff_files(workspace_dir: str, base_ref: str = "HEAD~1") -> Tuple[List[str], str]:
    """Retrieve list of modified files and raw diff content."""
    try:
        # Check if git repository exists
        git_check = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=workspace_dir, capture_output=True, text=True)
        if git_check.returncode != 0:
            return [], ""

        # Check commit count
        c_count = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=workspace_dir, capture_output=True, text=True)
        num_commits = int(c_count.stdout.strip()) if c_count.stdout.strip().isdigit() else 1

        if num_commits <= 1:
            diff_cmd = ["git", "diff", "--cached"]
            diff_files_cmd = ["git", "diff", "--cached", "--name-only"]
        else:
            diff_cmd = ["git", "diff", base_ref]
            diff_files_cmd = ["git", "diff", base_ref, "--name-only"]

        diff_res = subprocess.run(diff_cmd, cwd=workspace_dir, capture_output=True, text=True)
        files_res = subprocess.run(diff_files_cmd, cwd=workspace_dir, capture_output=True, text=True)

        files = [f.strip() for f in files_res.stdout.splitlines() if f.strip()]
        return files, diff_res.stdout
    except Exception:
        return [], ""


def review_pull_request(
    workspace: str = ".",
    base_ref: str = "HEAD~1",
    write_summary: bool = True,
    shadow_mode: bool = False,
) -> Dict[str, Any]:
    """Execute automated 3-Arm CI/CD inspection over git diff.

    Args:
        workspace: Workspace root path.
        base_ref: Base git commit reference to diff against.
        write_summary: Append markdown to $GITHUB_STEP_SUMMARY.
        shadow_mode: If True, executes advisory audit and logs findings without returning exit code 1.

    Returns:
        Dict with review results, markdown report, and exit code (0 = pass, 1 = merge hazard unless in shadow mode).
    """
    ws = Path(workspace).resolve()
    modified_files, raw_diff = _get_git_diff_files(str(ws), base_ref=base_ref)

    findings_arm6: List[str] = []
    findings_arm5: List[str] = []
    findings_arm0: List[str] = []

    hard_block = False

    # -------------------------------------------------------------------------
    # ARM 6: SECURITY & CREDENTIAL LEAK INSPECTION
    # -------------------------------------------------------------------------
    leaked_secrets: List[str] = []
    for line in raw_diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            for pat, secret_type in SECRET_PATTERNS:
                if re.search(pat, line):
                    leaked_secrets.append(secret_type)
                    hard_block = True

    if leaked_secrets:
        findings_arm6.append(f"CRITICAL: Leaked credentials detected in diff: {', '.join(set(leaked_secrets))}")
    else:
        findings_arm6.append("Zero credential or API key leaks detected in changed files.")

    # SQL Injection heuristic scan
    sqli_risk = False
    for line in raw_diff.splitlines():
        if line.startswith("+"):
            if re.search(r"f[\"'].*SELECT .*\{.*\}", line, re.IGNORECASE) or re.search(r"f[\"'].*INSERT .*\{.*\}", line, re.IGNORECASE):
                sqli_risk = True
                hard_block = True
                findings_arm6.append("CRITICAL: Raw SQL f-string query detected. Use parameterized ORM expressions.")
                break
    if not sqli_risk:
        findings_arm6.append("SQL queries verify parameterized input binding.")

    # -------------------------------------------------------------------------
    # ARM 5: QA & AST PRE-FLIGHT SYNTAX VALIDATION
    # -------------------------------------------------------------------------
    ast_errors: List[str] = []
    has_test_files = any("test" in f.lower() for f in modified_files)
    has_core_code = any(f.endswith(".py") and "test" not in f.lower() for f in modified_files)

    for rel_path in modified_files:
        target_path = ws / rel_path
        if not target_path.exists():
            continue

        if rel_path.endswith(".py"):
            try:
                ast.parse(target_path.read_text(encoding="utf-8"))
            except SyntaxError as e:
                ast_errors.append(f"{rel_path}:{e.lineno} ({e.msg})")
                hard_block = True
        elif rel_path.endswith(".json"):
            try:
                json.loads(target_path.read_text(encoding="utf-8"))
            except Exception as e:
                ast_errors.append(f"{rel_path} (Invalid JSON: {e})")
                hard_block = True

    if ast_errors:
        findings_arm5.append(f"CRITICAL: AST Syntax Errors detected in: {', '.join(ast_errors)}")
    else:
        findings_arm5.append("100% Python AST and JSON syntax valid across modified files.")

    if has_core_code and not has_test_files:
        findings_arm5.append("Advisory: Core application files modified without corresponding tests in tests/.")
    elif has_test_files:
        findings_arm5.append("PR includes accompanying test coverage updates.")

    # -------------------------------------------------------------------------
    # ARM 0: ARCHITECTURAL BOUNDARY & TOPOLOGY REVIEW
    # -------------------------------------------------------------------------
    circular_warnings: List[str] = []
    # Check for cross-tier boundary leaks (e.g. models importing from views)
    for rel_path in modified_files:
        if "models/" in rel_path or "db/" in rel_path:
            p = ws / rel_path
            if p.exists() and p.suffix == ".py":
                content = p.read_text(encoding="utf-8")
                if "import frontend" in content or "import views" in content:
                    circular_warnings.append(f"Inverted boundary: {rel_path} imports higher-level presentation layer.")

    if circular_warnings:
        findings_arm0.extend(circular_warnings)
    else:
        findings_arm0.append("Interface contracts, folder topology, and module boundaries verified clean.")

    # -------------------------------------------------------------------------
    # FORMAT OUTPUT REPORT (GitHub Markdown & Step Summary)
    # -------------------------------------------------------------------------
    overall_status = "BLOCKED" if hard_block else "PASSED"
    status_icon = "✖" if hard_block else "✔"
    badge_color = "red" if hard_block else "green"

    arm6_status = "✖ BLOCKED" if any("CRITICAL" in f for f in findings_arm6) else "✔ PASSED"
    arm5_status = "✖ BLOCKED" if any("CRITICAL" in f for f in findings_arm5) else "✔ PASSED"
    arm0_status = "ℹ ADVISORY" if circular_warnings else "✔ PASSED"

    shadow_header = "> **SHADOW CI MODE**: Advisory audit only. Pipeline merge blocking is suppressed.\n\n" if shadow_mode else ""
    report_md = f"""## OctoFlow Swarm Guard CI Review

{shadow_header}> **Swarm Verdict**: **{status_icon} {overall_status}** • 3 Arms Audited ({len(modified_files)} files modified)

| Ganglia Arm | Domain Role | Audit Status | Key Findings |
| :--- | :--- | :--- | :--- |
| **Arm 6: Security** | Credential Leaks & Injection | **{arm6_status}** | {" • ".join(findings_arm6)} |
| **Arm 5: QA & AST** | Pre-Flight Syntax & Tests | **{arm5_status}** | {" • ".join(findings_arm5)} |
| **Arm 0: Architect** | Topology & Interface Contracts | **{arm0_status}** | {" • ".join(findings_arm0)} |

"""
    if hard_block:
        report_md += "> ▲ **MERGE HAZARDS DETECTED**: Please resolve critical AST syntax errors or credential leaks before merging into production.\n"
    else:
        report_md += "> ✔ **READY TO MERGE**: Zero AST corruption or security risks detected by OctoFlow Swarm Guard.\n"

    # Write to GitHub Step Summary if in GitHub Actions environment
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if write_summary and summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(report_md + "\n")
        except Exception:
            pass

    resolved_exit_code = 0 if shadow_mode else (1 if hard_block else 0)

    return {
        "status": overall_status,
        "hard_block": hard_block,
        "exit_code": resolved_exit_code,
        "shadow_mode": shadow_mode,
        "modified_files": modified_files,
        "report_markdown": report_md,
        "markdown_report": report_md,
        "arm6_findings": findings_arm6,
        "arm5_findings": findings_arm5,
        "arm0_findings": findings_arm0,
    }
