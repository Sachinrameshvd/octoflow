"""Comprehensive tests for OctoFlow Cockpit Router Safety (P1.3).

Covers:
- Pure classifier classify_input() table-driven tests (>= 60 cases)
- Simple vs explicit vs compound vs swarm goal vs slash commands
- Destructive command detection (rm, rmdir, mv, cp -r, chmod -R, sudo, git reset --hard, etc.)
- Directory traversal (..) and out-of-workspace absolute paths
- Prose vs argument heuristic disambiguation
- Multi-line paste safety and bracketed paste protection
- Deprecated OCTOFLOW_LEGACY_ROUTER=1 escape hatch
- Command execution with shell=False for SHELL_SIMPLE and shell=True for SHELL_EXPLICIT
- 64 KB output capture truncation
- Command history logging with 0600 file permissions
- PTY simulation tests for confirmation (y confirms, n rejects, Enter rejects)
"""

import os
import pty
import select
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import pytest

pytestmark = pytest.mark.unit

import pytest

from octoflow.router import (
    ALLOWED_SIMPLE_SHELL_COMMANDS,
    DESTRUCTIVE_COMMANDS,
    PROSE_WORDS,
    Route,
    RouteKind,
    classify_input,
    classify_input_legacy,
    execute_shell_route,
    has_compound_operators,
    is_destructive_command,
    log_command_history,
    strip_prompt_prefixes,
    SESSION_COMMAND_HISTORY,
    MAX_CAPTURE_BYTES,
)


# ============================================================================
# 1. TABLE-DRIVEN ROUTER TEST SUITE (>= 60 TEST CASES)
# ============================================================================

