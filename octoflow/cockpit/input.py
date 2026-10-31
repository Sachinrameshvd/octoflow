"""Terminal Raw Mode Input, Keystroke Reading, and Bracketed Paste Handling.

Provides non-blocking 20 FPS keyboard polling, bracketed paste detection,
arrow-key navigation, and clean terminal state restoration on exit or signal.
"""

import atexit
import contextlib
import math
import os
import select
import signal
import sys
import termios
import tty
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live

from octoflow.cockpit.session import CockpitSession, Theme
from octoflow.runner import render_runner_frame
from octoflow.themes import get_banner_loop_frame

_saved_term_settings = None
_saved_term_fd: int | None = None


def restore_terminal_mode():
    """Restore terminal to its original state before cbreak mode was engaged."""
    global _saved_term_settings, _saved_term_fd
    if _saved_term_settings is not None and _saved_term_fd is not None:
        try:
            termios.tcsetattr(_saved_term_fd, termios.TCSADRAIN, _saved_term_settings)
        except Exception:
            pass
        _saved_term_settings = None
        _saved_term_fd = None


_prev_sigterm = None
_prev_sighup = None


def _sigterm_handler(signum, frame):
    """Ensure terminal settings are restored on SIGTERM/SIGHUP before exiting."""
    restore_terminal_mode()
    prev = _prev_sigterm if signum == signal.SIGTERM else _prev_sighup
    if callable(prev):
        prev(signum, frame)
    else:
        signal.signal(signum, signal.SIG_DFL)
        try:
            os.kill(os.getpid(), signum)
        except Exception:
            sys.exit(128 + signum)


atexit.register(restore_terminal_mode)
try:
    _prev_sigterm = signal.getsignal(signal.SIGTERM)
    _prev_sighup = signal.getsignal(signal.SIGHUP)
    signal.signal(signal.SIGTERM, _sigterm_handler)
    signal.signal(signal.SIGHUP, _sigterm_handler)
except (ValueError, AttributeError):
    pass


@contextlib.contextmanager
def raw_terminal_mode(fd: int):
    """Context manager setting cbreak raw mode with guaranteed restoration."""
    global _saved_term_settings, _saved_term_fd
    old_settings = None
    try:
        old_settings = termios.tcgetattr(fd)
        _saved_term_settings = old_settings
        _saved_term_fd = fd
        tty.setcbreak(fd)
    except Exception:
        pass

    try:
        yield old_settings
    finally:
        if old_settings is not None:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                pass
        _saved_term_settings = None
        _saved_term_fd = None


class CockpitInput(str):
    """Extends string with bracketed-paste metadata."""

    paste_line_count: int = 1
    is_pasted: bool = False


def clean_bracketed_paste(raw_chunk: str) -> tuple[str, bool, int]:
    """Parse bracketed paste control sequences and compute line metrics.

    Returns:
        (cleaned_text, is_pasted, line_count)
    """
    is_pasted = ("\x1b[200~" in raw_chunk) or (len(raw_chunk) > 3)
    clean_chunk = raw_chunk.replace("\x1b[200~", "").replace("\x1b[201~", "")
    p_lines = clean_chunk.splitlines()
    line_count = len(p_lines) if len(p_lines) > 1 else 1
    return clean_chunk, is_pasted, line_count


