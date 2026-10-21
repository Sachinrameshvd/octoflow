"""Cockpit Shell Command Execution and Confirmation Handling.

Integrates with octoflow.router to:
- Prompt user for confirmation on destructive or explicit commands using non-blocking 20 FPS UI
- Execute direct shell commands with timeout, 64 KB capture truncation, and secure history logging
- Handle in-process workspace navigation ('cd') without altering global process cwd
"""

import math
import os
import select
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.live import Live

from octoflow.router import (
    Route,
    RouteKind,
    execute_shell_route,
    log_command_history,
)
from octoflow.cockpit.session import CockpitSession
from octoflow.cockpit.input import raw_terminal_mode
from octoflow.cockpit.render import build_confirm_grid


def confirm_live_cockpit(
    route: Route,
    session: Optional[CockpitSession] = None,
    console: Optional[Console] = None,
) -> bool:
    """Non-blocking cockpit confirmation prompt maintaining the 20 FPS runner animation.

    Prompts user with 'y/N', defaulting to No on Enter or any non-'y' key.
    Non-blocking 20 FPS keyboard polling.
    """
    c = console or Console()
    s = session or CockpitSession()
    theme = s.theme

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        try:
            c.print(
                f"[{theme.rich_warning}]⚠ Confirm execution:[/{theme.rich_warning}] "
                f"[bold]{route.command}[/bold] ({route.reason}) [y/N]: ",
                end="",
            )
            raw_ans = sys.stdin.readline()
            ans = raw_ans.strip().lower() if raw_ans else ""
            return ans in ["y", "yes"]
        except Exception:
            return False

    fd = sys.stdin.fileno()

    tick = 0
    octo_x = 0.0
    octo_dx = 1.2
    octo_y = 0
    jump_phase = 0.0

    with raw_terminal_mode(fd):
        with Live(
            build_confirm_grid(route, s, tick, octo_x, octo_y),
            console=c,
            refresh_per_second=20,
            transient=True,
        ) as live:
            while True:
                # Guaranteed select timeout <= 0.045s
                rlist, _, _ = select.select([sys.stdin], [], [], 0.045)
                if rlist:
                    try:
                        raw_chunk = os.read(fd, 1024).decode("utf-8", errors="ignore")
                    except Exception:
                        raw_chunk = sys.stdin.read(1)

                    if not raw_chunk:
                        continue

                    if "\x03" in raw_chunk:
                        return False

                    first_char = raw_chunk[0].lower()
                    # Strict confirmation: only 'y' confirms, everything else (n, Enter, Esc, etc.) defaults to No
                    if first_char == "y":
                        return True
                    return False

                tick += 1
                octo_x += octo_dx
                if octo_x >= 45.0:
                    octo_x = 45.0
                    octo_dx = -1.2
                elif octo_x <= 0.0:
                    octo_x = 0.0
                    octo_dx = 1.2

                jump_phase += 0.16
                octo_y = 1 if math.sin(jump_phase) > 0.25 else 0

                live.update(build_confirm_grid(route, s, tick, octo_x, octo_y))


def execute_cockpit_shell(
    route: Route,
    session: CockpitSession,
    console: Console,
) -> None:
    """Execute direct shell commands or in-process cd navigation."""
    shell_cmd = route.command
    theme = session.theme
    parts = shell_cmd.split(maxsplit=1)
    cmd_head = parts[0].lower() if parts else ""

    # In-process workspace navigation (cd) without global os.chdir()
    if cmd_head == "cd":
        target_arg = parts[1].strip() if len(parts) > 1 else "~"
        if target_arg == "-":
            target_path = session.previous_workspace or session.workspace
        else:
            target_path = Path(os.path.expanduser(target_arg)).resolve()

        if not target_path.exists():
            console.print(f"[{theme.rich_danger}]cd: no such file or directory: {target_arg}[/{theme.rich_danger}]\n")
            log_command_history(shell_cmd, workspace=session.workspace, success=False, kind="CD")
            return
        if not target_path.is_dir():
            console.print(f"[{theme.rich_danger}]cd: not a directory: {target_arg}[/{theme.rich_danger}]\n")
            log_command_history(shell_cmd, workspace=session.workspace, success=False, kind="CD")
            return

        session.previous_workspace = session.workspace
        session.workspace = target_path
        log_command_history(shell_cmd, workspace=session.workspace, success=True, kind="CD")
        console.print(f"[{theme.rich_success}]✔ Active workspace switched to:[/{theme.rich_success}] [bold]{session.workspace}[/bold]\n")
        return

    console.print(f"[{theme.rich_primary}]⚡ Shell:[/{theme.rich_primary}] [dim]{shell_cmd}[/dim]")
    try:
        returncode, stdout, stderr = execute_shell_route(route, workspace=session.workspace, timeout=60)
        if stdout:
            console.print(stdout.rstrip())
        if stderr:
            console.print(f"[{theme.rich_danger}]{stderr.rstrip()}[/{theme.rich_danger}]")
        if returncode == 0 and not stdout:
            console.print(f"[{theme.rich_success}]✔ Command executed successfully.[/{theme.rich_success}]")
    except subprocess.TimeoutExpired:
        console.print(f"[{theme.rich_danger}]✖ Command timed out after 60 seconds.[/{theme.rich_danger}]")
        log_command_history(shell_cmd, workspace=session.workspace, success=False, kind=route.kind.value)
    except Exception as ex:
        console.print(f"[{theme.rich_danger}]✖ Command execution error: {ex}[/{theme.rich_danger}]")
        log_command_history(shell_cmd, workspace=session.workspace, success=False, kind=route.kind.value)

    console.print()