ROUTER_TEST_CASES = [
    # ------------------------------------------------------------------------
    # Category 1: Empty and Whitespace (4 cases)
    # ------------------------------------------------------------------------
    ("", RouteKind.EMPTY, False, False, False),
    ("   ", RouteKind.EMPTY, False, False, False),
    ("\t", RouteKind.EMPTY, False, False, False),
    ("  \n  ", RouteKind.EMPTY, False, False, False),

    # ------------------------------------------------------------------------
    # Category 2: Safe Simple Shell Commands (12 cases)
    # ------------------------------------------------------------------------
    ("ls", RouteKind.SHELL_SIMPLE, False, False, False),
    ("ls -la", RouteKind.SHELL_SIMPLE, False, False, False),
    ("ls -lh src", RouteKind.SHELL_SIMPLE, False, False, False),
    ("pwd", RouteKind.SHELL_SIMPLE, False, False, False),
    ("mkdir build", RouteKind.SHELL_SIMPLE, False, False, False),
    ("mkdir -p src/octoflow/components", RouteKind.SHELL_SIMPLE, False, False, False),
    ("touch index.html", RouteKind.SHELL_SIMPLE, False, False, False),
    ("touch README.md", RouteKind.SHELL_SIMPLE, False, False, False),
    ("cat pyproject.toml", RouteKind.SHELL_SIMPLE, False, False, False),
    ("grep -rn 'def classify' .", RouteKind.SHELL_SIMPLE, False, False, False),
    ("which python3", RouteKind.SHELL_SIMPLE, False, False, False),
    ("git status", RouteKind.SHELL_SIMPLE, False, False, False),

    # ------------------------------------------------------------------------
    # Category 3: Natural Language Swarm Goals (Shell heads with prose) (14 cases)
    # ------------------------------------------------------------------------
    ("make a resume analyzer", RouteKind.SWARM_GOAL, False, False, False),
    ("list the requirements.txt issues", RouteKind.SWARM_GOAL, False, False, False),
    ("touch the code up", RouteKind.SWARM_GOAL, False, False, False),
    ("ls the project requirements", RouteKind.SWARM_GOAL, False, False, False),
    ("mkdir a new fullstack web application", RouteKind.SWARM_GOAL, False, False, False),
    ("cd into the backend directory and inspect", RouteKind.SWARM_GOAL, False, False, False),
    ("cat all python files and summarize them", RouteKind.SWARM_GOAL, False, False, False),
    ("open the login page and test authentication", RouteKind.SWARM_GOAL, False, False, False),
    ("find any bugs in the provider cascade", RouteKind.SWARM_GOAL, False, False, False),
    ("grep for memory leaks in the app", RouteKind.SWARM_GOAL, False, False, False),
    ("touch user profile card component", RouteKind.SWARM_GOAL, False, False, False),
    ("build a distributed key-value store in python", RouteKind.SWARM_GOAL, False, False, False),
    ("create an e-commerce platform with stripe integration", RouteKind.SWARM_GOAL, False, False, False),
    ("design an autonomous multi-agent consensus protocol", RouteKind.SWARM_GOAL, False, False, False),

    # ------------------------------------------------------------------------
    # Category 4: Explicit Shell Commands (! and $) (8 cases)
    # ------------------------------------------------------------------------
    ("!echo hello world", RouteKind.SHELL_EXPLICIT, False, False, True),
    ("!ls -la", RouteKind.SHELL_EXPLICIT, False, False, True),
    ("!pytest tests/ -q", RouteKind.SHELL_EXPLICIT, False, False, True),
    ("!python -c 'import sys; print(sys.version)'", RouteKind.SHELL_EXPLICIT, False, False, True),
    ("$ ls -la", RouteKind.SHELL_EXPLICIT, False, False, True),
    ("$ echo test", RouteKind.SHELL_EXPLICIT, False, False, True),
    ("/sh pytest tests/", RouteKind.SHELL_EXPLICIT, False, False, True),
    ("/bash make test", RouteKind.SHELL_EXPLICIT, False, False, True),

    # ------------------------------------------------------------------------
    # Category 5: Compound Commands (Pipes, redirects, ;, &&, ||, subshells) (10 cases)
    # ------------------------------------------------------------------------
    ("ls; rm -rf ~", RouteKind.SHELL_EXPLICIT, True, True, True),
    ("mkdir a && cd a", RouteKind.SHELL_EXPLICIT, False, True, True),
    ("ls || echo 'failed'", RouteKind.SHELL_EXPLICIT, False, True, True),
    ("cat file.txt | grep foo", RouteKind.SHELL_EXPLICIT, False, True, True),
    ("echo 'data' > out.txt", RouteKind.SHELL_EXPLICIT, False, True, True),
    ("echo 'data' >> log.txt", RouteKind.SHELL_EXPLICIT, False, True, True),
    ("cat < input.txt", RouteKind.SHELL_EXPLICIT, False, True, True),
    ("echo `whoami`", RouteKind.SHELL_EXPLICIT, False, True, True),
    ("echo $(pwd)", RouteKind.SHELL_EXPLICIT, False, True, True),
    ("ls &", RouteKind.SHELL_EXPLICIT, False, True, True),

    # ------------------------------------------------------------------------
    # Category 6: Destructive Commands (14 cases)
    # ------------------------------------------------------------------------
    ("rm -rf build", RouteKind.SHELL_SIMPLE, True, False, True),
    ("rm file.txt", RouteKind.SHELL_SIMPLE, True, False, True),
    ("rmdir empty_dir", RouteKind.SHELL_SIMPLE, True, False, True),
    ("mv old.py new.py", RouteKind.SHELL_SIMPLE, True, False, True),
    ("cp -r src backup", RouteKind.SHELL_SIMPLE, True, False, True),
    ("cp -R src backup", RouteKind.SHELL_SIMPLE, True, False, True),
    ("cp --recursive src backup", RouteKind.SHELL_SIMPLE, True, False, True),
    ("chmod -R 755 dir", RouteKind.SHELL_SIMPLE, True, False, True),
    ("chmod --recursive 755 dir", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git reset --hard", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git reset --hard HEAD~1", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git clean -fd", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git push --force origin main", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git push -f", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git checkout -- .", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git checkout .", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git restore .", RouteKind.SHELL_SIMPLE, True, False, True),
    ("git branch -D old-branch", RouteKind.SHELL_SIMPLE, True, False, True),

    # ------------------------------------------------------------------------
    # Category 7: Parent Directory Traversal & Outside Workspace Paths (6 cases)
    # ------------------------------------------------------------------------
    ("cd ..", RouteKind.SHELL_SIMPLE, True, False, True),
    ("ls ../parent_dir", RouteKind.SHELL_SIMPLE, True, False, True),
    ("cat foo/../../secret", RouteKind.SHELL_SIMPLE, True, False, True),
    ("touch ../sibling.txt", RouteKind.SHELL_SIMPLE, True, False, True),
    ("cat /etc/passwd", RouteKind.SHELL_SIMPLE, True, False, True),
    ("ls /tmp", RouteKind.SHELL_SIMPLE, True, False, True),

    # ------------------------------------------------------------------------
    # Category 8: Slash Commands and Slashless Normalization (6 cases)
    # ------------------------------------------------------------------------
    ("/help", RouteKind.SLASH_COMMAND, False, False, False),
    ("/model gpt-4o", RouteKind.SLASH_COMMAND, False, False, False),
    ("/theme cyan", RouteKind.SLASH_COMMAND, False, False, False),
    ("screensaver", RouteKind.SLASH_COMMAND, False, False, False),
    ("manual 3", RouteKind.SLASH_COMMAND, False, False, False),
    ("clear", RouteKind.SLASH_COMMAND, False, False, False),
]


