"""OctoFlow Terminal Dashboard Rendering Functions.

Renders real-time reactive dashboards with live surprise gauges, active
coalition links, and token savings metrics for single-octopus and multi-octopus swarms.
"""

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from octoflow.config import get_octoflow_dir, load_secure_config
from octoflow.glyphs import glyph
from octoflow.themes import OctoTheme, load_saved_theme


def render_consortium_dashboard(
    objective: str,
    octopus_states: dict,
    total_tokens_saved: float,
    total_cost: float,
    last_event_msg: str,
    visualizer_url: str = "http://localhost:8088",
    elapsed_seconds: float = 0.0,
    total_arms: int = 24,
    tier_name: str = "TRIAD",
    theme: OctoTheme | None = None,
) -> Panel:
    """Render the multi-octopus consortium dashboard using Rich."""
    if theme is None:
        theme = load_saved_theme()

    metrics_table = Table.grid(expand=True)
    metrics_table.add_column(justify="left")
    metrics_table.add_column(justify="right")

    status_text = Text()
    status_text.append(" ◈ OCTOSFLOW v1.0.0", style=theme.rich_primary)
    status_text.append(f" | Tier: {tier_name}", style=theme.rich_secondary)
    status_text.append(
        f" | Swarm: {len(octopus_states)} Octopuses ({total_arms} Arms)", style=theme.rich_success
    )

    badge_text = Text()
    badge_text.append(f"Cost: ${total_cost:.3f} ", style="bold white")
    badge_text.append("| Synaptic Links: Active", style=theme.rich_primary)

    metrics_table.add_row(status_text, badge_text)

    mins, secs = divmod(int(elapsed_seconds), 60)
    elapsed_str = f"{mins:02d}:{secs:02d}"

    info_banner = Panel(
        Text(f" ● Elapsed: {elapsed_str}  |  ◈ Objective: {objective[:70]}...", style="bold white"),
        border_style="dim",
    )

    visualizer_banner = Panel(
        Text(
            f" ● Live 3D Constellation Visualizer: {visualizer_url}  (Cmd+Click link to watch all {len(octopus_states)} octopuses fire live)",
            style=theme.rich_primary,
        ),
        border_style=theme.rich_border,
    )

    grid = Table(expand=True, border_style=theme.rich_border)
    grid.add_column("Octopus", justify="center", style=theme.rich_primary, width=10)
    grid.add_column("Department Guild", justify="left", style="white", width=22)
    grid.add_column("Swarm Progress", justify="center", width=18)
    grid.add_column("8-Arm Neural Matrix", justify="center", width=34)
    grid.add_column("Current Deliverable Execution", justify="left", style="white")

    for oct_id, data in sorted(octopus_states.items()):
        status = data.get("status", "ACTIVE")
        if status == "STANDBY":
            prog_bar = "[dim][░░░░░░░░░░] RSV[/dim]"
            action_disp = "[dim]Synaptic reserve (cross-coalitions)[/dim]"
        else:
            pct = float(data.get("progress_pct", 0.0))
            bar_width = 10
            filled = int(round((pct / 100.0) * bar_width))
            filled = max(0, min(bar_width, filled))
            empty = bar_width - filled
            bar_color = (
                "bold green" if pct >= 100 else ("bold cyan" if pct >= 50 else "bold yellow")
            )
            prog_bar = (
                f"[{bar_color}]{'█' * filled}[/{bar_color}][dim]{'░' * empty}[/dim] {int(pct):>3}%"
            )
            action_disp = data.get("action", "Coordinating domain arms...")
            if len(action_disp) > 55:
                action_disp = action_disp[:52] + "..."

        arms_list = data.get("arms", ["·"] * 8)
        arm_badges = []
        bolt_char = glyph("BOLT")
        ok_char = glyph("OK")
        for idx, sym in enumerate(arms_list):
            if sym in ("\u26a1", "↯", "!"):
                arm_badges.append(f"[bold yellow]\\[{idx}{bolt_char}][/bold yellow]")
            elif sym in ("✔", "✓", "+"):
                arm_badges.append(f"[bold green]\\[{idx}{ok_char}][/bold green]")
            else:
                arm_badges.append(f"[dim]\\[{idx}·][/dim]")
        matrix_str = " ".join(arm_badges)

        color_tag = data.get("color_tag", "cyan")
        title_str = f"[{color_tag}]{data.get('title', f'Octopus {oct_id}')}[/{color_tag}]"

        grid.add_row(
            f"◈ Octo {oct_id}",
            title_str,
            prog_bar,
            matrix_str,
            action_disp,
        )

    legend_text = f"[dim]Matrix Key: [bold yellow][{bolt_char}][/bold yellow] Arm Firing  [bold green][{ok_char}][/bold green] Arm Completed  [dim][·][/dim] Neural Standby[/dim]"
    synaptic_panel = Panel(
        Text.from_markup(f"{bolt_char} [bold]Synaptic Event Stream:[/bold] {last_event_msg}\n{legend_text}"),
        title=f"[{theme.rich_secondary}]Inter-Octopus Synaptic Bus[/{theme.rich_secondary}]",
        border_style=theme.rich_secondary,
    )

    # Render LLM Cascade Pool status if configured
    llm_cascade_panel = None
    cfg_file = get_octoflow_dir() / "config.json"
    if cfg_file.exists():
        try:
            cfg_data = load_secure_config(cfg_file)
            pool = cfg_data.get("llm_pool", [])
            if pool:
                llm_table = Table(box=box.SIMPLE, show_header=True, expand=True, padding=(0, 1))
                llm_table.add_column("Priority", style="bold cyan", width=10)
                llm_table.add_column("Provider / Model", style="white", width=28)
                llm_table.add_column("Endpoint URL", style="dim", width=36)
                llm_table.add_column("Cascade State", style="bold green", width=18)
                for idx, p in enumerate(pool):
                    p_stat = (
                        "[bold green]ACTIVE[/bold green]"
                        if idx == 0
                        else "[dim]STANDBY (Hot-Swap)[/dim]"
                    )
                    url_disp = p.get("base_url") or "Default Cloud"
                    if len(url_disp) > 34:
                        url_disp = url_disp[:32] + "..."
                    p_name = f"{p.get('name', 'Model')} ({p.get('model', 'default')})"
                    llm_table.add_row(f"[#{idx + 1}]", p_name, url_disp, p_stat)
                llm_cascade_panel = Panel(
                    llm_table,
                    title="[bold cyan]Neural LLM Cascade & Token Failover Pool (Auto-Hot-Swap)[/bold cyan]",
                    border_style="cyan",
                )
        except Exception:
            pass

    full_layout = Table.grid(expand=True)
    full_layout.add_row(metrics_table)
    full_layout.add_row(info_banner)
    full_layout.add_row(visualizer_banner)
    full_layout.add_row(grid)
    full_layout.add_row(synaptic_panel)
    if llm_cascade_panel:
        full_layout.add_row(llm_cascade_panel)

    return Panel(
        full_layout,
        border_style=theme.rich_border,
        title=f"[{theme.rich_primary}]OctosFlow Cephalopod Consortium ({total_arms} Neural Arms)[/{theme.rich_primary}]",
    )


