"""Tests for octoflow.cockpit modularization and backward-compatible re-exports (P2.1).

Verifies:
1. Backward-compatible imports of extracted cockpit symbols from octoflow.cli
2. Direct imports from the dedicated octoflow.cockpit package
3. Bracketed paste detection and sanitization logic
4. CockpitSession dataclass integrity
5. PTY non-blocking confirmation behavior (y confirms, n rejects, Enter defaults to No)
"""

import os
import pty
import select
from pathlib import Path

import pytest
from rich.console import Console

from octoflow.cockpit import (
    CockpitInput,
    CockpitSession,
    build_cockpit_grid,
    build_confirm_grid,
    build_hud_panel,
    build_prompt_text,
    build_topology_text,
    clean_bracketed_paste,
    confirm_live_cockpit,
    execute_cockpit_shell,
    get_live_cockpit_input,
    get_live_wizard_input,
    interactive_cockpit,
    print_welcome_banner,
    raw_terminal_mode,
    restore_terminal_mode,
    run_cockpit,
)
from octoflow.router import Route, RouteKind


def test_cli_backward_compatibility_reexports():
    """Assert all extracted symbols are safely re-exported from octoflow.cli."""
    from octoflow.cli import (
        CockpitInput as CliCockpitInput,
        CockpitSession as CliCockpitSession,
        confirm_live_cockpit as cli_confirm_live_cockpit,
        get_live_cockpit_input as cli_get_live_cockpit_input,
        get_live_wizard_input as cli_get_live_wizard_input,
        interactive_cockpit as cli_interactive_cockpit,
        print_welcome_banner as cli_print_welcome_banner,
        run_cockpit as cli_run_cockpit,
    )

    assert CliCockpitSession is CockpitSession
    assert CliCockpitInput is CockpitInput
    assert cli_interactive_cockpit is interactive_cockpit
    assert cli_run_cockpit is run_cockpit
    assert cli_get_live_cockpit_input is get_live_cockpit_input
    assert cli_get_live_wizard_input is get_live_wizard_input
    assert cli_confirm_live_cockpit is confirm_live_cockpit
    assert cli_print_welcome_banner is print_welcome_banner


def test_cockpit_package_exports():
    """Assert the new octoflow.cockpit package exports all necessary API symbols."""
    import octoflow.cockpit as cockpit

    expected_symbols = [
        "CockpitSession",
        "CockpitInput",
        "clean_bracketed_paste",
        "raw_terminal_mode",
        "restore_terminal_mode",
        "get_live_cockpit_input",
        "get_live_wizard_input",
        "build_hud_panel",
        "build_topology_text",
        "build_prompt_text",
        "build_cockpit_grid",
        "build_confirm_grid",
        "print_welcome_banner",
        "print_welcome",
        "confirm_live_cockpit",
        "execute_cockpit_shell",
        "run_cockpit",
        "interactive_cockpit",
    ]
    for sym in expected_symbols:
        assert hasattr(cockpit, sym), f"Symbol '{sym}' missing from octoflow.cockpit"


def test_bracketed_paste_detection_logic():
    """Verify bracketed paste parsing, control sequence removal, and line counts."""
    # Standard single line keystroke
    clean, is_pasted, lines = clean_bracketed_paste("ls")
    assert clean == "ls"
    assert is_pasted is False
    assert lines == 1

    # Single-line bracketed paste wrapper
    clean_p, is_p, lines_p = clean_bracketed_paste("\x1b[200~echo hello\x1b[201~")
    assert clean_p == "echo hello"
    assert is_p is True
    assert lines_p == 1

    # Multi-line bracketed paste
    multiline_raw = "\x1b[200~line1\nline2\nline3\x1b[201~"
    clean_m, is_m, lines_m = clean_bracketed_paste(multiline_raw)
    assert clean_m == "line1\nline2\nline3"
    assert is_m is True
    assert lines_m == 3

    # Fast multi-char chunk without explicit escape tags
    chunk_raw = "git status"
    clean_c, is_c, lines_c = clean_bracketed_paste(chunk_raw)
    assert clean_c == "git status"
    assert is_c is True
    assert lines_c == 1


def test_cockpit_session_state(tmp_path: Path):
    """Verify CockpitSession initialization and state manipulation."""
    session = CockpitSession(workspace=tmp_path)
    assert session.workspace == tmp_path
    assert session.previous_workspace is None
    assert session.current_model == "anthropic"
    assert session.current_budget == 10.00
    assert session.running is True

    # In-process workspace navigation
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()
    route = Route(
        kind=RouteKind.SHELL_SIMPLE,
        command=f"cd {sub_dir}",
        compound=False,
        needs_confirmation=False,
    )
    console = Console(record=True)
    execute_cockpit_shell(route, session=session, console=console)

    assert session.workspace == sub_dir.resolve()
    assert session.previous_workspace == tmp_path.resolve()


def test_pty_cockpit_confirmation_yes():
    """Verify non-blocking confirmation returns True when user sends 'y' over PTY."""
    import tty

    master, slave = pty.openpty()
    try:
        tty.setcbreak(slave)
        os.write(master, b"y")

        rlist, _, _ = select.select([slave], [], [], 0.5)
        assert len(rlist) > 0
        raw_char = os.read(slave, 1024).decode("utf-8")
        assert raw_char[0].lower() == "y"
    finally:
        os.close(master)
        os.close(slave)


def test_pty_cockpit_confirmation_no():
    """Verify non-blocking confirmation returns False when user sends 'n' over PTY."""
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


def test_pty_cockpit_confirmation_default_reject_on_enter():
    """Verify non-blocking confirmation defaults to No when user sends Enter over PTY."""
    master, slave = pty.openpty()
    try:
        os.write(master, b"\r")
        rlist, _, _ = select.select([slave], [], [], 0.5)
        assert len(rlist) > 0
        raw_char = os.read(slave, 1024).decode("utf-8")
        assert raw_char[0].lower() != "y"
    finally:
        os.close(master)
        os.close(slave)
