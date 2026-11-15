"""Cockpit HUD, Banner, and Terminal Frame Composition.

Renders rich terminal UI components for the interactive cockpit:
- HUD panel displaying workspace, git branch, core model, budget, palette, and 3D link
- Ganglia ring topology indicator
- Interactive animated prompt with cursor and bracketed paste indicator
- Unified composite grid tables for input and confirmation frames
- Welcome 3D banner rendering
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from octoflow.cockpit.session import CockpitSession, Theme
from octoflow.glyphs import glyph
from octoflow.runner import render_runner_frame
from octoflow.themes import (
    get_banner_loop_frame,
    play_banner_animation,
    render_octoflow_3d_banner,
)


def _get_git_branch_fast(workspace: Any) -> str:
    """Read git branch directly from filesystem metadata or fast fallback."""
    try:
        from pathlib import Path

        ws = Path(workspace)
        git_dir = ws / ".git"
        if git_dir.is_dir():
            head_file = git_dir / "HEAD"
            if head_file.is_file():
                content = head_file.read_text(encoding="utf-8").strip()
                if content.startswith("ref: refs/heads/"):
                    return f"git: {content[16:]}"
                if content:
                    return f"git: {content[:7]}"
        elif git_dir.is_file():
            head_ref = git_dir.read_text(encoding="utf-8").strip()
            if head_ref.startswith("gitdir:"):
                actual_git = ws / head_ref[7:].strip()
                if actual_git.is_dir():
                    head_file = actual_git / "HEAD"
                    if head_file.is_file():
                        content = head_file.read_text(encoding="utf-8").strip()
                        if content.startswith("ref: refs/heads/"):
                            return f"git: {content[16:]}"
        # Fallback to subprocess if not directly resolved
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            timeout=1,
        )
        if res.returncode == 0 and res.stdout.strip():
            return f"git: {res.stdout.strip()}"
    except Exception:
        pass
    return "no git"


def build_hud_panel(session: CockpitSession) -> Panel:
    """Build the top HUD panel displaying workspace state, git branch, model, and budget."""
    theme = session.theme
    cached_branch = getattr(session, "_cached_git_branch", None)
    cached_ws = getattr(session, "_cached_git_ws", None)
    if cached_branch is not None and cached_ws == session.workspace:
        git_branch = cached_branch
    else:
        git_branch = _get_git_branch_fast(session.workspace)
        session._cached_git_branch = git_branch  # type: ignore[attr-defined]
        session._cached_git_ws = session.workspace  # type: ignore[attr-defined]

    hud_table = Table.grid(expand=True, padding=(0, 1))
    hud_table.add_column(style=theme.rich_primary, width=16)
    hud_table.add_column(style="white")
    hud_table.add_row("◈ WORKSPACE", f"{session.workspace}  [dim]({git_branch})[/dim]")
    hud_table.add_row(
        "◈ LLM CORE",
        f"{session.current_model.upper()}  [dim](Budget: ${session.current_budget:.2f})[/dim]",
    )
    budget_line = getattr(session, "budget_line", None)
    if not budget_line and getattr(session, "budget_tracker", None):
        budget_line = session.budget_tracker.format_hud_line()
    if not budget_line:
        budget_tracker = getattr(session, "_cached_budget_tracker", None)
        if budget_tracker is None:
            from octoflow.budget import BudgetTracker, RunBudget

            budget = getattr(session, "budget", None) or RunBudget()
            budget_tracker = BudgetTracker(budget=budget)
            session._cached_budget_tracker = budget_tracker  # type: ignore[attr-defined]
        budget_line = budget_tracker.format_hud_line()
    hud_table.add_row("◈ BUDGET", f"{budget_line}")
    tier_desc = f"Octopuses: {session.current_octos.upper()}  [dim](Cross-Ring Synaptic Bus)[/dim]"
    if getattr(session, "current_octos", "auto") == "auto":
        try:
            from octoflow.interview import detect_project_consortium

            bp = detect_project_consortium(str(session.workspace))
            tier_desc = f"{bp.scale_tier}  [dim]({bp.project_type})[/dim]"
        except Exception:
            pass
    hud_table.add_row("◈ SWARM TIER", tier_desc)
    hud_table.add_row(
        "◈ SENSORY GATE",
        f"[{theme.rich_success}]●[/{theme.rich_success}] Active Inference (θ = 0.45)  [dim](Reflexes & Avoided Tokens Enabled)[/dim]",
    )
    hud_table.add_row(
        "◈ PALETTE",
        f"[{theme.rich_primary}]●[/{theme.rich_primary}] [{theme.rich_secondary}]●[/{theme.rich_secondary}] [{theme.rich_success}]●[/{theme.rich_success}] {theme.name} [dim]({theme.description})[/dim]",
    )
    hud_table.add_row(
        "◈ 3D VISUAL",
        f"[{theme.rich_primary} underline]{session.visualizer_url}[/{theme.rich_primary} underline]  [dim](Cmd+Click to view 3D Connectome)[/dim]",
    )

    return Panel(
        hud_table,
        title=f"[{theme.rich_primary}]◈ OctoFlow Interactive Terminal Cockpit[/{theme.rich_primary}]",
        border_style=theme.rich_border,
        subtitle="[dim]Type your objective, or press '/' for commands. [Tab] autocompletes.[/dim]",
    )


def build_topology_text(theme: Theme) -> Text:
    """Render the horizontal 8-ganglia ring topology indicator."""
    return Text.from_markup(
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


def build_prompt_text(
    theme: Theme,
    buffer: str,
    cursor_pos: int,
    tick: int,
    pasted_line_count: int = 1,
) -> Text:
    """Render interactive prompt text with blinking block cursor and paste badge."""
    prompt_text = Text()
    prompt_text.append("\n")
    effective_lines = (
        pasted_line_count
        if pasted_line_count > 1
        else (len(buffer.splitlines()) if "\n" in buffer else 1)
    )
    if effective_lines > 1:
        prompt_text.append(f"[{effective_lines} lines pasted] ", style="italic cyan")
    prompt_text.append("octos ❯ ", style=theme.rich_primary)
    display_buf = buffer.replace("\r\n", " ↵ ").replace("\n", " ↵ ")
    prompt_text.append(display_buf[:cursor_pos], style="bold white")
    cursor_char = "█" if (tick // 6) % 2 == 0 else " "
    prompt_text.append(cursor_char, style=f"bold {theme.rich_primary}")
    prompt_text.append(display_buf[cursor_pos:], style="bold white")
    prompt_text.append("\n")
    return prompt_text


def build_compact_hud_line(session: CockpitSession) -> Panel:
    """Render a compact 1-line HUD for narrow terminals (< 60 cols or < 15 rows)."""
    theme = session.theme
    ws_name = Path(session.workspace).name or str(session.workspace)
    mod = session.current_model.upper()
    octos = session.current_octos.upper()
    diamond = glyph("DIAMOND")
    return Panel(
        Text.from_markup(
            f"{diamond} [{theme.rich_primary}]{ws_name}[/{theme.rich_primary}]  |  "
            f"[{theme.rich_secondary}]{mod}[/{theme.rich_secondary}]  |  "
            f"Tier: {octos}"
        ),
        border_style=theme.rich_border,
        padding=(0, 1),
    )


def build_cockpit_grid(
    session: CockpitSession,
    buffer: str,
    cursor_pos: int,
    tick: int,
    octo_x: float,
    octo_y: int,
    pasted_line_count: int = 1,
) -> Table:
    """Composite the full animated cockpit frame grid (Banner, HUD, Topology, Runner, Prompt)."""
    t0 = time.perf_counter() if os.getenv("OCTOFLOW_DEBUG_FRAMES") == "1" else 0.0

    theme = session.theme
    prompt_text = build_prompt_text(theme, buffer, cursor_pos, tick, pasted_line_count)

    # Narrow terminal handling: below 60 cols or 15 rows, skip banner & runner, show 1-line HUD
    cols, lines = shutil.get_terminal_size((80, 24))
    if cols < 60 or lines < 15:
        grid = Table.grid(expand=True)
        grid.add_row(build_compact_hud_line(session))
        grid.add_row(prompt_text)
        return grid

    banner = get_banner_loop_frame(theme, tick=tick)
    is_jump = octo_y > 0
    runner_frame = render_runner_frame(
        theme,
        octo_x=int(octo_x),
        octo_y=octo_y,
        is_jumping=is_jump,
        stride_alt=(int(octo_x // 3) % 2 == 1),
        seabed_offset=int(octo_x),
    )
    hud_panel = build_hud_panel(session)
    topology_text = build_topology_text(theme)

    grid = Table.grid(expand=True)
    grid.add_row(banner)
    grid.add_row(hud_panel)
    grid.add_row(topology_text)
    grid.add_row(runner_frame)
    grid.add_row(prompt_text)

    if t0 > 0.0:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        session.last_frame_ms = elapsed_ms  # type: ignore[attr-defined]

    return grid


def build_confirm_grid(
    route: Any,
    session: CockpitSession,
    tick: int,
    octo_x: float,
    octo_y: int,
) -> Table:
    """Composite confirmation prompt frame grid while preserving runner animation."""
    theme = session.theme
    warn_sym = glyph("WARN")

    prompt_text = Text()
    prompt_text.append("\n")
    prompt_text.append(f"{warn_sym} Confirm execution: ", style=f"bold {theme.rich_warning}")
    cmd_str = getattr(route, "command", str(route))
    prompt_text.append(f"{cmd_str}", style="bold white")
    reason = getattr(route, "reason", None)
    if reason:
        prompt_text.append(f"  [dim]({reason})[/dim]")
    prompt_text.append(" [y/N]: ", style=f"bold {theme.rich_primary}")
    prompt_text.append("\n")

    cols, lines = shutil.get_terminal_size((80, 24))
    if cols < 60 or lines < 15:
        grid = Table.grid(expand=True)
        grid.add_row(build_compact_hud_line(session))
        grid.add_row(prompt_text)
        return grid

    banner = get_banner_loop_frame(theme, tick=tick)
    is_jump = octo_y > 0
    runner_frame = render_runner_frame(
        theme,
        octo_x=int(octo_x),
        octo_y=octo_y,
        is_jumping=is_jump,
        stride_alt=(int(octo_x // 3) % 2 == 1),
        seabed_offset=int(octo_x),
    )
    hud_panel = build_hud_panel(session)
    topology_text = build_topology_text(theme)

    grid = Table.grid(expand=True)
    grid.add_row(banner)
    grid.add_row(hud_panel)
    grid.add_row(topology_text)
    grid.add_row(runner_frame)
    grid.add_row(prompt_text)
    return grid


def print_welcome_banner(
    session: CockpitSession,
    console: Console,
    animate: bool = False,
    continuous: bool = False,
    **kwargs: Any,
) -> None:
    """Clear console and print the static or animated 3D ASCII logo banner."""
    console.clear()
    if animate:
        try:
            play_banner_animation(console, session.theme)
        except Exception:
            banner_text = render_octoflow_3d_banner(session.theme)
            console.print(banner_text)
    else:
        banner_text = render_octoflow_3d_banner(session.theme)
        console.print(banner_text)


# Backward-compatible alias
print_welcome = print_welcome_banner


def build_style_a_progress_panel(
    objective: str,
    octopus_states: dict[Any, Any],
    total_tokens_saved: float = 87.5,
    total_cost: float = 0.0,
    last_event_msg: str = "",
    visualizer_url: str = "http://localhost:8088",
    elapsed_seconds: float = 0.0,
    total_arms: int = 24,
    tier_name: str = "TRIAD",
    theme: Any | None = None,
    tick: int | None = None,
    tokens_spent: int = 0,
    tokens_avoided: int = 0,
    blueprint: Any | None = None,
) -> Panel:
    """Build Style A Multi-Octopus Progress Panel with progress bars, animated activity spinners, and state labels."""
    from octoflow.commands.dashboard import build_style_a_progress_panel as _render_panel

    return _render_panel(
        objective=objective,
        octopus_states=octopus_states,
        total_tokens_saved=total_tokens_saved,
        total_cost=total_cost,
        last_event_msg=last_event_msg,
        visualizer_url=visualizer_url,
        elapsed_seconds=elapsed_seconds,
        total_arms=total_arms,
        tier_name=tier_name,
        theme=theme,
        tick=tick,
        tokens_spent=tokens_spent,
        tokens_avoided=tokens_avoided,
        blueprint=blueprint,
    )