def get_live_cockpit_keys(
    session: CockpitSession | None = None,
    grid_builder: Callable[[str, int, int, float, int, int], Any] | None = None,
    console: Console | None = None,
    commands: list[str] | None = None,
) -> CockpitInput:
    """Non-blocking animated cockpit input loop.

    Polls keyboard events at 20 FPS (timeout <= 0.045s) while updating live animations.
    Never calls blocking input functions.
    """
    if session is None:
        session = CockpitSession()
    if console is None:
        console = Console()
    if grid_builder is None:
        from octoflow.cockpit.render import build_cockpit_grid

        _sess = session

        def grid_builder(b, c, t, ox, oy, plc):
            return build_cockpit_grid(_sess, b, c, t, ox, oy, plc)

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        try:
            raw_line = sys.stdin.readline()
            if not raw_line:
                return CockpitInput("/exit")
            cleaned = raw_line.strip()
            res = CockpitInput(cleaned)
            res.paste_line_count = len(raw_line.splitlines()) if "\n" in raw_line else 1
            res.is_pasted = res.paste_line_count > 1
            return res
        except (KeyboardInterrupt, EOFError):
            return CockpitInput("/exit")

    fd = sys.stdin.fileno()

    buffer = ""
    cursor_pos = 0
    tick = 0
    octo_x = 0.0
    octo_dx = 1.2
    octo_y = 0
    jump_phase = 0.0
    pasted_line_count = 1
    cmd_list = commands or []

    console.clear()

    with raw_terminal_mode(fd):
        with Live(
            grid_builder(buffer, cursor_pos, tick, octo_x, octo_y, pasted_line_count),
            console=console,
            refresh_per_second=20,
            transient=True,
        ) as live:
            while True:
                # Guaranteed select timeout <= 0.045s
                rlist, _, _ = select.select([sys.stdin], [], [], 0.045)
                if rlist:
                    try:
                        raw_chunk = os.read(fd, 8192).decode("utf-8", errors="ignore")
                    except Exception:
                        raw_chunk = sys.stdin.read(1)

                    if not raw_chunk:
                        continue

                    # Paste detection and processing
                    clean_chunk, is_pasted, l_count = clean_bracketed_paste(raw_chunk)

                    if is_pasted:
                        if l_count > 1:
                            pasted_line_count = max(pasted_line_count, l_count)
                        clean_paste = clean_chunk.replace("\r\n", "\n").replace("\r", "\n")
                        buffer = buffer[:cursor_pos] + clean_paste + buffer[cursor_pos:]
                        cursor_pos += len(clean_paste)
                        continue

                    # Enter / Carriage Return
                    if clean_chunk in ["\r", "\n", "\r\n"]:
                        break

                    # Ctrl+C
                    if "\x03" in clean_chunk:
                        raise KeyboardInterrupt()
                    # Ctrl+D
                    if "\x04" in clean_chunk:
                        raise EOFError()

                    idx = 0
                    while idx < len(clean_chunk):
                        ch = clean_chunk[idx]
                        if ch == "\x1b":
                            if (
                                idx + 2 < len(clean_chunk)
                                and clean_chunk[idx : idx + 3] == "\x1b[C"
                            ):
                                cursor_pos = min(cursor_pos + 1, len(buffer))
                                idx += 3
                                continue
                            elif (
                                idx + 2 < len(clean_chunk)
                                and clean_chunk[idx : idx + 3] == "\x1b[D"
                            ):
                                cursor_pos = max(cursor_pos - 1, 0)
                                idx += 3
                                continue
                            else:
                                end_m = idx + 1
                                while (
                                    end_m < len(clean_chunk)
                                    and clean_chunk[end_m] not in "ABCDEFHJKSTZ~"
                                ):
                                    end_m += 1
                                idx = end_m + 1
                                continue
                        elif ch in ["\x7f", "\x08"]:
                            if cursor_pos > 0:
                                buffer = buffer[: cursor_pos - 1] + buffer[cursor_pos:]
                                cursor_pos -= 1
                            idx += 1
                        elif ch == "\t":
                            matches = [c for c in cmd_list if c.startswith(buffer)]
                            if matches:
                                buffer = matches[0]
                                cursor_pos = len(buffer)
                            idx += 1
                        elif ch >= " ":
                            buffer = buffer[:cursor_pos] + ch + buffer[cursor_pos:]
                            cursor_pos += 1
                            idx += 1
                        else:
                            idx += 1

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

                live.update(
                    grid_builder(buffer, cursor_pos, tick, octo_x, octo_y, pasted_line_count)
                )

    res = CockpitInput(buffer.strip())
    res.paste_line_count = (
        pasted_line_count
        if pasted_line_count > 1
        else (len(buffer.splitlines()) if "\n" in buffer else 1)
    )
    res.is_pasted = pasted_line_count > 1 or "\n" in buffer
    return res