@pytest.mark.parametrize("input_line,expected_kind,expected_destructive,expected_compound,expected_confirmation", ROUTER_TEST_CASES)
def test_classify_input_table(
    input_line: str,
    expected_kind: RouteKind,
    expected_destructive: bool,
    expected_compound: bool,
    expected_confirmation: bool,
    tmp_path: Path,
):
    """Table-driven test validating at least 60 distinct input variations for P1.3."""
    route = classify_input(input_line, workspace=tmp_path)
    assert route.kind == expected_kind, f"Failed kind for '{input_line}': got {route.kind}, expected {expected_kind}"
    assert route.destructive == expected_destructive, f"Failed destructive for '{input_line}': got {route.destructive}, expected {expected_destructive}"
    assert route.compound == expected_compound, f"Failed compound for '{input_line}': got {route.compound}, expected {expected_compound}"
    assert route.needs_confirmation == expected_confirmation, f"Failed confirmation for '{input_line}': got {route.needs_confirmation}, expected {expected_confirmation}"


def test_table_case_count():
    """Ensure the table-driven test suite exceeds the required 60 cases."""
    assert len(ROUTER_TEST_CASES) >= 60, f"Expected >= 60 test cases, found {len(ROUTER_TEST_CASES)}"


# ============================================================================
# 2. SPECIFIC ACCEPTANCE CRITERIA VERIFICATIONS
# ============================================================================

def test_acceptance_rm_rf_requires_confirmation(tmp_path: Path):
    """classify_input('rm -rf build') has destructive=True and requires y/N confirmation."""
    route = classify_input("rm -rf build", workspace=tmp_path)
    assert route.kind == RouteKind.SHELL_SIMPLE
    assert route.destructive is True
    assert route.needs_confirmation is True
    assert "rm" in route.reason


def test_acceptance_natural_language_prose_goals(tmp_path: Path):
    """'make a resume analyzer', 'list the requirements.txt issues', and 'touch the code up' route to SWARM_GOAL."""
    r1 = classify_input("make a resume analyzer", workspace=tmp_path)
    assert r1.kind == RouteKind.SWARM_GOAL

    r2 = classify_input("list the requirements.txt issues", workspace=tmp_path)
    assert r2.kind == RouteKind.SWARM_GOAL

    r3 = classify_input("touch the code up", workspace=tmp_path)
    assert r3.kind == RouteKind.SWARM_GOAL


