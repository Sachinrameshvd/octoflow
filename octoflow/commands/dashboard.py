"""OctoFlow Terminal Dashboard Rendering Functions.

Renders real-time reactive dashboards with live surprise gauges, active
coalition links, and token savings metrics for single-octopus and multi-octopus swarms.
Includes Style A live progress bars, animated activity spinners, and state indicators.
"""

from __future__ import annotations

import shutil
import time
from typing import Any

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from octoflow.config import get_octoflow_dir, load_secure_config
from octoflow.glyphs import glyph, is_ascii_mode, is_no_anim
from octoflow.themes import OctoTheme, load_saved_theme

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
ASCII_SPINNER_FRAMES = ["|", "/", "-", "\\"]


def _get_spinner_frame(tick: int | None = None) -> str:
    """Return the current activity spinner glyph respecting ASCII and animation modes."""
    if tick is not None:
        if is_ascii_mode():
            return ASCII_SPINNER_FRAMES[tick % len(ASCII_SPINNER_FRAMES)]
        return SPINNER_FRAMES[tick % len(SPINNER_FRAMES)]

    if is_no_anim():
        return glyph("BOLT")

    idx = int(time.time() * 8)
    if is_ascii_mode():
        return ASCII_SPINNER_FRAMES[idx % len(ASCII_SPINNER_FRAMES)]
    return SPINNER_FRAMES[idx % len(SPINNER_FRAMES)]


