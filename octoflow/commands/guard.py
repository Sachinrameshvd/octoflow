"""Guard and Install-Hooks CLI command for pre-commit security and AST syntax verification."""

import ast
import json
import re
import stat
import subprocess
from pathlib import Path

import typer
from rich.console import Console

from octoflow.themes import load_saved_theme

console = Console()


def run_guard(workspace: str = ".") -> bool:
    """Pre-commit security and AST syntax guard inspecting staged git changes."""
    theme = load_saved_theme()
    ws = Path(workspace).resolve()

    console.print(f"[{theme.rich_primary}]◈ OctoFlow Pre-Commit Swarm Guard[/{theme.rich_primary}]")

    # 1. Get staged files
    res = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], cwd=str(ws), capture_output=True, text=True
    )
    if res.returncode != 0:
        console.print("[dim]Not a git repository or git error. Guard skipped.[/dim]")
        return True

    staged_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
    if not staged_files:
        console.print(
            f"[{theme.rich_success}]✔ No staged git files to guard. Safe.[/{theme.rich_success}]"
        )
        return True

    console.print(
        f"[dim]Inspecting {len(staged_files)} staged file(s) for secrets and syntax errors...[/dim]"
    )

    SECRET_PATTERNS = [
        (re.compile(r"sk-ant-[a-zA-Z0-9_\-]{20,}"), "Exposed Anthropic API Key"),
        (re.compile(r"sk-[a-zA-Z0-9_\-]{30,}"), "Exposed OpenAI API Key"),
        (re.compile(r"ghp_[a-zA-Z0-9]{20,}"), "Exposed GitHub Personal Access Token"),
        (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "Exposed Private Key block"),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "Exposed AWS Access Key ID"),
    ]

    violations = []

    for rel_path in staged_files:
        target = ws / rel_path
        if not target.exists() or target.is_dir():
            continue

        try:
            content = target.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Check 1: Secret leaks (skip test suites and docs describing redacted patterns)
        is_test_or_doc = (
            rel_path.startswith("tests/")
            or rel_path.startswith("docs/")
            or rel_path == "octoflow/manual.py"
        )
        if not is_test_or_doc:
            for pat, desc in SECRET_PATTERNS:
                if pat.search(content):
                    violations.append(f"Security Alert: {desc} in staged file '{rel_path}'")

        # Check 2: Pre-flight AST Syntax check for Python
        if target.suffix == ".py":
            try:
                ast.parse(content, filename=rel_path)
            except SyntaxError as e:
                violations.append(
                    f"SyntaxError in staged '{rel_path}' at line {e.lineno}, col {e.offset}: {e.msg}"
                )

        # Check 3: JSON decode check
        elif target.suffix == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                violations.append(
                    f"JSONDecodeError in staged '{rel_path}' at line {e.lineno}: {e.msg}"
                )

    if violations:
        console.print(
            f"\n[{theme.rich_danger}]✖ Pre-Commit Guard Blocked Commit ({len(violations)} violation(s)):[/{theme.rich_danger}]"
        )
        for v in violations:
            console.print(f"  [{theme.rich_danger}]●[/{theme.rich_danger}] {v}")
        console.print("\n[dim]Fix the above issues or stage clean files before committing.[/dim]\n")
        return False

    console.print(
        f"[{theme.rich_success}]✔ Pre-Commit Guard: All {len(staged_files)} staged file(s) passed security & AST syntax checks. Commit allowed.[/{theme.rich_success}]"
    )
    return True


def install_git_hooks(workspace: str = ".") -> bool:
    """Install OctoFlow pre-commit guard into .git/hooks/pre-commit."""
    import os

    theme = load_saved_theme()
    ws = Path(workspace).resolve()
    git_dir = ws / ".git"

    if not git_dir.exists():
        console.print(
            f"[{theme.rich_danger}]Error: '{ws}' is not a git repository. Run 'git init' first.[/{theme.rich_danger}]"
        )
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    pre_commit_file = hooks_dir / "pre-commit"

    hook_script = "#!/bin/sh\n# OctoFlow Automated Pre-Commit Swarm Guard\noctos guard\n"
    pre_commit_file.write_text(hook_script, encoding="utf-8")

    st = os.stat(pre_commit_file)
    os.chmod(pre_commit_file, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)  # noqa: S103 - git pre-commit hook script requires executable bit permissions

    console.print(
        f"[{theme.rich_success}]✔ Installed OctoFlow Pre-Commit Guard at {pre_commit_file}[/{theme.rich_success}]"
    )
    console.print(
        "[dim]Every future 'git commit' will now automatically verify secrets and AST syntax.[/dim]\n"
    )
    return True


def guard_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory"),
):
    """Run pre-commit secret leak and AST syntax verification on staged git files."""
    safe = run_guard(workspace=workspace)
    if not safe:
        raise typer.Exit(code=1)


def install_hooks_cli_cmd(
    workspace: str = typer.Option(
        ".", "--dir", "-d", help="Workspace directory with .git repository"
    ),
):
    """Install automated OctoFlow pre-commit hook into .git/hooks/."""
    ok = install_git_hooks(workspace=workspace)
    if not ok:
        raise typer.Exit(code=1)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register guard and install-hooks commands with Typer apps."""
    app.command("guard")(guard_cli_cmd)
    octos_app.command("guard")(guard_cli_cmd)
    app.command("install-hooks")(install_hooks_cli_cmd)
    octos_app.command("install-hooks")(install_hooks_cli_cmd)