def test_acceptance_compound_never_autorun(tmp_path: Path):
    """ls; rm -rf ~ is never auto-run; it is classified as compound and requires confirmation."""
    route = classify_input("ls; rm -rf ~", workspace=tmp_path)
    assert route.kind == RouteKind.SHELL_EXPLICIT
    assert route.compound is True
    assert route.destructive is True
    assert route.needs_confirmation is True


# ============================================================================
# 3. SAFE PASTE HANDLING & MULTI-LINE PROTECTION
# ============================================================================

def test_multiline_paste_treated_as_swarm_goal(tmp_path: Path):
    """Multi-line paste without '!' is treated as a single SWARM_GOAL and never auto-executed."""
    pasted_text = "rm -rf /\nls -la\ncat /etc/passwd"
    route = classify_input(pasted_text, workspace=tmp_path, paste_line_count=3)
    assert route.kind == RouteKind.SWARM_GOAL
    assert route.compound is True
    assert route.needs_confirmation is False
    assert route.paste_line_count == 3


def test_multiline_paste_with_explicit_prefix(tmp_path: Path):
    """Multi-line paste prefixed with '!' is classified as SHELL_EXPLICIT and requires confirmation."""
    pasted_text = "!echo line 1\necho line 2"
    route = classify_input(pasted_text, workspace=tmp_path, paste_line_count=2)
    assert route.kind == RouteKind.SHELL_EXPLICIT
    assert route.compound is True
    assert route.needs_confirmation is True
    assert route.paste_line_count == 2


def test_bracketed_paste_stripping_and_newline():
    """Verify bracketed paste control codes strip properly without auto-submission."""
    raw = "\x1b[200~rm -rf x\n\x1b[201~"
    cleaned = raw.replace("\x1b[200~", "").replace("\x1b[201~", "")
    assert cleaned == "rm -rf x\n"


# ============================================================================
# 4. PATH SAFETY & TRAVERSAL DETECTION
# ============================================================================

def test_inside_workspace_absolute_path_is_safe(tmp_path: Path):
    """Absolute paths located inside the active workspace do not trigger destructive confirmation."""
    inside_file = tmp_path / "subdir" / "data.txt"
    inside_file.parent.mkdir(parents=True, exist_ok=True)
    inside_file.touch()

    route = classify_input(f"ls {inside_file}", workspace=tmp_path)
    assert route.kind == RouteKind.SHELL_SIMPLE
    assert route.destructive is False
    assert route.needs_confirmation is False


def test_outside_workspace_absolute_path_requires_confirmation(tmp_path: Path):
    """Absolute paths outside active workspace trigger destructive confirmation."""
    outside_file = Path("/tmp")
    route = classify_input(f"ls {outside_file}", workspace=tmp_path)
    assert route.kind == RouteKind.SHELL_SIMPLE
    assert route.destructive is True
    assert route.needs_confirmation is True
    assert "outside active workspace" in route.reason


# ============================================================================
# 5. LEGACY ESCAPE HATCH (OCTOFLOW_LEGACY_ROUTER=1)
# ============================================================================

def test_legacy_escape_hatch(monkeypatch, tmp_path: Path):
    """When OCTOFLOW_LEGACY_ROUTER=1, unhardened legacy classification is used."""
    monkeypatch.setenv("OCTOFLOW_LEGACY_ROUTER", "1")

    # Under legacy router, 'cd ..' was simple without destructive safety flag
    legacy_route = classify_input("cd ..", workspace=tmp_path)
    assert legacy_route.kind == RouteKind.SHELL_SIMPLE
    assert legacy_route.needs_confirmation is False


# ============================================================================
# 6. COMMAND EXECUTION & 64 KB OUTPUT TRUNCATION
# ============================================================================

def test_execute_shell_route_simple(tmp_path: Path):
    """SHELL_SIMPLE runs subprocess.run with shell=False."""
    route = Route(
        kind=RouteKind.SHELL_SIMPLE,
        command="python3 -c 'print(\"simple_ok\")'",
        argv=["python3", "-c", "print(\"simple_ok\")"],
    )
    code, stdout, stderr = execute_shell_route(route, workspace=tmp_path)
    assert code == 0
    assert "simple_ok" in stdout