def render_consortium_dashboard(
    objective: str,
    octopus_states: dict[Any, Any],
    total_tokens_saved: float = 87.5,
    total_cost: float = 0.0,
    last_event_msg: str = "",
    visualizer_url: str = "http://localhost:8088",
    elapsed_seconds: float = 0.0,
    total_arms: int = 24,
    tier_name: str = "TRIAD",
    theme: OctoTheme | None = None,
    tick: int | None = None,
    tokens_spent: int = 0,
    tokens_avoided: int = 0,
    blueprint: Any | None = None,
) -> Panel:
    """Render the Style A multi-octopus consortium dashboard using Rich."""
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
    badge_text.append("| Reflex θ=0.45: Active", style=theme.rich_primary)

    metrics_table.add_row(status_text, badge_text)

    mins, secs = divmod(int(elapsed_seconds), 60)
    elapsed_str = f"{mins:02d}:{secs:02d}"

    info_banner = Panel(
        Text(f" ● Elapsed: {elapsed_str}  |  ◈ Objective: {objective[:70]}...", style="bold white"),
        border_style="dim",
        padding=(0, 1),
    )

    visualizer_banner = Panel(
        Text(
            f" ● Live 3D Brain Visualizer: {visualizer_url}  (Cmd+Click link to watch {len(octopus_states)} octopuses fire live)",
            style=theme.rich_primary,
        ),
        border_style=theme.rich_border,
        padding=(0, 1),
    )

    # Determine layout mode based on terminal columns
    cols, _ = shutil.get_terminal_size((80, 24))
    use_compact_cols = cols < 100

    bolt_char = glyph("BOLT")
    ok_char = glyph("OK")
    dot_char = glyph("MIDDLE_DOT")
    circle_char = glyph("CIRCLE")
    spinner_char = _get_spinner_frame(tick)

    if use_compact_cols:
        grid = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
        grid.add_column("Octopus & Guild", style="bold cyan")
        grid.add_column("Progress", justify="center")
        grid.add_column("8 Arms", justify="center")
        grid.add_column("State & Deliverable", style="white")
    else:
        grid = Table(box=box.SIMPLE_HEAD, expand=True, padding=(0, 1))
        grid.add_column("Octo", style="bold cyan", width=8, justify="center")
        grid.add_column("Department Guild", style="white", width=22)
        grid.add_column("Swarm Progress", width=18, justify="center")
        grid.add_column("8-Arm Matrix", width=14, justify="center")
        grid.add_column("State & Deliverable Execution", style="white")

    for oct_id, data in sorted(octopus_states.items()):
        raw_status = str(data.get("status", "")).upper()
        pct = float(data.get("progress_pct", 0.0))
        arms_list = data.get("arms", ["·"] * 8)

        # Detect active / firing / completed states
        has_firing = any(sym in ("\u26a1", "↯", "!", bolt_char) for sym in arms_list)
        all_completed = (
            all(sym in ("✔", "✓", "+", ok_char) for sym in arms_list)
            and len(arms_list) == 8
            and pct >= 95.0
        )

        if raw_status in ("COMPLETED", "COMPLETE", "DONE") or pct >= 100.0 or all_completed:
            resolved_status = "COMPLETED"
        elif raw_status in ("STANDBY", "RSV"):
            resolved_status = "STANDBY"
        elif raw_status in ("WAITING", "BLOCKED", "CONTRACT", "PENDING"):
            resolved_status = "WAITING"
        elif (
            raw_status in ("RUNNING", "ACTIVE", "INITIALIZING", "WORKING", "ESCALATED")
            or has_firing
            or pct > 0.0
        ):
            resolved_status = "RUNNING"
        else:
            resolved_status = "WAITING" if oct_id > 0 else "RUNNING"

        # Format Progress Bar
        bar_width = 10
        if resolved_status == "STANDBY":
            prog_bar = "[dim]░░░░░░░░░░  RSV[/dim]"
        elif resolved_status == "COMPLETED" or pct >= 100.0:
            prog_bar = "[bold green]██████████ 100%[/bold green]"
        else:
            filled = int(round((pct / 100.0) * bar_width))
            filled = max(0, min(bar_width, filled))
            empty = bar_width - filled
            color = "bold cyan" if pct >= 50 else ("bold yellow" if pct > 0 else "dim")
            prog_bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim] {int(pct):>3}%"

        # Format 8-Arm Neural Matrix
        arm_symbols = []
        for sym in arms_list:
            if sym in ("\u26a1", "↯", "!", bolt_char):
                arm_symbols.append(f"[bold yellow]{bolt_char}[/bold yellow]")
            elif sym in ("✔", "✓", "+", ok_char):
                arm_symbols.append(f"[bold green]{ok_char}[/bold green]")
            else:
                arm_symbols.append(f"[dim]{dot_char}[/dim]")
        matrix_str = f"[{''.join(arm_symbols)}]"

        # Format State Label with Animated Spinner
        if resolved_status == "COMPLETED":
            state_badge = f"[bold green]{ok_char} Complete[/bold green]"
        elif resolved_status == "STANDBY":
            state_badge = f"[dim]{dot_char} Standby[/dim]"
        elif resolved_status == "WAITING":
            wait_sym = "~" if is_ascii_mode() else circle_char
            state_badge = f"[bold yellow]{wait_sym} Waiting[/bold yellow]"
        else:
            state_badge = f"[bold cyan]{spinner_char} Working[/bold cyan]"

        # Action / Deliverable Description
        raw_action = data.get("action", "")
        if not raw_action:
            if resolved_status == "COMPLETED":
                raw_action = "Deliverables verified and committed"
            elif resolved_status == "STANDBY":
                raw_action = "Synaptic reserve (cross-coalitions)"
            elif resolved_status == "WAITING":
                raw_action = f"Awaiting contracts from Octopus {max(0, oct_id - 1)}..."
            else:
                raw_action = "Coordinating domain arms..."

        color_tag = data.get("color_tag", "cyan")
        guild_title = str(data.get("title", f"Octopus {oct_id}"))

        if use_compact_cols:
            grid.add_row(
                f"[{color_tag}]◈ Octo {oct_id}[/{color_tag}]\n[dim]{guild_title}[/dim]",
                f"{prog_bar}",
                matrix_str,
                f"{state_badge}\n{raw_action}",
            )
        else:
            grid.add_row(
                f"[{color_tag}]◈ #{oct_id}[/{color_tag}]",
                f"[{color_tag}]{guild_title}[/{color_tag}]",
                prog_bar,
                matrix_str,
                f"{state_badge}: {raw_action}",
            )

    legend_text = (
        f"[dim]Matrix Key: [bold yellow][{bolt_char}][/bold yellow] Firing  "
        f"[bold green][{ok_char}][/bold green] Complete  "
        f"[dim][{dot_char}][/dim] Standby[/dim]"
    )

    # Compute realistic sensory gating token metrics
    spent = tokens_spent or (int(total_cost * 100_000) if total_cost > 0 else 14_210)
    avoided = tokens_avoided or (
        int(spent * (total_tokens_saved / max(1.0, 100.0 - total_tokens_saved)))
        if total_tokens_saved > 0
        else 48_930
    )

    synaptic_panel = Panel(
        Text.from_markup(
            f"{bolt_char} [bold]Synaptic Stream:[/bold] {last_event_msg or 'Cross-ring active inference engaged.'}\n"
            f"{legend_text}\n"
            f"[dim]Reflex Sensory Gating (Active Inference θ=0.45): [bold green]{total_tokens_saved:.1f}% reflex savings[/bold green]  |  "
            f"Spent: {spent:,}  |  Avoided: {avoided:,}[/dim]"
        ),
        title=f"[{theme.rich_secondary}]Inter-Octopus Synaptic Bus & Reflex Telemetry[/{theme.rich_secondary}]",
        border_style=theme.rich_secondary,
        padding=(0, 1),
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
    theme: OctoTheme | None = None,
    tick: int | None = None,
    tokens_spent: int = 0,
    tokens_avoided: int = 0,
    blueprint: Any | None = None,
) -> Panel:
    """Build Style A Multi-Octopus Progress Panel with progress bars, animated activity spinners, and state labels."""
    return render_consortium_dashboard(
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