def render_dashboard(
    objective: str,
    morphology: str,
    arm_states: dict,
    active_coalitions: list,
    tokens_saved_pct: float,
    total_cost: float,
    last_event_msg: str,
    visualizer_url: str = "http://localhost:8088",
    progress_pct: float = 0.0,
    cycle: int = 1,
    max_cycles: int = 10,
    quiescent_count: int = 0,
    elapsed_seconds: float = 0.0,
    theme: OctoTheme | None = None,
    budget_line: str | None = None,
) -> Panel:
    """Render the reactive cephalopod terminal dashboard using Rich."""
    if theme is None:
        theme = load_saved_theme()

    # Top metrics bar
    metrics_table = Table.grid(expand=True)
    metrics_table.add_column(justify="left")
    metrics_table.add_column(justify="right")

    status_text = Text()
    status_text.append(" ◈ OCTOFLOW v1.0.0", style=theme.rich_primary)
    status_text.append(f" | Mode: {morphology.upper()}", style=theme.rich_secondary)
    status_text.append(f" | Objective: {objective[:45]}...", style="white")

    savings_style = theme.rich_success if tokens_saved_pct >= 50.0 else theme.rich_warning
    badge_text = Text()
    if budget_line:
        badge_text.append(f"{budget_line} | ", style=theme.rich_secondary)
    badge_text.append(f"Tokens Saved: {tokens_saved_pct:.1f}% ", style=savings_style)
    badge_text.append(f"| Cost: ${total_cost:.3f} ", style="bold white")
    badge_text.append(f"| Coalitions: {len(active_coalitions)}", style=theme.rich_primary)

    metrics_table.add_row(status_text, badge_text)

    # Mission Progress & ETA Banner
    mins, secs = divmod(int(elapsed_seconds), 60)
    elapsed_str = f"{mins:02d}:{secs:02d}"

    bar_width = 16
    filled = int((progress_pct / 100.0) * bar_width)
    filled = min(bar_width, max(0, filled))
    bar_str = "█" * filled + "░" * (bar_width - filled)

    prog_color = (
        theme.rich_success
        if progress_pct >= 85.0
        else theme.rich_primary
        if progress_pct >= 40.0
        else theme.rich_warning
    )
    progress_bar_display = f"[{prog_color}][{bar_str}] {progress_pct:.1f}%[/{prog_color}]"

    if progress_pct >= 5.0 and progress_pct < 100.0:
        est_total = elapsed_seconds / (progress_pct / 100.0)
        remaining = max(0.0, est_total - elapsed_seconds)
        rem_m, rem_s = divmod(int(remaining), 60)
        eta_str = f"~{rem_m:02d}:{rem_s:02d} left"
    elif progress_pct >= 100.0:
        eta_str = f"[{theme.rich_success}]Complete[/{theme.rich_success}]"
    else:
        eta_str = "estimating..."

    hourglass_char = glyph("HOURGLASS")
    progress_banner = Panel(
        Text.from_markup(
            f" ● [bold white]Elapsed:[/bold white] [{theme.rich_primary}]{elapsed_str}[/{theme.rich_primary}]  |  "
            f"{hourglass_char} [bold white]ETA:[/bold white] [{theme.rich_warning}]{eta_str}[/{theme.rich_warning}]  |  "
            f"◈ [bold white]Mission Progress:[/bold white] {progress_bar_display}  "
            f"[dim](Cycle {cycle}/{max_cycles} • {quiescent_count}/8 Arms Finished)[/dim]"
        ),
        border_style=theme.rich_border,
        padding=(0, 1),
    )

    # Live Visualizer Link Banner
    visualizer_banner = Panel(
        Text.from_markup(
            f" ● [bold white]Live 3D Brain Visualizer:[/bold white] [{theme.rich_primary} underline]{visualizer_url}[/{theme.rich_primary} underline]  "
            f"[dim](Cmd+Click link to watch neural connectome & 8 arms fire live in browser)[/dim]"
        ),
        border_style=theme.rich_success,
        padding=(0, 1),
    )

    # 8-Arm Grid Table
    grid = Table(show_header=True, header_style=theme.rich_secondary, expand=True, padding=(0, 1))
    grid.add_column("Arm ID", width=8, style=theme.rich_primary)
    grid.add_column("Role", width=22)
    grid.add_column("Status", width=18)
    grid.add_column("Surprise Meter (ΔS / θ)", width=26)
    grid.add_column("Current Tool Execution", ratio=1)

    status_styles = {
        "SILENT_WORKING": f"[{theme.rich_success}]● SILENT EXEC[/{theme.rich_success}]",
        "COALITION_BOUND": f"[{theme.rich_primary}]⇄ COALITION[/{theme.rich_primary}]",
        "ESCALATED": f"[{theme.rich_danger}]▲ ESCALATED[/{theme.rich_danger}]",
        "QUIESCENT": "[dim white]○ QUIESCENT[/dim white]",
        "IDLE": "[dim]IDLE[/dim]",
    }

    for arm_id in range(8):
        st = arm_states.get(
            arm_id,
            {
                "role": f"Arm {arm_id}",
                "status": "IDLE",
                "surprise": 0.0,
                "threshold": 0.50,
                "action": "Waiting...",
            },
        )

        surp = st["surprise"]
        thresh = st["threshold"]
        blocks = int(surp * 10)
        bar = "█" * blocks + "░" * (10 - blocks)

        color = "red" if surp > thresh else "green" if surp < 0.20 else "yellow"
        bar_formatted = f"[{color}][{bar}] {surp:.2f} / {thresh:.2f}[/{color}]"

        raw_action = st["action"]
        if st["status"] == "QUIESCENT":
            action_display = f"[{theme.rich_success}]✔ Deliverable Complete[/{theme.rich_success}] [dim]({raw_action[:40]})[/dim]"
        elif len(raw_action) > 55:
            action_display = f"{raw_action[:52]}..."
        else:
            action_display = raw_action

        status_disp = status_styles.get(st["status"], st["status"])
        grid.add_row(f"Arm {arm_id}", st["role"], status_disp, bar_formatted, action_display)

    # Dynamic Coalition Panel
    coalition_desc = "None (All arms executing independently in parallel silence)"
    if active_coalitions:
        coalition_desc = " ⇄ ".join([f"Coalition {c}" for c in active_coalitions])

    bolt_char = glyph("BOLT")
    coalition_panel = Panel(
        Text(
            f"⇄ Active Attention Coalitions: {coalition_desc}\n{bolt_char} Event Stream: {last_event_msg}",
            style=theme.rich_primary,
        ),
        title=f"[{theme.rich_secondary}]Dynamic Neural Binding[/{theme.rich_secondary}]",
        border_style=theme.rich_secondary,
    )

    full_layout = Table.grid(expand=True)
    full_layout.add_row(metrics_table)
    full_layout.add_row(progress_banner)
    full_layout.add_row(visualizer_banner)
    full_layout.add_row(grid)
    full_layout.add_row(coalition_panel)

    return Panel(
        full_layout,
        border_style=theme.rich_border,
        title=f"[{theme.rich_primary}]Cephalopod Neural Swarm[/{theme.rich_primary}]",
    )