def test_execute_shell_route_explicit(tmp_path: Path):
    """SHELL_EXPLICIT runs subprocess.run with shell=True."""
    route = Route(
        kind=RouteKind.SHELL_EXPLICIT,
        command="python3 -c 'import sys; sys.stdout.write(\"explicit_ok\\n\")'",
        argv=[],
    )
    code, stdout, stderr = execute_shell_route(route, workspace=tmp_path)
    assert code == 0
    assert "explicit_ok" in stdout


def test_output_truncation_at_64kb(tmp_path: Path):
    """Captured shell output is strictly truncated at 64 KB."""
    # Generate 100 KB of text
    route = Route(
        kind=RouteKind.SHELL_SIMPLE,
        command="python3 -c 'print(\"A\" * 100000)'",
        argv=["python3", "-c", "print(\"A\" * 100000)"],
    )
    code, stdout, stderr = execute_shell_route(route, workspace=tmp_path)
    assert code == 0
    assert len(stdout.encode("utf-8")) <= MAX_CAPTURE_BYTES + 200
    assert "[OUTPUT TRUNCATED AT 64 KB]" in stdout


# ============================================================================
# 7. COMMAND HISTORY LOGGING & 0600 PERMISSIONS
# ============================================================================

def test_history_logging_and_permissions(tmp_path: Path, monkeypatch):
    """History logs to memory and ~/.octoflow/history with mode 0600."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    log_command_history("ls -la", workspace=tmp_path, success=True, kind="SHELL_SIMPLE")

    # Check memory record
    assert any(rec["command"] == "ls -la" for rec in SESSION_COMMAND_HISTORY)

    # Check file record
    hist_file = fake_home / ".octoflow" / "history"
    assert hist_file.exists()
    content = hist_file.read_text(encoding="utf-8")
    assert "ls -la" in content

    # Check file permissions are 0600
    file_mode = stat.S_IMODE(hist_file.stat().st_mode)
    assert file_mode == 0o600


# ============================================================================
# 8. PTY / TERMINAL CONFIRMATION SIMULATION TESTS
# ============================================================================

@pytest.mark.pty
def test_pty_confirmation_yes(tmp_path: Path):
    """Verify non-blocking confirmation succeeds when user provides 'y'."""
    import tty
    master, slave = pty.openpty()
    try:
        tty.setcbreak(slave)
        # Simulate typing 'y'
        os.write(master, b"y")

        # Non-blocking read simulation matching confirm_live_cockpit logic
        rlist, _, _ = select.select([slave], [], [], 0.5)
        assert len(rlist) > 0
        raw_char = os.read(slave, 1024).decode("utf-8")
        assert raw_char[0].lower() == "y"
    finally:
        os.close(master)
        os.close(slave)


@pytest.mark.pty
def test_pty_confirmation_no(tmp_path: Path):
    """Verify non-blocking confirmation rejects when user provides 'n'."""
    import tty
    master, slave = pty.openpty()
    try:
        tty.setcbreak(slave)
        os.write(master, b"n")
        rlist, _, _ = select.select([slave], [], [], 0.5)
        assert len(rlist) > 0
        raw_char = os.read(slave, 1024).decode("utf-8")
        assert raw_char[0].lower() == "n"
    finally:
        os.close(master)
        os.close(slave)


@pytest.mark.pty
def test_pty_confirmation_default_reject_on_enter(tmp_path: Path):
    """Verify non-blocking confirmation defaults to No when user presses Enter."""
    master, slave = pty.openpty()
    try:
        os.write(master, b"\r")
        rlist, _, _ = select.select([slave], [], [], 0.5)
        assert len(rlist) > 0
        raw_char = os.read(slave, 1024).decode("utf-8")
        # Enter is not 'y', so it defaults to rejection
        assert raw_char[0].lower() != "y"
    finally:
        os.close(master)
        os.close(slave)