# Backward-compatible alias for live cockpit input
get_live_cockpit_input = get_live_cockpit_keys


def get_live_wizard_keys(
    theme: Theme,
    prompt_label: str = "Select option: ",
    default_value: str = "",
    extra_panels: list | None = None,
    is_password: bool = False,
    existing_cfg: dict | None = None,
    workspace: Path | None = None,
    console: Console | None = None,
) -> str:
    """Non-blocking animated input loop for setup wizard.

    Keeps the runner jumping and banner updating without blocking.
    """
    import subprocess

    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    c = console or Console()

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        try:
            line = sys.stdin.readline().strip()
            return line or default_value
        except (KeyboardInterrupt, EOFError):
            return default_value

    fd = sys.stdin.fileno()
    ws = workspace or Path.cwd().resolve()
    git_branch = "no git"
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            timeout=1,
        )
        if res.returncode == 0 and res.stdout.strip():
            git_branch = f"git: {res.stdout.strip()}"
    except Exception:
        pass

    cfg = existing_cfg or {}
    curr_mod = cfg.get("default_model", "INITIAL SETUP")
    curr_bud = float(cfg.get("default_budget", 10.00))

    hud_table = Table.grid(expand=True, padding=(0, 1))
    hud_table.add_column(style=theme.rich_primary, width=16)
    hud_table.add_column(style="white")
    hud_table.add_row("◈ WORKSPACE", f"{ws}  [dim]({git_branch})[/dim]")
    hud_table.add_row("◈ LLM CORE", f"{curr_mod.upper()}  [dim](Budget: ${curr_bud:.2f})[/dim]")
    hud_table.add_row("◈ SWARM TIER", "Octopuses: AUTO  [dim](Cross-Ring Synaptic Bus)[/dim]")
    hud_table.add_row(
        "◈ PALETTE",
        f"[{theme.rich_primary}]●[/{theme.rich_primary}] [{theme.rich_secondary}]●[/{theme.rich_secondary}] [{theme.rich_success}]●[/{theme.rich_success}] {theme.name} [dim]({theme.description})[/dim]",
    )
    hud_table.add_row(
        "◈ 3D VISUAL",
        f"[{theme.rich_primary} underline]http://localhost:8088[/{theme.rich_primary} underline]  [dim](Cmd+Click to view 3D Connectome)[/dim]",
    )

    cockpit_panel = Panel(
        hud_table,
        title=f"[{theme.rich_primary}]◈ OctoFlow Interactive Terminal Cockpit[/{theme.rich_primary}]",
        border_style=theme.rich_border,
        subtitle="[dim]Type your objective, or press '/' for commands. [Tab] autocompletes.[/dim]",
    )

    topology_text = Text.from_markup(
        f"\n  [dim]Ganglia Ring Topology:[/dim]  "
        f"[{theme.rich_primary}][0:Arch][/] ●  "
        f"[{theme.rich_primary}][1:API][/] ●  "
        f"[{theme.rich_primary}][2:DB][/] ●  "
        f"[{theme.rich_primary}][3:Logic][/] ●  "
        f"[{theme.rich_primary}][4:DevOps][/] ●  "
        f"[{theme.rich_primary}][5:UI][/] ●  "
        f"[{theme.rich_primary}][6:Test][/] ●  "
        f"[{theme.rich_primary}][7:Docs][/] ●\n"
    )

    def build_wizard_grid(buf: str, cur_pos: int, tick: int, ox: float, oy: int) -> Table:
        banner = get_banner_loop_frame(theme, tick=tick)
        runner = render_runner_frame(
            theme,
            octo_x=int(ox),
            octo_y=oy,
            is_jumping=(oy > 0),
            stride_alt=(int(ox // 3) % 2 == 1),
            seabed_offset=int(ox),
        )

        grid = Table.grid(expand=True)
        grid.add_row(banner)
        grid.add_row(cockpit_panel)
        grid.add_row(topology_text)
        grid.add_row(runner)
        if extra_panels:
            for ep in extra_panels:
                grid.add_row(ep)

        prompt_t = Text()
        prompt_t.append("\n")
        prompt_t.append(prompt_label, style=f"bold {theme.rich_primary}")
        disp_buf = ("*" * len(buf)) if is_password else buf
        prompt_t.append(disp_buf[:cur_pos], style="bold white")
        cur_char = "█" if (tick // 6) % 2 == 0 else " "
        prompt_t.append(cur_char, style=f"bold {theme.rich_primary}")
        prompt_t.append(disp_buf[cur_pos:], style="bold white")
        prompt_t.append("\n")

        grid.add_row(prompt_t)
        return grid

    buffer = default_value
    cursor_pos = len(buffer)
    tick = 0
    octo_x = 0.0
    octo_dx = 1.2
    octo_y = 0
    jump_phase = 0.0

    c.clear()

    with raw_terminal_mode(fd):
        with Live(
            build_wizard_grid(buffer, cursor_pos, tick, octo_x, octo_y),
            console=c,
            refresh_per_second=20,
            transient=True,
        ) as live:
            while True:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.045)
                if rlist:
                    try:
                        raw_chunk = os.read(fd, 8192).decode("utf-8", errors="ignore")
                    except Exception:
                        raw_chunk = sys.stdin.read(1)

                    if not raw_chunk:
                        continue

                    if "\x03" in raw_chunk:
                        raise KeyboardInterrupt()
                    if "\x04" in raw_chunk:
                        raise EOFError()

                    is_pasted = "\x1b[200~" in raw_chunk or len(raw_chunk) > 3
                    raw_chunk = raw_chunk.replace("\x1b[200~", "").replace("\x1b[201~", "")

                    if is_pasted:
                        clean_paste = "".join(ch for ch in raw_chunk if ch >= " ")
                        buffer = buffer[:cursor_pos] + clean_paste + buffer[cursor_pos:]
                        cursor_pos += len(clean_paste)
                        continue

                    if raw_chunk in ["\r", "\n", "\r\n"]:
                        break

                    idx = 0
                    while idx < len(raw_chunk):
                        ch = raw_chunk[idx]
                        if ch == "\x1b":
                            if idx + 2 < len(raw_chunk) and raw_chunk[idx : idx + 3] == "\x1b[C":
                                cursor_pos = min(cursor_pos + 1, len(buffer))
                                idx += 3
                                continue
                            elif idx + 2 < len(raw_chunk) and raw_chunk[idx : idx + 3] == "\x1b[D":
                                cursor_pos = max(cursor_pos - 1, 0)
                                idx += 3
                                continue
                            else:
                                end_m = idx + 1
                                while (
                                    end_m < len(raw_chunk)
                                    and raw_chunk[end_m] not in "ABCDEFHJKSTZ~"
                                ):
                                    end_m += 1
                                idx = end_m + 1
                                continue
                        elif ch in ["\x7f", "\x08"]:
                            if cursor_pos > 0:
                                buffer = buffer[: cursor_pos - 1] + buffer[cursor_pos:]
                                cursor_pos -= 1
                            idx += 1
                        elif ch >= " ":
                            buffer = buffer[:cursor_pos] + ch + buffer[cursor_pos:]
                            cursor_pos += 1
                            idx += 1
                        else:
                            idx += 1

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

                live.update(build_wizard_grid(buffer, cursor_pos, tick, octo_x, octo_y))

    return buffer.strip() or default_value


# Backward-compatible alias for live wizard input
get_live_wizard_input = get_live_wizard_keys
