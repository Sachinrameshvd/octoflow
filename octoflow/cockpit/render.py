"""Cockpit HUD, Banner, and Terminal Frame Composition.

Renders rich terminal UI components for the interactive cockpit:
- HUD panel displaying workspace, git branch, core model, budget, palette, and 3D link
- Ganglia ring topology indicator
- Interactive animated prompt with cursor and bracketed paste indicator
- Unified composite grid tables for input and confirmation frames
- Welcome 3D banner rendering
"""

import subprocess
from typing import Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from octoflow.themes import (
    OctoTheme,
    get_banner_loop_frame,
    render_octoflow_3d_banner,
    play_banner_animation,
)
from octoflow.runner import render_runner_frame
from octoflow.cockpit.session import CockpitSession, Theme


def build_hud_panel(session: CockpitSession) -> Panel:
    """Build the top HUD panel displaying workspace state, git branch, model, and budget."""
    theme = session.theme
    git_branch = "no git"
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(session.workspace),
            capture_output=True,
            text=True,
            timeout=1,
        )
        if res.returncode == 0 and res.stdout.strip():
            git_branch = f"git: {res.stdout.strip()}"
    except Exception:
        pass

    hud_table = Table.grid(expand=True, padding=(0, 1))
    hud_table.add_column(style=theme.rich_primary, width=16)
    hud_table.add_column(style="white")
    hud_table.add_row("◈ WORKSPACE", f"{session.workspace}  [dim]({git_branch})[/dim]")
    hud_table.add_row("◈ LLM CORE", f"{session.current_model.upper()}  [dim](Budget: ${session.current_budget:.2f})[/dim]")
    budget_line = getattr(session, "budget_line", None)
    if not budget_line and getattr(session, "budget_tracker", None):
        budget_line = session.budget_tracker.format_hud_line()
    if not budget_line:
        from octoflow.budget import RunBudget, BudgetTracker
        budget = getattr(session, "budget", None) or RunBudget()
        tracker = BudgetTracker(budget=budget)
        budget_line = tracker.format_hud_line()
    hud_table.add_row("◈ BUDGET", f"{budget_line}")
    hud_table.add_row("◈ SWARM TIER", f"Octopuses: {session.current_octos.upper()}  [dim](Cross-Ring Synaptic Bus)[/dim]")
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
    theme = session.theme
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
    prompt_text = build_prompt_text(theme, buffer, cursor_pos, tick, pasted_line_count)

    grid = Table.grid(expand=True)
    grid.add_row(banner)
    grid.add_row(hud_panel)
    grid.add_row(topology_text)
    grid.add_row(runner_frame)
    grid.add_row(prompt_text)
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

    prompt_text = Text()
    prompt_text.append("\n")
    prompt_text.append("⚠ Confirm execution: ", style=f"bold {theme.rich_warning}")
    cmd_str = getattr(route, "command", str(route))
    prompt_text.append(f"{cmd_str}", style="bold white")
    reason = getattr(route, "reason", None)
    if reason:
        prompt_text.append(f"  [dim]({reason})[/dim]")
    prompt_text.append(" [y/N]: ", style=f"bold {theme.rich_primary}")
    prompt_text.append("\n")

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
