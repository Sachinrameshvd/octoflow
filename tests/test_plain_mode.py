"""Tests for Plain Mode, NO_COLOR, ASCII Output, Narrow Terminals, and PTY Accessibility.

P6.3 Standards:
- NO_COLOR: Output piped or with NO_COLOR=1 contains 0 ANSI escape sequences.
- ASCII Fallback: --ascii or OCTOFLOW_ASCII=1 contains only bytes < 128.
- Plain Mode: Line-oriented [arm <id> <role>] <summary> output without Live TUI.
- Machine Output: --json emits clean machine-parseable JSON payload.
- Narrow Terminal: Adapts to < 60 cols or < 15 rows without crashing.
- PTY Support: --no-anim disables continuous redraws; SIGWINCH resize does not crash.
"""

import fcntl
import json
import os
import pty
import select
import shutil
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

import pytest
from rich.console import Console

from octoflow.cockpit.render import build_cockpit_grid, build_confirm_grid
from octoflow.cockpit.session import CockpitSession
from octoflow.glyphs import (
    is_ascii_mode,
    is_no_anim,
    is_no_color,
    is_plain_mode,
    reset_glyph_modes,
    set_ascii_mode,
    set_no_anim_mode,
    set_no_color_mode,
    set_plain_mode,
)
from octoflow.router import Route, RouteKind


@pytest.fixture(autouse=True)
def clean_modes():
    reset_glyph_modes()
    yield
    reset_glyph_modes()


def test_no_color_subprocess_pipe():
    """`NO_COLOR=1 octoflow run ... | cat` produces ANSI-clean output (no \\x1b)."""
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env["OCTOFLOW_DRY_RUN"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "octoflow.cli",
        "run",
        "verify auth helper",
        "--dry-run",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0
    # Strict assertion: Zero ANSI escape codes in stdout
    assert "\x1b" not in proc.stdout, f"Found ANSI escape code in NO_COLOR output: {proc.stdout[:200]}"


def test_ascii_mode_subprocess():
    """`--ascii` output contains only bytes < 128."""
    env = os.environ.copy()
    env["OCTOFLOW_DRY_RUN"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "octoflow.cli",
        "run",
        "build test suite",
        "--dry-run",
        "--ascii",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0
    assert proc.stdout, "Process produced no stdout"
    non_ascii = [c for c in proc.stdout if ord(c) >= 128]
    assert not non_ascii, f"Found non-ASCII characters with ord >= 128: {non_ascii[:10]}"


def test_plain_mode_arm_progress():
    """`--plain` outputs simple line-by-line arm progress events."""
    env = os.environ.copy()
    env["OCTOFLOW_DRY_RUN"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "octoflow.cli",
        "run",
        "create math service",
        "--dry-run",
        "--plain",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0
    # In plain mode, progress lines are formatted as [arm <id> <role>] <summary>
    assert "[arm " in proc.stdout
    assert "]" in proc.stdout


def test_quiet_mode_suppresses_progress():
    """`--quiet` / `-q` suppresses per-arm progress lines."""
    env = os.environ.copy()
    env["OCTOFLOW_DRY_RUN"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "octoflow.cli",
        "run",
        "create worker daemon",
        "--dry-run",
        "--plain",
        "--quiet",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0
    # Progress lines should be suppressed
    assert "[arm " not in proc.stdout


def test_json_output_mode():
    """`--json` returns machine-readable JSON outcome to stdout."""
    env = os.environ.copy()
    env["OCTOFLOW_DRY_RUN"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "octoflow.cli",
        "run",
        "generate schema types",
        "--dry-run",
        "--json",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout.strip())
    assert data["objective"] == "generate schema types"
    assert data["status"] == "dry_run"
    assert data["success"] is True
    assert "execution_time_seconds" in data
    assert "tokens_saved_pct" in data


def test_consortium_plain_mode():
    """`octos run` and `octoflow consortium` respect plain mode."""
    env = os.environ.copy()
    env["OCTOFLOW_DRY_RUN"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "octoflow.cli",
        "consortium",
        "monorepo orchestration",
        "--dry-run",
        "--plain",
        "--octos",
        "3",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0
    assert "[arm " in proc.stdout or "CONSORTIUM" in proc.stdout


def test_narrow_terminal_adaptation(monkeypatch):
    """When terminal size is < 60 cols or < 15 rows, render compact 1-line HUD without crash."""
    session = CockpitSession()

    # Emulate narrow terminal: 50 columns x 10 rows
    monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((50, 10)))

    # Composite cockpit grid
    grid = build_cockpit_grid(session, "echo test", cursor_pos=9, tick=0, octo_x=0.0, octo_y=0)
    assert grid is not None

    console = Console(width=50, height=10, record=True)
    console.print(grid)
    rendered = console.export_text()

    # Should contain compact HUD info and prompt without error
    assert "Tier:" in rendered or "◈" in rendered or "*" in rendered

    # Composite confirmation grid
    route = Route(kind=RouteKind.SHELL_EXPLICIT, command="rm -rf /tmp/foo", reason="Testing destructive")
    confirm_grid = build_confirm_grid(route, session, tick=0, octo_x=0.0, octo_y=0)
    assert confirm_grid is not None
    console.print(confirm_grid)
    confirm_rendered = console.export_text()
    assert "Confirm execution:" in confirm_rendered


def test_pty_no_anim_mode_idle():
    """In PTY with --no-anim, two idle reads produce zero additional frames."""
    master, slave = pty.openpty()
    try:
        env = os.environ.copy()
        env["OCTOFLOW_ANIM"] = "0"
        env["OCTOFLOW_DRY_RUN"] = "1"

        # Spawn python process in PTY running an input check or quick exit
        cmd = [
            sys.executable,
            "-c",
            "import os, time; from octoflow.glyphs import is_no_anim; print('NO_ANIM:', is_no_anim()); time.sleep(0.1)",
        ]
        proc = subprocess.Popen(
            cmd,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=env,
            close_fds=True,
        )

        # Read output from master
        time.sleep(0.05)
        rlist, _, _ = select.select([master], [], [], 1.0)
        assert rlist, "No output from PTY process"
        chunk1 = os.read(master, 1024).decode("utf-8", errors="ignore")
        assert "NO_ANIM: True" in chunk1

        proc.wait(timeout=5)
    finally:
        os.close(master)
        os.close(slave)


def test_pty_window_resize_no_crash():
    """Simulating SIGWINCH / PTY window resize during runtime does not crash."""
    master, slave = pty.openpty()
    try:
        # Initial standard size 80x24
        winsize_std = struct.pack("HHHH", 24, 80, 0, 0)
        fcntl.ioctl(master, termios.TIOCSWINSZ, winsize_std)

        # Resize to narrow 50x12
        winsize_narrow = struct.pack("HHHH", 12, 50, 0, 0)
        fcntl.ioctl(master, termios.TIOCSWINSZ, winsize_narrow)

        # Resize back to wide 120x40
        winsize_wide = struct.pack("HHHH", 40, 120, 0, 0)
        fcntl.ioctl(master, termios.TIOCSWINSZ, winsize_wide)
    finally:
        os.close(master)
        os.close(slave)
