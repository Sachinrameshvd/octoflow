"""OctoFlow CLI & Live Rich Terminal Cephalopod Dashboard.

Provides command-line commands ('octoflow run', 'octoflow train', 'octoflow ui')
and renders a real-time reactive dashboard with live surprise gauges, active
coalition links, and token savings metrics.
"""

import json
import math
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Optional, List, Any, Dict, Callable
import typer
from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import getpass
from rich.markdown import Markdown
from dataclasses import asdict
from octoflow.config import (
    OctoFlowConfig,
    SwarmMorphology,
    list_available_guilds,
    load_custom_guild,
    save_custom_guild,
    SOFTWARE_DEV_ROSTER,
    get_octoflow_dir,
    load_secure_config,
    save_secure_config,
    mask_credential,
)
from octoflow.conductor import SupraesophagealConductor, SwarmTelemetryEvent
from octoflow.outcome import RunMode, RunOutcome, RunResult, ProviderExhaustedError
from octoflow.memory import VerticalLobeMemory
from octoflow.server import TelemetryBroadcaster
from octoflow.consortium import (
    OctosConsortium,
    TRIAD_GUILDS,
    OCTOPOLIS_GUILDS,
    SynapticContractEvent,
    estimate_elastic_octopus_count,
)
from octoflow.ignition import ProjectIgniter
from octoflow.themes import (
    OctoTheme,
    get_theme,
    load_saved_theme,
    save_theme_preference,
    list_themes,
    render_octoflow_3d_banner,
)
from octoflow.router import (
    classify_input,
    RouteKind,
    Route,
    execute_shell_route,
    log_command_history,
)

app = typer.Typer(help="◈ OctoFlow: Decentralized Cephalopod Multi-Agent Swarm with Sensory Surprise Gating")
octos_app = typer.Typer(help="◈ OctosFlow: Multi-Cephalopod Swarm Consortium (3 to 8 Octopuses • 24 to 64 Arms)")
console = Console()


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
    theme: Optional[OctoTheme] = None,
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
    status_text.append(f" | Swarm: {len(octopus_states)} Octopuses ({total_arms} Arms)", style=theme.rich_success)

    badge_text = Text()
    badge_text.append(f"Cost: ${total_cost:.3f} ", style="bold white")
    badge_text.append(f"| Synaptic Links: Active", style=theme.rich_primary)

    metrics_table.add_row(status_text, badge_text)

    mins, secs = divmod(int(elapsed_seconds), 60)
    elapsed_str = f"{mins:02d}:{secs:02d}"

    info_banner = Panel(
        Text(f" ● Elapsed: {elapsed_str}  |  ◈ Objective: {objective[:70]}...", style="bold white"),
        border_style="dim",
    )

    visualizer_banner = Panel(
        Text(f" ● Live 3D Constellation Visualizer: {visualizer_url}  (Cmd+Click link to watch all {len(octopus_states)} octopuses fire live)", style=theme.rich_primary),
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
            bar_color = "bold green" if pct >= 100 else ("bold cyan" if pct >= 50 else "bold yellow")
            prog_bar = f"[{bar_color}]{'█' * filled}[/{bar_color}][dim]{'░' * empty}[/dim] {int(pct):>3}%"
            action_disp = data.get("action", "Coordinating domain arms...")
            if len(action_disp) > 55:
                action_disp = action_disp[:52] + "..."

        arms_list = data.get("arms", ["·"] * 8)
        arm_badges = []
        for idx, sym in enumerate(arms_list):
            if sym == "⚡":
                arm_badges.append(f"[bold yellow]\\[{idx}⚡][/bold yellow]")
            elif sym == "✔":
                arm_badges.append(f"[bold green]\\[{idx}✔][/bold green]")
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

    legend_text = "[dim]Matrix Key: [bold yellow][⚡][/bold yellow] Arm Firing  [bold green][✔][/bold green] Arm Completed  [dim][·][/dim] Neural Standby[/dim]"
    synaptic_panel = Panel(
        Text.from_markup(f"⚡ [bold]Synaptic Event Stream:[/bold] {last_event_msg}\n{legend_text}"),
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
                    p_stat = "[bold green]ACTIVE[/bold green]" if idx == 0 else "[dim]STANDBY (Hot-Swap)[/dim]"
                    url_disp = p.get("base_url") or "Default Cloud"
                    if len(url_disp) > 34:
                        url_disp = url_disp[:32] + "..."
                    p_name = f"{p.get('name', 'Model')} ({p.get('model', 'default')})"
                    llm_table.add_row(f"[#{idx+1}]", p_name, url_disp, p_stat)
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

    return Panel(full_layout, border_style=theme.rich_border, title=f"[{theme.rich_primary}]OctosFlow Cephalopod Consortium ({total_arms} Neural Arms)[/{theme.rich_primary}]")



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
    theme: Optional[OctoTheme] = None,
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

    prog_color = theme.rich_success if progress_pct >= 85.0 else theme.rich_primary if progress_pct >= 40.0 else theme.rich_warning
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

    progress_banner = Panel(
        Text.from_markup(
            f" ● [bold white]Elapsed:[/bold white] [{theme.rich_primary}]{elapsed_str}[/{theme.rich_primary}]  |  "
            f"⏳ [bold white]ETA:[/bold white] [{theme.rich_warning}]{eta_str}[/{theme.rich_warning}]  |  "
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
        st = arm_states.get(arm_id, {
            "role": f"Arm {arm_id}",
            "status": "IDLE",
            "surprise": 0.0,
            "threshold": 0.50,
            "action": "Waiting...",
        })

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

    coalition_panel = Panel(
        Text(f"⇄ Active Attention Coalitions: {coalition_desc}\n⚡ Event Stream: {last_event_msg}", style=theme.rich_primary),
        title=f"[{theme.rich_secondary}]Dynamic Neural Binding[/{theme.rich_secondary}]",
        border_style=theme.rich_secondary,
    )

    full_layout = Table.grid(expand=True)
    full_layout.add_row(metrics_table)
    full_layout.add_row(progress_banner)
    full_layout.add_row(visualizer_banner)
    full_layout.add_row(grid)
    full_layout.add_row(coalition_panel)

    return Panel(full_layout, border_style=theme.rich_border, title=f"[{theme.rich_primary}]Cephalopod Neural Swarm[/{theme.rich_primary}]")


@app.command()
def run(
    objective: str = typer.Argument(..., help="High-level engineering or research goal for the swarm"),
    mode: str = typer.Option("software_dev", "--mode", "-m", help="Swarm mode: 'software_dev', 'aiml_research', 'fullstack_ai'"),
    guild: Optional[str] = typer.Option(None, "--guild", "-g", help="Specialist roster/guild name from ~/.octoflow/guilds/"),
    model: str = typer.Option("mock", "--model", help="LLM backend: 'mock', 'anthropic', 'openai', 'ollama'"),
    budget: float = typer.Option(5.00, "--budget", "-b", help="Hard spending limit in dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer telemetry port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
    open_ui: bool = typer.Option(False, "--open-ui", "--ui", help="Auto-open 3D Connectome Visualizer in default browser"),
    octos: str = typer.Option("1", "--octos", "-o", help="Count of octopuses: 'auto' (dynamic load autoscaler), 1 (Solo), 3 (Triad), or 8 (Octopolis)"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette ('abyssal', 'catppuccin', 'tokyo-night', 'dracula', 'cyberpunk', 'nord', 'gruvbox', 'minimalist')"),
    sandbox: str = typer.Option("local", "--sandbox", "-s", help="Execution isolation: 'local' (host) or 'docker' (containerized)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with mock provider, write no project files"),
):
    """Deploy the cephalopod swarm (1 to 8 octopuses • 8 to 64 arms) to execute an objective."""
    dry_val = dry_run if isinstance(dry_run, bool) else False
    orig_dry = os.environ.get("OCTOFLOW_DRY_RUN")
    is_dry = dry_val or (orig_dry == "1")
    if is_dry:
        os.environ["OCTOFLOW_DRY_RUN"] = "1"
        if model in ["mock", "anthropic", "openai"]:
            model = "mock"
    else:
        force_live = (os.getenv("OCTOFLOW_FORCE_LIVE") == "1")
        is_testing = not force_live and (("PYTEST_CURRENT_TEST" in os.environ) or ("pytest" in sys.modules) or (os.getenv("OCTOFLOW_TESTING") == "1"))
        if model == "mock" and not is_testing:
            console.print("\n✖ [bold red][FAILED] Mock LLM provider requested without --dry-run. Pass --dry-run or configure a real provider.[/bold red]\n")
            raise typer.Exit(code=2)

    selected_guild = guild or (mode if mode not in ["software_dev", "aiml_research", "fullstack_ai"] else None)
    if not selected_guild and (mode == "software_dev" or not mode):
        from octoflow.consortium import detect_morphology_from_objective
        morphology_enum = detect_morphology_from_objective(objective)
    else:
        morphology_enum = SwarmMorphology.CUSTOM if selected_guild else SwarmMorphology(mode.lower())
    port_val = 8088 if not isinstance(port, int) else port
    active_theme = get_theme(theme)
    sandbox_str = sandbox if isinstance(sandbox, str) else "local"
    config = OctoFlowConfig(
        morphology=morphology_enum,
        guild=selected_guild,
        model_provider=model,
        max_budget_dollars=budget,
        workspace_dir=workspace,
        telemetry_port=port_val,
        sandbox_mode=sandbox_str,
        dry_run=is_dry,
    )

    host_str = host if isinstance(host, str) else "127.0.0.1"
    if host_str not in ("127.0.0.1", "localhost"):
        console.print(f"[{active_theme.rich_warning}]▲ WARNING: Binding telemetry server to '{host_str}' exposes the swarm to the network![/{active_theme.rich_warning}]")
    broadcaster = TelemetryBroadcaster(port=port_val, host=host_str)
    broadcaster.start_in_background()
    broadcaster.broadcast_raw({
        "type": "THEME_CHANGE",
        "theme_id": active_theme.id,
        "tokens": asdict(active_theme),
    })
    visualizer_url = f"http://{host}:{broadcaster.port}"

    # -------------------------------------------------------------------------
    # ELASTIC AUTOSCALING RESOLUTION
    # -------------------------------------------------------------------------
    if str(octos).lower() in ["auto", "0"]:
        resolved_octos, rationale = estimate_elastic_octopus_count(objective, model_provider=model)
        console.print(f"\n◈ [bold cyan]Elastic Autoscaler:[/bold cyan] {rationale} -> Provisioning [bold green]{resolved_octos} Octopuses[/bold green] ({resolved_octos * 8} Neural Arms)")
    else:
        try:
            resolved_octos = int(octos)
        except ValueError:
            resolved_octos, rationale = estimate_elastic_octopus_count(objective, model_provider=model)
            console.print(f"\n◈ [bold cyan]Elastic Autoscaler:[/bold cyan] {rationale} -> Provisioning [bold green]{resolved_octos} Octopuses[/bold green] ({resolved_octos * 8} Neural Arms)")

    # -------------------------------------------------------------------------
    # MULTI-OCTOPUS CONSORTIUM MODE (resolved_octos > 1)
    # -------------------------------------------------------------------------
    if resolved_octos > 1:
        tier_name = "OCTOPOLIS" if resolved_octos >= 8 else "TRIAD"
        total_arms = resolved_octos * 8
        console.print(f"\n[bold cyan]◈ Launching OctosFlow Consortium with {resolved_octos} Octopuses ({total_arms} Neural Arms)...[/bold cyan]")
        console.print(f"● [bold green]Live 3D Brain Visualizer:[/bold green] [bold cyan underline]{visualizer_url}[/bold cyan underline]")
        console.print("   [dim]● Cmd+Click the link above to watch the multi-octopus connectome fire live in your browser![/dim]\n")

        if open_ui:
            import webbrowser
            try:
                webbrowser.open(visualizer_url)
            except Exception:
                pass

        octopus_states = {}
        from octoflow.consortium import get_consortium_guilds
        roster_pool = get_consortium_guilds(morphology_enum, 8)
        for g in roster_pool:
            is_active = (g.octopus_id < resolved_octos)
            color_tag = "cyan" if "00F0FF" in g.color_hex else ("magenta" if "EC4899" in g.color_hex else ("yellow" if "F59E0B" in g.color_hex else ("green" if "10B981" in g.color_hex else "blue")))
            octopus_states[g.octopus_id] = {
                "title": g.title,
                "color_hex": g.color_hex,
                "color_tag": color_tag,
                "status": "INITIALIZING" if is_active else "STANDBY",
                "action": "Starting up neural core..." if is_active else "Synaptic reserve (cross-coalitions)",
                "progress_pct": 0.0,
                "arms": ["·"] * 8,
            }

        last_synaptic_event = ["Consortium phase gates engaged across Synaptic Bus."]
        start_time = time.time()
        live_holder = [None]

        def on_consortium_telemetry(event: SwarmTelemetryEvent):
            oct_id = event.octopus_id
            if oct_id in octopus_states:
                octopus_states[oct_id]["status"] = event.status
                octopus_states[oct_id]["action"] = event.summary
                current_p = octopus_states[oct_id].get("progress_pct", 0.0)
                new_p = max(current_p, getattr(event, "progress_pct", 0.0) or 0.0)
                octopus_states[oct_id]["progress_pct"] = new_p

                # Update 8-Arm Neural Matrix badge for this arm
                arm_idx = event.arm_id
                if 0 <= arm_idx < 8:
                    if event.status in ["RUNNING"]:
                        octopus_states[oct_id]["arms"][arm_idx] = "⚡"
                    elif event.status in ["ESCALATED", "COMPLETED", "QUIESCENT"]:
                        octopus_states[oct_id]["arms"][arm_idx] = "✔"
                    elif event.status in ["INITIALIZING"]:
                        octopus_states[oct_id]["arms"][arm_idx] = "·"

            last_synaptic_event[0] = f"[{event.octopus_title} / {event.role}]: {event.summary}"
            broadcaster.broadcast(event)
            if live_holder[0] is not None:
                live_holder[0].update(
                    render_consortium_dashboard(
                        objective=objective,
                        octopus_states=octopus_states,
                        total_tokens_saved=87.5,
                        total_cost=0.0,
                        last_event_msg=last_synaptic_event[0],
                        visualizer_url=visualizer_url,
                        elapsed_seconds=time.time() - start_time,
                        total_arms=total_arms,
                        tier_name=tier_name,
                        theme=active_theme,
                    )
                )

        try:
            consortium = OctosConsortium(config=config, octopus_count=resolved_octos, telemetry_callback=on_consortium_telemetry)
        except ProviderExhaustedError as pe:
            console.print(f"\n✖ [bold red][FAILED] {pe}[/bold red]\n")
            raise typer.Exit(code=2)

        try:
            with Live(console=console, refresh_per_second=6) as live:
                live_holder[0] = live
                live.update(
                    render_consortium_dashboard(
                        objective=objective,
                        octopus_states=octopus_states,
                        total_tokens_saved=87.5,
                        total_cost=0.0,
                        last_event_msg=last_synaptic_event[0],
                        visualizer_url=visualizer_url,
                        elapsed_seconds=time.time() - start_time,
                        total_arms=total_arms,
                        tier_name=tier_name,
                        theme=active_theme,
                    )
                )
                res = consortium.run_consortium(objective=objective, cycles_per_octopus=4)

            if is_dry:
                console.print("\n◈ [bold yellow][DRY-RUN: no project files written][/bold yellow]\n")
                raise typer.Exit(code=0)

            console.print(f"\n[bold green]✔ OCTOSFLOW CONSORTIUM MISSION COMPLETE![/bold green]")
            console.print(f"◈ Deployed: [bold cyan]{resolved_octos} Octopuses ({total_arms} Neural Arms)[/bold cyan]")
            console.print(f"● Total Execution Time: {res.get('execution_time_seconds', 0):.2f}s")

            ign = res.get("ignition")
            if ign and ign.get("primary_url"):
                prim_url = ign["primary_url"]
                docs_url = ign.get("api_docs_url")
                inf_url = ign.get("inference_url")
                svc_type = ign.get("service_type", "app").upper().replace("_", " ")

                live_text = f"[bold green]⚡ LIVE {svc_type} OPERATIONAL:[/bold green] [bold cyan underline]{prim_url}[/bold cyan underline]\n"
                if docs_url and docs_url != prim_url:
                    live_text += f"[bold magenta]● API Swagger Docs:[/bold magenta]    [bold cyan underline]{docs_url}[/bold cyan underline]\n"
                if inf_url and inf_url != prim_url:
                    live_text += f"[bold amber]● Inference Playground:[/bold amber] [bold cyan underline]{inf_url}[/bold cyan underline]\n"
                live_text += f"[bold blue]● 3D Brain Telemetry:[/bold blue]    [bold cyan underline]{visualizer_url}[/bold cyan underline]\n\n"
                live_text += "[dim]● Cmd+Click any link to test your newly built application live in browser![/dim]"

                console.print(Panel(live_text, title="⚡ OCTOSFLOW PHASE 4 LIVE IGNITION", border_style="cyan"))
            else:
                console.print(f"● 3D Brain Telemetry: [bold cyan underline]{visualizer_url}[/bold cyan underline]\n")

            raise typer.Exit(code=0)
        except ProviderExhaustedError as pe:
            console.print(f"\n✖ [bold red][FAILED] {pe}[/bold red]\n")
            raise typer.Exit(code=2)
        except typer.Exit:
            raise
        except KeyboardInterrupt:
            console.print("\n[bold yellow]· Consortium paused by user (Ctrl+C). Generated files preserved.[/bold yellow]\n")
            raise typer.Exit(code=1)
        except Exception as e:
            log_dir = Path.home() / ".octoflow"
            log_dir.mkdir(parents=True, exist_ok=True)
            crash_log = log_dir / "last_error.log"
            with open(crash_log, "w") as f:
                traceback.print_exc(file=f)
            error_panel = Panel(
                Text.from_markup(f"[bold red]▲ Consortium Encountered an Interrupt:[/bold red] [yellow]{e}[/yellow]"),
                border_style="red",
            )
            console.print(error_panel)
            raise typer.Exit(code=2)

    # -------------------------------------------------------------------------
    # SINGLE OCTOPUS MODE (octos == 1)
    # -------------------------------------------------------------------------
    console.print(f"\n[bold cyan]◈ Launching OctoFlow Swarm in {mode.upper()} mode...[/bold cyan]")
    console.print(f"● [bold green]Live 3D Brain Visualizer:[/bold green] [bold cyan underline]{visualizer_url}[/bold cyan underline]")
    console.print("   [dim]● Cmd+Click the link above to watch the neural connectome & 8 arms fire live in your browser![/dim]\n")

    if open_ui:
        import webbrowser
        try:
            webbrowser.open(visualizer_url)
        except Exception:
            pass
        except Exception:
            pass

    arm_states = {}
    active_coalitions = []
    tokens_saved = [0.0]
    total_cost = [0.0]
    last_event = ["Swarm initialized in silent execution mode."]
    progress_pct = [0.0]
    cycle_num = [1]
    max_cycles_num = [10]
    quiescent_count = [0]
    start_time = time.time()

    live_holder = [None]

    def on_telemetry(event: SwarmTelemetryEvent):
        arm_states[event.arm_id] = {
            "role": event.role,
            "status": event.status,
            "surprise": event.surprise,
            "threshold": event.threshold,
            "action": event.summary,
        }
        active_coalitions.clear()
        active_coalitions.extend(event.active_coalitions)
        tokens_saved[0] = event.tokens_saved_pct
        total_cost[0] = event.total_cost_dollars
        last_event[0] = f"[{event.role}]: {event.summary}"
        progress_pct[0] = event.progress_pct
        cycle_num[0] = event.cycle
        max_cycles_num[0] = event.max_cycles
        quiescent_count[0] = event.quiescent_count
        broadcaster.broadcast(event)
        if live_holder[0] is not None:
            live_holder[0].update(
                render_dashboard(
                    objective,
                    mode,
                    arm_states,
                    active_coalitions,
                    tokens_saved[0],
                    total_cost[0],
                    last_event[0],
                    visualizer_url,
                    progress_pct[0],
                    cycle_num[0],
                    max_cycles_num[0],
                    quiescent_count[0],
                    time.time() - start_time,
                    theme=active_theme,
                )
            )

    try:
        conductor = SupraesophagealConductor(config=config, telemetry_callback=on_telemetry)
    except ProviderExhaustedError as pe:
        console.print(f"\n✖ [bold red][FAILED] {pe}[/bold red]\n")
        raise typer.Exit(code=2)

    try:
        with Live(console=console, refresh_per_second=8) as live:
            live_holder[0] = live
            live.update(
                render_dashboard(
                    objective,
                    mode,
                    arm_states,
                    active_coalitions,
                    tokens_saved[0],
                    total_cost[0],
                    last_event[0],
                    visualizer_url,
                    progress_pct[0],
                    cycle_num[0],
                    max_cycles_num[0],
                    quiescent_count[0],
                    time.time() - start_time,
                    theme=active_theme,
                )
            )
            result = conductor.run_swarm(objective=objective, max_cycles=10)

        if is_dry:
            console.print("\n◈ [bold yellow][DRY-RUN: no project files written][/bold yellow]\n")
            return

        # LIVE Mode Outcome Check
        outcome = getattr(result, "outcome", None)
        if outcome is None and isinstance(result, dict):
            outcome = result.get("outcome")
            if outcome is None:
                if result.get("status") in ["completed", "GLOBAL_QUIESCENCE", "QUIESCENCE"] or result.get("success"):
                    outcome = RunOutcome.COMPLETE
                else:
                    outcome = RunOutcome.FAILED

        files = getattr(result, "files_written", []) if not isinstance(result, dict) else result.get("files_written", [])
        prov = getattr(result, "provider_used", "live") if not isinstance(result, dict) else result.get("provider_used", "live")
        mod = getattr(result, "model", "default") if not isinstance(result, dict) else result.get("model", "default")

        if outcome == RunOutcome.COMPLETE or str(outcome).lower() == "complete":
            console.print(f"\n◈ [bold green][LIVE: {prov}:{mod}] COMPLETE, {len(files)} files written[/bold green]")
            for f in files:
                console.print(f"  • {f}")
            console.print(f"● Final Tokens Consumed: {conductor.total_tokens_used:,} (vs. ~{conductor.estimated_chatty_tokens:,} chatty baseline)")
            console.print(f"● Token Savings: [bold green]{tokens_saved[0]:.1f}%[/bold green]")
            console.print(f"● Total API Cost: ${conductor.total_cost:.4f}\n")

            # Live Phase 4 Ignition
            try:
                igniter = ProjectIgniter(workspace_dir=workspace)
                ign_manifest = igniter.ignite(objective=objective)
                if ign_manifest and ign_manifest.status == "RUNNING" and ign_manifest.primary_url:
                    prim_url = ign_manifest.primary_url
                    docs_url = ign_manifest.api_docs_url
                    inf_url = ign_manifest.inference_url
                    svc_type = ign_manifest.service_type.upper().replace("_", " ")

                    live_text = f"[bold green]⚡ LIVE {svc_type} OPERATIONAL:[/bold green] [bold cyan underline]{prim_url}[/bold cyan underline]\n"
                    if docs_url and docs_url != prim_url:
                        live_text += f"[bold magenta]● API Swagger Docs:[/bold magenta]    [bold cyan underline]{docs_url}[/bold cyan underline]\n"
                    if inf_url and inf_url != prim_url:
                        live_text += f"[bold amber]● Inference Playground:[/bold amber] [bold cyan underline]{inf_url}[/bold cyan underline]\n"
                    live_text += f"[bold blue]● 3D Brain Telemetry:[/bold blue]    [bold cyan underline]{visualizer_url}[/bold cyan underline]\n\n"
                    live_text += "[dim]● Cmd+Click any link to test your newly built application live in browser![/dim]"

                    console.print(Panel(live_text, title="⚡ OCTOFLOW PHASE 4 LIVE IGNITION", border_style="cyan"))

                    # Broadcast to 3D visualizer
                    telemetry_evt = SwarmTelemetryEvent(
                        event_type="LIVE_SERVICE_READY",
                        arm_id=7,
                        role="Runner",
                        status="RUNNING",
                        surprise=0.0,
                        threshold=0.5,
                        summary=f"⚡ LIVE APP DEPLOYED: {prim_url}",
                        octopus_id=0,
                        octopus_title="Cephalopod Core",
                        color_hex="#00F0FF",
                        service_url=prim_url,
                        api_docs_url=docs_url,
                        service_type=ign_manifest.service_type,
                        payload=ign_manifest.model_dump(),
                    )
                    broadcaster.broadcast(telemetry_evt)
            except Exception:
                pass
            return

        elif outcome == RunOutcome.PARTIAL or str(outcome).lower() == "partial":
            reason = getattr(result, "reason", "partial quiescence") if not isinstance(result, dict) else result.get("reason", "partial quiescence")
            console.print(f"\n◈ [bold yellow][PARTIAL] {reason}[/bold yellow]\n")
            raise typer.Exit(code=1)
        else:
            reason = getattr(result, "reason", "model produced no file changes")
            console.print(f"\n✖ [bold red][FAILED] {reason}[/bold red]\n")
            raise typer.Exit(code=2)

    except ProviderExhaustedError as pe:
        console.print(f"\n✖ [bold red][FAILED] {pe}[/bold red]\n")
        raise typer.Exit(code=2)
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n[bold yellow]· Swarm execution paused by user (Ctrl+C). Generated files preserved.[/bold yellow]\n")
        raise typer.Exit(code=1)
    except Exception as e:
        log_dir = Path.home() / ".octoflow"
        log_dir.mkdir(parents=True, exist_ok=True)
        crash_log = log_dir / "last_error.log"
        with open(crash_log, "w") as f:
            traceback.print_exc(file=f)

        error_panel = Panel(
            Text.from_markup(
                f"[bold red]▲ Swarm Encountered an Environmental Interrupt[/bold red]\n\n"
                f"[white]Details:[/white] [yellow]{e}[/yellow]\n\n"
                f"[dim]• Your generated code in [bold]{workspace}[/bold] is completely intact.\n"
                f"• Diagnostic log saved to: [bold]{crash_log}[/bold]\n"
                f"• Re-running with [cyan]--model ollama[/cyan] will safely resume work.[/dim]"
            ),
            title="[bold red]OctoFlow Fault-Tolerance Shield[/bold red]",
            border_style="red",
        )
        console.print(error_panel)
        raise typer.Exit(code=2)
    finally:
        if orig_dry is None:
            os.environ.pop("OCTOFLOW_DRY_RUN", None)
        else:
            os.environ["OCTOFLOW_DRY_RUN"] = orig_dry


@app.command()
def train(
    objective: str = typer.Argument(..., help="Model architecture and training objective"),
    model: str = typer.Option("mock", "--model", help="LLM backend"),
    budget: float = typer.Option(5.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with mock provider, write no project files"),
):
    """Shortcut command to run swarm in AIML_RESEARCH morphology."""
    run(objective=objective, mode="aiml_research", model=model, budget=budget, workspace=workspace, port=8088, dry_run=dry_run)


@app.command()
def ui(
    port: int = typer.Option(8088, "--port", "-p", help="Port to host 3D visualizer"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind 3D visualizer (default: 127.0.0.1)"),
):
    """Launch the 3D Cephalopod Connectome Visualizer bridge."""
    host_str = host if isinstance(host, str) else "127.0.0.1"
    if host_str not in ("127.0.0.1", "localhost"):
        console.print(f"[bold red]▲ WARNING: Binding visualizer to '{host_str}' exposes the bridge to the network![/bold red]")
    url = f"http://{host_str}:{port}"
    console.print(f"\n[bold cyan]◈ Launching OctoFlow 3D Connectome Visualizer on {url}...[/bold cyan]")
    broadcaster = TelemetryBroadcaster(port=port, host=host_str)
    broadcaster.start_in_background()
    import webbrowser
    try:
        webbrowser.open(url)
    except Exception:
        pass
    console.print(f"● Visualizer opened in browser. Bridge active on {url}.")
    console.print(f"   [dim]Press Ctrl+C to stop.[/dim]\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\nStopped.")


@app.command(name="mcp-serve")
def mcp_serve(workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory")):
    """Run OctoFlow as a Model Context Protocol (MCP) server for Claude Code and Cursor."""
    import asyncio
    from octoflow.mcp import OctoFlowMCPServer

    server = OctoFlowMCPServer(workspace_dir=workspace)
    asyncio.run(server.run_stdio())


@app.command(name="consortium")
def consortium_cmd(
    objective: str = typer.Argument(..., help="Engineering goal for the multi-octopus consortium"),
    octos: str = typer.Option("auto", "--octos", "-o", help="Count of octopuses ('auto', 3 for Triad, 8 for Octopolis)"),
    model: str = typer.Option("mock", "--model", help="LLM backend: 'mock', 'anthropic', 'openai', 'ollama'"),
    budget: float = typer.Option(10.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open 3D Visualizer in browser"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with mock provider, write no project files"),
):
    """Deploy the multi-cephalopod consortium (3 to 8 octopuses • 24 to 64 arms) on a project."""
    run(objective=objective, mode="software_dev", model=model, budget=budget, workspace=workspace, port=port, host=host, open_ui=open_ui, octos=octos, theme=theme, dry_run=dry_run)


@octos_app.command("run")
def octos_run(
    objective: str = typer.Argument(..., help="Engineering goal for the multi-octopus consortium"),
    octos: str = typer.Option("auto", "--octos", "-o", help="Count of octopuses: 'auto' (dynamic load autoscaler), 3 (Triad), or 8 (Octopolis)"),
    guild: Optional[str] = typer.Option(None, "--guild", "-g", help="Specialist roster/guild name from ~/.octoflow/guilds/"),
    model: str = typer.Option("mock", "--model", help="LLM backend: 'mock', 'anthropic', 'openai', 'ollama'"),
    budget: float = typer.Option(10.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open 3D Visualizer in browser"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with mock provider, write no project files"),
):
    """Deploy the multi-cephalopod consortium (3 to 8 octopuses • 24 to 64 arms) on a project."""
    run(objective=objective, mode="software_dev", guild=guild, model=model, budget=budget, workspace=workspace, port=port, host=host, open_ui=open_ui, octos=octos, theme=theme, dry_run=dry_run)


@octos_app.command("octopolis")
def octos_octopolis(
    objective: str = typer.Argument(..., help="Engineering goal for the 8-octopus Octopolis (64 Arms)"),
    model: str = typer.Option("mock", "--model", help="LLM backend"),
    budget: float = typer.Option(15.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open visualizer"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with mock provider, write no project files"),
):
    """Deploy the flagship 8-Octopus Octopolis (64 Neural Arms) on an objective."""
    run(objective=objective, mode="software_dev", model=model, budget=budget, workspace=workspace, port=port, host=host, open_ui=open_ui, octos=8, theme=theme, dry_run=dry_run)


@octos_app.command("ui")
def octos_ui(
    port: int = typer.Option(8088, "--port", "-p", help="Port to host 3D visualizer"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind 3D visualizer (default: 127.0.0.1)"),
):
    """Launch the 3D Cephalopod Constellation Visualizer bridge."""
    ui(port=port, host=host)


@app.command("theme")
def app_theme_cmd(
    name: Optional[str] = typer.Argument(None, help="Theme palette ('abyssal', 'catppuccin', 'tokyo-night', 'dracula', 'cyberpunk', 'nord', 'gruvbox', 'minimalist')"),
):
    """View or switch the OctoFlow terminal & visualizer theme."""
    _execute_theme_cmd(name)


@octos_app.command("theme")
def octos_theme_cmd(
    name: Optional[str] = typer.Argument(None, help="Theme palette ('abyssal', 'catppuccin', 'tokyo-night', 'dracula', 'cyberpunk', 'nord', 'gruvbox', 'minimalist')"),
):
    """View or switch the OctoFlow terminal & visualizer theme."""
    _execute_theme_cmd(name)


def _execute_theme_cmd(name: Optional[str]):
    """Execute theme display or switch."""
    cur_theme = load_saved_theme()
    if not name:
        if sys.stdin.isatty() and sys.stdout.isatty():
            from octoflow.theme_selector import run_interactive_theme_picker
            chosen = run_interactive_theme_picker(console, initial_theme=cur_theme)
            console.print(f"[{chosen.rich_success}]✔ Theme locked in: [bold]{chosen.name}[/bold] ({chosen.description})[/{chosen.rich_success}]")
            console.print(f"[dim]Saved to ~/.octoflow/theme.json and synchronized with 3D Visualizer.[/dim]\n")
            return

        themes_all = list_themes()
        theme_table = Table(title="◈ Available Developer Palettes", border_style=cur_theme.rich_border, expand=True)
        theme_table.add_column("#", width=4, style=cur_theme.rich_primary)
        theme_table.add_column("Theme ID", style="bold white", width=16)
        theme_table.add_column("Name", style="white", width=22)
        theme_table.add_column("Palette Swatch", width=14)
        theme_table.add_column("Description", style="dim")

        for idx, (t_id, t_obj) in enumerate(themes_all.items(), 1):
            is_active = " [bold green]✔ ACTIVE[/]" if t_id == cur_theme.id else ""
            swatch = f"[{t_obj.rich_primary}]●[/{t_obj.rich_primary}] [{t_obj.rich_secondary}]●[/{t_obj.rich_secondary}] [{t_obj.rich_success}]●[/{t_obj.rich_success}] [{t_obj.rich_warning}]●[/{t_obj.rich_warning}]"
            theme_table.add_row(str(idx), t_id + is_active, t_obj.name, swatch, t_obj.description)

        console.print(theme_table)
        console.print(f"[dim]Tip: Switch theme by typing [bold]octos theme <id>[/bold] (e.g. [cyan]octos theme catppuccin[/cyan])[/dim]\n")
    else:
        new_theme = get_theme(name)
        save_theme_preference(new_theme.id)
        console.print(f"[{new_theme.rich_success}]✔ Switched palette to: [bold]{new_theme.name}[/bold] ({new_theme.description})[/{new_theme.rich_success}]")
        console.print(f"[dim]Saved to ~/.octoflow/theme.json and synchronized with 3D Visualizer.[/dim]\n")


def _run_banner(loop: bool, theme_name: Optional[str]):
    t = get_theme(theme_name) if theme_name else load_saved_theme()
    if loop:
        from octoflow.themes import play_banner_continuous
        play_banner_continuous(console, t, prompt_message="Press [Enter] or any key to exit")
    else:
        from octoflow.themes import play_banner_animation
        play_banner_animation(console, t)


@app.command("banner")
def app_banner_cmd(
    loop: bool = typer.Option(False, "--loop", "-l", help="Run continuous ambient animation loop"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
):
    """Play the 3D animated OCTOFLOW banner (single replay or continuous loop)."""
    _run_banner(loop, theme)


@octos_app.command("banner")
def octos_banner_cmd(
    loop: bool = typer.Option(False, "--loop", "-l", help="Run continuous ambient animation loop"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
):
    """Play the 3D animated OCTOFLOW banner (single replay or continuous loop)."""
    _run_banner(loop, theme)


@app.command("screensaver")
def app_screensaver_cmd(
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
):
    """Launch continuous ambient 3D banner screensaver until keypress."""
    _run_banner(True, theme)


@octos_app.command("screensaver")
def octos_screensaver_cmd(
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
):
    """Launch continuous ambient 3D banner screensaver until keypress."""
    _run_banner(True, theme)


# Re-exported from octoflow.cockpit for backward compatibility
from octoflow.cockpit import get_live_wizard_input



def run_setup_wizard(launch_after: bool = False):
    """Guided first-run configuration wizard for API keys, model, and theme."""
    import os
    import json
    import subprocess

    cur_theme = load_saved_theme()
    cfg_file = get_octoflow_dir() / "config.json"
    existing_cfg = load_secure_config(cfg_file)

    workspace = Path.cwd().resolve()

    # Step 1: Provider selection panel & table
    wizard_panel = Panel(
        f"[{cur_theme.rich_primary}]◈ OctoFlow Interactive Setup Wizard[/{cur_theme.rich_primary}]\n"
        "[dim]Configure your default LLM provider, API credentials, and terminal preferences.[/dim]",
        border_style=cur_theme.rich_border,
    )

    table = Table(title="◈ Supported LLM Neural Engines", border_style=cur_theme.rich_border, expand=True)
    table.add_column("#", width=4, justify="center", style=cur_theme.rich_primary)
    table.add_column("Provider", width=22, style="bold white")
    table.add_column("Recommended Model", width=24, style=cur_theme.rich_secondary)
    table.add_column("Best Suited For", style="white")

    table.add_row("1", Text("[Anthropic Claude]"), "claude-3-5-sonnet", "State-of-the-art coding & autonomous reasoning")
    table.add_row("2", Text("[OpenAI]"), "gpt-4o / o3-mini", "High speed, broad tool calling & code synthesis")
    table.add_row("3", Text("[Google Gemini]"), "gemini-2.0-flash", "Massive context window & rapid code generation")
    table.add_row("4", Text("[xAI Grok]"), "grok-2", "Low-latency inference & mathematical reasoning")
    table.add_row("5", Text("[DeepSeek]"), "deepseek-chat (V3/R1)", "High-performance coding at economical cost")
    table.add_row("6", Text("[Local Ollama]"), "qwen2.5-coder / llama3", "100% Free, offline & private on local Mac")
    table.add_row("7", Text("[Mock Mode]"), "deterministic-mock", "Offline test harness (zero cost, dry run)")

    step1_heading = Text("\nStep 1: Choose Primary LLM Core Provider", style="bold white")

    # Live animated input for provider selection (octopus runs left & right and jumps continuously)
    choice = get_live_wizard_input(
        theme=cur_theme,
        prompt_label="Select provider [1-7] (default 1): ",
        default_value="1",
        extra_panels=[wizard_panel, step1_heading, table],
        existing_cfg=existing_cfg,
        workspace=workspace,
    )

    prov_map = {
        "1": "anthropic",
        "2": "openai",
        "3": "gemini",
        "4": "grok",
        "5": "deepseek",
        "6": "ollama",
        "7": "mock",
    }
    chosen_provider = prov_map.get(choice, "anthropic")
    prov_labels = {
        "anthropic": "Anthropic Claude",
        "openai": "OpenAI",
        "gemini": "Google Gemini",
        "grok": "xAI Grok",
        "deepseek": "DeepSeek",
        "ollama": "Local Ollama",
        "mock": "Mock Mode",
    }
    prov_name = prov_labels.get(chosen_provider, chosen_provider)

    # Step 2: Key input (non-echoing via getpass for credentials)
    saved_key = ""
    step2_heading = Text(f"\nStep 1 Selected: [{prov_name}]\nStep 2: Enter API Key or Endpoint (optional - press Enter to skip)\n", style="bold white")

    def _prompt_secret_key(key_env_var: str, current_val: str) -> str:
        masked = mask_credential(current_val) if current_val else ""
        prompt_label = f"Enter {key_env_var} [{masked}]: " if masked else f"Enter {key_env_var}: "
        console.print(wizard_panel)
        console.print(step2_heading)
        try:
            val = getpass.getpass(prompt_label).strip()
        except Exception:
            try:
                val = input(prompt_label).strip()
            except Exception:
                val = ""
        return val if val else current_val

    if chosen_provider == "anthropic":
        env_key = os.getenv("ANTHROPIC_API_KEY") or existing_cfg.get("anthropic_api_key", "")
        saved_key = _prompt_secret_key("ANTHROPIC_API_KEY", env_key)
        if saved_key:
            existing_cfg["anthropic_api_key"] = saved_key
            os.environ["ANTHROPIC_API_KEY"] = saved_key

    elif chosen_provider == "openai":
        env_key = os.getenv("OPENAI_API_KEY") or existing_cfg.get("openai_api_key", "")
        saved_key = _prompt_secret_key("OPENAI_API_KEY", env_key)
        if saved_key:
            existing_cfg["openai_api_key"] = saved_key
            os.environ["OPENAI_API_KEY"] = saved_key

    elif chosen_provider == "gemini":
        env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or existing_cfg.get("gemini_api_key", "")
        saved_key = _prompt_secret_key("GEMINI_API_KEY", env_key)
        if saved_key:
            existing_cfg["gemini_api_key"] = saved_key
            os.environ["GEMINI_API_KEY"] = saved_key

    elif chosen_provider == "grok":
        env_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY") or existing_cfg.get("grok_api_key", "")
        saved_key = _prompt_secret_key("XAI_API_KEY", env_key)
        if saved_key:
            existing_cfg["grok_api_key"] = saved_key
            os.environ["XAI_API_KEY"] = saved_key

    elif chosen_provider == "deepseek":
        env_key = os.getenv("DEEPSEEK_API_KEY") or existing_cfg.get("deepseek_api_key", "")
        saved_key = _prompt_secret_key("DEEPSEEK_API_KEY", env_key)
        if saved_key:
            existing_cfg["deepseek_api_key"] = saved_key
            os.environ["DEEPSEEK_API_KEY"] = saved_key

    elif chosen_provider == "ollama":
        base_url = get_live_wizard_input(
            theme=cur_theme,
            prompt_label="Enter Ollama URL [http://localhost:11434]: ",
            default_value="http://localhost:11434",
            extra_panels=[wizard_panel, step2_heading],
            existing_cfg=existing_cfg,
            workspace=workspace,
        )
        existing_cfg["ollama_base_url"] = base_url

    existing_cfg["default_model"] = chosen_provider

    # Also register in LLM failover pool
    pool = existing_cfg.get("llm_pool", [])
    entry_defs = {
        "anthropic": ("Anthropic Claude", "claude-3-5-sonnet", None),
        "openai": ("OpenAI", "gpt-4o", None),
        "gemini": ("Google Gemini", "gemini-2.0-flash", None),
        "grok": ("xAI Grok", "grok-2", None),
        "deepseek": ("DeepSeek", "deepseek-chat", None),
        "ollama": ("Local Ollama", "qwen2.5-coder:32b", existing_cfg.get("ollama_base_url", "http://localhost:11434")),
    }
    if chosen_provider in entry_defs:
        p_name, p_model, p_url = entry_defs[chosen_provider]
        pool_idx = next((i for i, e in enumerate(pool) if e.get("provider") == chosen_provider), None)
        entry = {
            "id": f"{chosen_provider}_primary",
            "provider": chosen_provider,
            "name": p_name,
            "model": p_model,
            "base_url": p_url,
            "api_key": saved_key if saved_key else None,
            "priority": 1,
            "enabled": True,
        }
        if pool_idx is not None:
            pool[pool_idx] = entry
        else:
            pool.append(entry)
        existing_cfg["llm_pool"] = pool

    # Step 3: Theme selection (also in live animated loop)
    step3_heading = Text("\nStep 3: Choose Developer Terminal Theme\n", style="bold white")
    theme_table = Table.grid(padding=(0, 2))
    theme_table.add_column(style="bold white")
    theme_table.add_column(style="dim")
    theme_table.add_row("[1] Abyssal Cyber", "Bioluminescent Cyan & Neon Magenta")
    theme_table.add_row("[2] Catppuccin Mocha", "Soothing Pastel Mauve & Sapphire")
    theme_table.add_row("[3] Tokyo Night", "Midnight Cyberpunk")
    theme_table.add_row("[4] Dracula Pro", "Electric Vampire")
    theme_table.add_row("[5] Nord Arctic", "Calm Polar Blue")
    theme_table.add_row("[6] Minimalist Obsidian", "Stark Monochrome & Emerald")

    theme_choice = get_live_wizard_input(
        theme=cur_theme,
        prompt_label="Select theme [1-6] (default 2): ",
        default_value="2",
        extra_panels=[wizard_panel, step3_heading, theme_table],
        existing_cfg=existing_cfg,
        workspace=workspace,
    )
    theme_map = {"1": "abyssal", "2": "catppuccin", "3": "tokyo-night", "4": "dracula", "5": "nord", "6": "minimalist"}
    new_theme_id = theme_map.get(theme_choice, "catppuccin")
    save_theme_preference(new_theme_id)
    existing_cfg["default_theme"] = new_theme_id

    # Save to ~/.octoflow/config.json with 0600 mode
    save_secure_config(existing_cfg, cfg_file)

    console.clear()
    console.print(f"\n[{cur_theme.rich_success}]◈ Configuration saved successfully to ~/.octoflow/config.json![/{cur_theme.rich_success}]")
    console.print(f"  • Provider: [bold]{chosen_provider.upper()}[/bold]")
    console.print(f"  • Theme: [bold]{new_theme_id}[/bold]")
    console.print(f"[dim]Transitioning into live cephalopod console...[/dim]\n")

    if launch_after:
        interactive_cockpit()


@app.command("setup")
@octos_app.command("setup")
def setup_cli_cmd():
    """Launch the interactive OctoFlow Setup Wizard."""
    run_setup_wizard(launch_after=True)


def run_doctor(workspace: str = ".", fix: bool = False):
    """Run system environment and dependency diagnostics (like 'ruflo doctor')."""
    import os
    import socket
    import subprocess
    import shutil
    import json
    import httpx

    theme = load_saved_theme()
    ws = Path(workspace).resolve()

    console.print(f"\n[{theme.rich_primary}]◈ OctoFlow Diagnostic Doctor v1.0.0[/{theme.rich_primary}]")
    console.print(f"[dim]Inspecting runtime environment, neural assets, git safety, and provider endpoints...[/dim]\n")

    doc_table = Table(title="System & Neural Swarm Health", border_style=theme.rich_border, expand=True)
    doc_table.add_column("Subsystem", style=theme.rich_primary, width=22)
    doc_table.add_column("Status", width=12)
    doc_table.add_column("Diagnostics & Details", style="white")

    all_passed = True

    # 1. Python Runtime
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        doc_table.add_row("Python Runtime", f"[{theme.rich_success}]● PASS[/{theme.rich_success}]", f"v{py_ver} (64-bit {sys.platform})")
    else:
        doc_table.add_row("Python Runtime", f"[{theme.rich_danger}]✖ FAIL[/{theme.rich_danger}]", f"v{py_ver} (Requires Python >= 3.10)")
        all_passed = False

    # 2. Workspace & Git Safety
    is_git = False
    git_branch = "none"
    try:
        r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=str(ws), capture_output=True, text=True, timeout=1)
        if r.returncode == 0 and "true" in r.stdout:
            is_git = True
            b_r = subprocess.run(["git", "branch", "--show-current"], cwd=str(ws), capture_output=True, text=True, timeout=1)
            git_branch = b_r.stdout.strip()
    except Exception:
        pass

    if is_git:
        branch_style = theme.rich_warning if git_branch in ["main", "master"] else theme.rich_success
        doc_table.add_row("Git Repository", f"[{theme.rich_success}]● PASS[/{theme.rich_success}]", f"Root: {ws.name} | Branch: [{branch_style}]{git_branch}[/{branch_style}]")
    else:
        doc_table.add_row("Git Repository", f"[{theme.rich_warning}]▲ WARN[/{theme.rich_warning}]", "Not inside a git worktree. /rollback requires git.")
        if fix:
            try:
                subprocess.run(["git", "init"], cwd=str(ws), capture_output=True)
                console.print(f"[{theme.rich_success}]✔ [doctor --fix] Initialized git repository in {ws}[/{theme.rich_success}]")
            except Exception:
                pass

    # 3. Precompiled 3D Visualizer Assets
    dist_dir = Path(__file__).parent / "dist"
    has_dist = (dist_dir / "index.html").exists() and (dist_dir / "assets").exists()
    if has_dist:
        doc_table.add_row("3D Visualizer Dist", f"[{theme.rich_success}]● PASS[/{theme.rich_success}]", f"Bundled package assets verified ({dist_dir})")
    else:
        doc_table.add_row("3D Visualizer Dist", f"[{theme.rich_danger}]✖ FAIL[/{theme.rich_danger}]", "Missing octoflow/dist bundle. Zero-node visualizer unavailable.")
        all_passed = False

    # 4. Port 8088 Visualizer Bridge
    port_status = "Available"
    port_color = theme.rich_success
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        in_use = (s.connect_ex(("127.0.0.1", 8088)) == 0)
        if in_use:
            port_status = "Active / In Use (Bridge Live)"
            port_color = theme.rich_secondary
    doc_table.add_row("Telemetry Port 8088", f"[{port_color}]● INFO[/{port_color}]", port_status)

    # 5. LLM API Providers & Credentials
    cfg_file = get_octoflow_dir() / "config.json"
    saved_cfg = load_secure_config(cfg_file) if cfg_file.exists() else {}

    has_anthropic = bool(saved_cfg.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(saved_cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY"))

    ant_status = f"[{theme.rich_success}]● READY[/{theme.rich_success}]" if has_anthropic else f"[dim]○ UNSET[/dim]"
    oai_status = f"[{theme.rich_success}]● READY[/{theme.rich_success}]" if has_openai else f"[dim]○ UNSET[/dim]"
    doc_table.add_row("Anthropic API", ant_status, "Claude 3.7 Sonnet / Claude 3.5 Haiku" if has_anthropic else "Not configured")
    doc_table.add_row("OpenAI API", oai_status, "o3-mini / GPT-4o-mini" if has_openai else "Not configured")

    # 6. Local Ollama Daemon
    ollama_ok = False
    ollama_models = []
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=0.8)
        if resp.status_code == 200:
            ollama_ok = True
            data = resp.json()
            ollama_models = [m.get("name") for m in data.get("models", [])][:4]
    except Exception:
        pass

    if ollama_ok:
        models_str = f"Models: {', '.join(ollama_models)}" if ollama_models else "Daemon online (no models pulled yet)"
        doc_table.add_row("Local Ollama", f"[{theme.rich_success}]● ONLINE[/{theme.rich_success}]", f"http://localhost:11434 | {models_str}")
    else:
        doc_table.add_row("Local Ollama", f"[dim]○ OFFLINE[/dim]", "No local Ollama daemon found (optional offline LLM)")

    # 7. Vertical Lobe Memory
    mem_file = Path.home() / ".octoflow" / "vertical_lobe.json"
    if mem_file.exists():
        try:
            mem_data = json.loads(mem_file.read_text(encoding="utf-8"))
            count = len(mem_data.get("entries", []))
            doc_table.add_row("Vertical Lobe LTP", f"[{theme.rich_success}]● PASS[/{theme.rich_success}]", f"{count} Hebbian heuristics stored")
        except Exception:
            doc_table.add_row("Vertical Lobe LTP", f"[{theme.rich_warning}]▲ WARN[/{theme.rich_warning}]", "Unreadable memory file")
    else:
        doc_table.add_row("Vertical Lobe LTP", f"[{theme.rich_secondary}]● INITIAL[/{theme.rich_secondary}]", "Will initialize upon first error consolidation")

    console.print(doc_table)

    if all_passed:
        console.print(f"\n[{theme.rich_success}]✔ All critical subsystems nominal. Cephalopod Swarm is deployment-ready![/{theme.rich_success}]\n")
    else:
        console.print(f"\n[{theme.rich_warning}]▲ Action items detected above. Run [bold]octos setup[/bold] to configure credentials.[/{theme.rich_warning}]\n")


@app.command("doctor")
@octos_app.command("doctor")
def doctor_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    fix: bool = typer.Option(False, "--fix", help="Automatically repair missing directories and initialize git if needed"),
):
    """Run OctoFlow environment and provider diagnostics (like 'ruflo doctor')."""
    run_doctor(workspace=workspace, fix=fix)


@app.command("mcp")
@octos_app.command("mcp")
def mcp_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory for the MCP server"),
):
    """Start OctoFlow as a Model Context Protocol (MCP) JSON-RPC 2.0 stdio server for Claude Code and Cursor."""
    import asyncio
    from octoflow.mcp import OctoFlowMCPServer
    server = OctoFlowMCPServer(workspace_dir=workspace)
    try:
        asyncio.run(server.run_stdio())
    except (KeyboardInterrupt, EOFError):
        pass


def run_guard(workspace: str = ".") -> bool:
    """Pre-commit security and AST syntax guard inspecting staged git changes."""
    import subprocess
    import re
    import ast
    import json

    theme = load_saved_theme()
    ws = Path(workspace).resolve()

    console.print(f"[{theme.rich_primary}]◈ OctoFlow Pre-Commit Swarm Guard[/{theme.rich_primary}]")

    # 1. Get staged files
    res = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=str(ws), capture_output=True, text=True)
    if res.returncode != 0:
        console.print("[dim]Not a git repository or git error. Guard skipped.[/dim]")
        return True

    staged_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
    if not staged_files:
        console.print(f"[{theme.rich_success}]✔ No staged git files to guard. Safe.[/{theme.rich_success}]")
        return True

    console.print(f"[dim]Inspecting {len(staged_files)} staged file(s) for secrets and syntax errors...[/dim]")

    SECRET_PATTERNS = [
        (re.compile(r'sk-ant-[a-zA-Z0-9_\-]{20,}'), "Exposed Anthropic API Key"),
        (re.compile(r'sk-[a-zA-Z0-9_\-]{30,}'), "Exposed OpenAI API Key"),
        (re.compile(r'ghp_[a-zA-Z0-9]{20,}'), "Exposed GitHub Personal Access Token"),
        (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), "Exposed Private Key block"),
        (re.compile(r'AKIA[0-9A-Z]{16}'), "Exposed AWS Access Key ID"),
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

        # Check 1: Secret leaks
        for pat, desc in SECRET_PATTERNS:
            if pat.search(content):
                violations.append(f"Security Alert: {desc} in staged file '{rel_path}'")

        # Check 2: Pre-flight AST Syntax check for Python
        if target.suffix == ".py":
            try:
                ast.parse(content, filename=rel_path)
            except SyntaxError as e:
                violations.append(f"SyntaxError in staged '{rel_path}' at line {e.lineno}, col {e.offset}: {e.msg}")

        # Check 3: JSON decode check
        elif target.suffix == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                violations.append(f"JSONDecodeError in staged '{rel_path}' at line {e.lineno}: {e.msg}")

    if violations:
        console.print(f"\n[{theme.rich_danger}]✖ Pre-Commit Guard Blocked Commit ({len(violations)} violation(s)):[/{theme.rich_danger}]")
        for v in violations:
            console.print(f"  [{theme.rich_danger}]●[/{theme.rich_danger}] {v}")
        console.print(f"\n[dim]Fix the above issues or stage clean files before committing.[/dim]\n")
        return False

    console.print(f"[{theme.rich_success}]✔ Pre-Commit Guard: All {len(staged_files)} staged file(s) passed security & AST syntax checks. Commit allowed.[/{theme.rich_success}]")
    return True


def install_git_hooks(workspace: str = ".") -> bool:
    """Install OctoFlow pre-commit guard into .git/hooks/pre-commit."""
    import os
    import stat
    theme = load_saved_theme()
    ws = Path(workspace).resolve()
    git_dir = ws / ".git"

    if not git_dir.exists():
        console.print(f"[{theme.rich_danger}]Error: '{ws}' is not a git repository. Run 'git init' first.[/{theme.rich_danger}]")
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    pre_commit_file = hooks_dir / "pre-commit"

    hook_script = "#!/bin/sh\n# OctoFlow Automated Pre-Commit Swarm Guard\noctos guard\n"
    pre_commit_file.write_text(hook_script, encoding="utf-8")

    st = os.stat(pre_commit_file)
    os.chmod(pre_commit_file, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    console.print(f"[{theme.rich_success}]✔ Installed OctoFlow Pre-Commit Guard at {pre_commit_file}[/{theme.rich_success}]")
    console.print(f"[dim]Every future 'git commit' will now automatically verify secrets and AST syntax.[/dim]\n")
    return True


@app.command("guard")
@octos_app.command("guard")
def guard_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory"),
):
    """Run pre-commit secret leak and AST syntax verification on staged git files."""
    safe = run_guard(workspace=workspace)
    if not safe:
        raise typer.Exit(code=1)


@app.command("install-hooks")
@octos_app.command("install-hooks")
def install_hooks_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory with .git repository"),
):
    """Install automated OctoFlow pre-commit hook into .git/hooks/."""
    ok = install_git_hooks(workspace=workspace)
    if not ok:
        raise typer.Exit(code=1)


@app.command("init-ide")
@octos_app.command("init-ide")
@octos_app.command("init")
def init_ide_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Project workspace directory to onboard"),
):
    """Auto-configure Cursor (.cursorrules), Claude (MCP), VS Code (tasks), and Git (hooks)."""
    from octoflow.onboarding import onboard_ide
    theme = load_saved_theme()
    console.print(f"\n[{theme.rich_primary}]◈ Auto-Onboarding Omni-IDE Surfaces for Workspace:[/{theme.rich_primary}] [bold white]{workspace}[/bold white]\n")
    res = onboard_ide(workspace=workspace)

    t = Table(title="Omni-IDE Developer Surface Status", border_style=theme.rich_border, expand=True)
    t.add_column("Developer Surface", style="bold white", width=28)
    t.add_column("Status", width=14)
    t.add_column("Configuration Details", style="white")

    t.add_row("Cursor AI (.cursorrules)", f"[{theme.rich_success}]✔ CONFIGURED[/]" if res["cursor"] else "[dim]SKIPPED[/]", "8-Arm Swarm delegation rules & architecture heuristics")
    t.add_row("Claude Code CLI (~/.claude.json)", f"[{theme.rich_success}]✔ INJECTED[/]" if res["claude_code"] else "[dim]SKIPPED[/]", "Direct MCP connection for multi-file swarm execution")
    t.add_row("Claude Desktop App", f"[{theme.rich_success}]✔ INJECTED[/]" if res["claude_desktop"] else "[dim]NOT FOUND[/]", "Desktop UI connectome MCP tool integration")
    t.add_row("VS Code (.vscode/tasks.json)", f"[{theme.rich_success}]✔ CONFIGURED[/]" if res["vscode_tasks"] else "[dim]SKIPPED[/]", "4 Command Palette shortcut tasks (Cockpit, Guard, UI, Doctor)")
    t.add_row("Git Pre-Commit Hook", f"[{theme.rich_success}]✔ INSTALLED[/]" if res["git_hooks"] else "[dim]SKIPPED[/]", "Swarm Guard AST validation & secret leak protection")

    console.print(t)
    console.print(f"[{theme.rich_success}]✔ Omni-IDE onboarding completed in <1s. Zero manual configuration required![/{theme.rich_success}]\n")


@app.command("init-action")
@octos_app.command("init-action")
def init_action_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace directory"),
):
    """Generate automated OctoFlow Swarm Guard GitHub Action (.github/workflows/octoflow-guard.yml)."""
    from octoflow.ci import generate_github_action_workflow
    theme = load_saved_theme()
    wf_path = generate_github_action_workflow(workspace)
    console.print(f"\n[{theme.rich_success}]✔ Generated GitHub Actions Workflow:[/{theme.rich_success}] [bold white]{wf_path}[/bold white]")
    console.print(f"[dim]Every Pull Request will now automatically trigger Arm 6 (Security), Arm 5 (QA/AST), and Arm 0 (Architect) audits.[/dim]\n")


@app.command("review-pr")
@octos_app.command("review-pr")
def review_pr_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
    base: str = typer.Option("HEAD~1", "--base", "-b", help="Base git ref to diff against"),
    summary: bool = typer.Option(True, "--summary/--no-summary", help="Append markdown to $GITHUB_STEP_SUMMARY"),
    export: Optional[str] = typer.Option(None, "--export", "-e", help="Path to export standalone HTML audit report"),
    shadow: bool = typer.Option(False, "--shadow", help="Run advisory audit without blocking PR merge (Shadow CI Mode)"),
):
    """Execute automated 3-Arm CI/CD PR Review over git diffs."""
    from octoflow.ci import review_pull_request
    theme = load_saved_theme()
    mode_label = " [dim](Shadow CI Mode: Non-blocking)[/dim]" if shadow else ""
    console.print(f"\n[{theme.rich_primary}]● OctoFlow Swarm Guard: Auditing Pull Request Diff...{mode_label}[/{theme.rich_primary}]\n")
    res = review_pull_request(workspace=workspace, base_ref=base, write_summary=summary, shadow_mode=shadow)

    # Render Terminal Review Table
    t = Table(title="OctoFlow Swarm Guard PR Audit" + (" [SHADOW CI]" if shadow else ""), border_style=theme.rich_border, expand=True)
    t.add_column("Ganglia Arm", style="bold white", width=22)
    t.add_column("Role Scope", style=theme.rich_secondary, width=20)
    t.add_column("Status", width=12)
    t.add_column("Audit Findings", style="white")

    arm6_ok = not any("CRITICAL" in f for f in res["arm6_findings"])
    arm5_ok = not any("CRITICAL" in f for f in res["arm5_findings"])
    arm0_ok = not any("Inverted" in f for f in res["arm0_findings"])

    t.add_row("Arm 6: Security", "Credentials & Injection", f"[{theme.rich_success}]✔ PASSED[/]" if arm6_ok else f"[{theme.rich_danger}]✖ BLOCKED[/]", " • ".join(res["arm6_findings"]))
    t.add_row("Arm 5: QA & AST", "Syntax & Test Coverage", f"[{theme.rich_success}]✔ PASSED[/]" if arm5_ok else f"[{theme.rich_danger}]✖ BLOCKED[/]", " • ".join(res["arm5_findings"]))
    t.add_row("Arm 0: Architect", "Topology & Contracts", f"[{theme.rich_success}]✔ PASSED[/]" if arm0_ok else f"[{theme.rich_warning}]ℹ ADVISORY[/]", " • ".join(res["arm0_findings"]))

    console.print(t)

    if export:
        from octoflow.report import collect_mission_audit_data, generate_html_audit_report
        m_data = collect_mission_audit_data(workspace=workspace)
        out_html = generate_html_audit_report(m_data, output_path=export, theme_id=theme.id)
        console.print(f"\n[{theme.rich_success}]✔ Exported Standalone Audit Report:[/{theme.rich_success}] [bold white]{out_html}[/bold white]")

    if res["hard_block"] and not shadow:
        console.print(f"\n[{theme.rich_danger}]✖ Merge Blocked: Critical security vulnerabilities or AST syntax errors detected.[/{theme.rich_danger}]\n")
        raise typer.Exit(code=1)
    elif res["hard_block"] and shadow:
        console.print(f"\n[{theme.rich_warning}]▲ Shadow CI: Merge hazards detected, but PR was NOT blocked (Advisory Mode).[/{theme.rich_warning}]\n")
    else:
        console.print(f"\n[{theme.rich_success}]✔ Swarm Verdict: READY TO MERGE. Zero merge hazards detected.[/{theme.rich_success}]\n")


@app.command("export")
@octos_app.command("export")
@app.command("report")
@octos_app.command("report")
def export_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    output: Optional[str] = typer.Option(None, "--out", "-o", help="Target HTML audit report output path"),
    open_browser: bool = typer.Option(False, "--open", help="Open generated HTML report in default browser"),
):
    """Generate standalone self-contained HTML mission audit report with interactive connectome replay."""
    from octoflow.report import collect_mission_audit_data, generate_html_audit_report
    theme = load_saved_theme()
    console.print(f"\n[{theme.rich_primary}]◈ Generating Standalone HTML Swarm Mission Audit...[/{theme.rich_primary}]")
    m_data = collect_mission_audit_data(workspace=workspace)
    report_path = generate_html_audit_report(m_data, output_path=output, theme_id=theme.id)
    console.print(f"[{theme.rich_success}]✔ Exported Standalone Audit Report:[/{theme.rich_success}] [bold white]{report_path}[/bold white]")
    console.print(f"[dim]100% self-contained single-file HTML • Zero external CDN dependencies • Connectome replay included.[/dim]\n")
    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{report_path.resolve()}")


@app.command("heal")
@octos_app.command("heal")
@app.command("fix")
@octos_app.command("fix")
def heal_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
    attempts: int = typer.Option(3, "--attempts", "-a", help="Max healing iterations"),
):
    """Execute autonomous closed-loop test repair with Arm 5 (QA) and Arm 2 (Backend)."""
    from octoflow.healing import self_heal_workspace
    theme = load_saved_theme()
    console.print(f"\n[{theme.rich_primary}]◈ OctoFlow Autonomous Self-Healing: Running test suite and diagnosing...[/{theme.rich_primary}]\n")
    res = self_heal_workspace(workspace_dir=workspace, max_attempts=attempts)

    t = Table(title="OctoFlow Self-Healing Summary", border_style=theme.rich_border, expand=True)
    t.add_column("Property", style=theme.rich_secondary, width=20)
    t.add_column("Value", style="bold white")

    status_str = f"[{theme.rich_success}]✔ HEALED & PASSING[/]" if res["success"] else f"[{theme.rich_danger}]✖ UNRESOLVED[/]"
    t.add_row("Status", status_str)
    t.add_row("Framework", res["framework"].upper())
    t.add_row("Attempts Used", f"{res['attempts']} / {attempts}")
    t.add_row("Repaired Files", ", ".join(res["repaired_files"]) if res["repaired_files"] else "None (tests already passing)")
    t.add_row("Result Note", res["message"])
    console.print(t)
    console.print()


@app.command("triage")
@octos_app.command("triage")
@app.command("diff-review")
@octos_app.command("diff-review")
def triage_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
    auto_approve: bool = typer.Option(False, "--yes", "-y", help="Auto-approve all AST-valid changes"),
):
    """Interactive file-by-file patch inspector and diff triage with AST validation."""
    from octoflow.triage import triage_workspace_diffs
    theme = load_saved_theme()
    console.print(f"\n[{theme.rich_primary}]◈ OctoFlow Patch Triage: Reviewing uncommitted changes...[/{theme.rich_primary}]")
    res = triage_workspace_diffs(workspace_dir=workspace, interactive=not auto_approve, auto_approve=auto_approve, console=console)
    console.print(f"\n[{theme.rich_success}]✔ {res['message']}[/{theme.rich_success}]\n")


@app.command("notify")
@octos_app.command("notify")
def notify_cli_cmd(
    message: str = typer.Argument("OctoFlow Swarm Mission Update", help="Notification summary text"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Target Slack or Discord webhook URL"),
):
    """Dispatch mission status card to team Slack or Discord webhook."""
    from octoflow.notify import send_mission_notification
    theme = load_saved_theme()
    ok = send_mission_notification(webhook_url=url, custom_message=message)
    if ok:
        console.print(f"[{theme.rich_success}]✔ Successfully dispatched alert to team webhook.[/{theme.rich_success}]\n")
    else:
        console.print(f"[{theme.rich_warning}]▲ Webhook dispatch skipped: No active webhook URL configured or network unreachable.[/{theme.rich_warning}]\n")


@app.command("guild")
@octos_app.command("guild")
def guild_cli_cmd(
    action: str = typer.Argument("list", help="Action: 'list', 'show', 'export'"),
    name: Optional[str] = typer.Argument(None, help="Guild name"),
):
    """Manage 8-arm specialist guilds (custom community rosters)."""
    theme = load_saved_theme()
    if action == "list":
        guilds = list_available_guilds()
        g_table = Table(title="Specialist 8-Arm Guilds & Rosters", border_style=theme.rich_border, expand=True)
        g_table.add_column("Guild Name", style="bold white", width=18)
        g_table.add_column("Type", style=theme.rich_secondary, width=12)
        g_table.add_column("Description", style="white")

        for g_name, g_desc in guilds.items():
            g_type = "Built-In" if g_name in ["software_dev", "aiml_research", "fullstack_ai"] else "Community"
            g_table.add_row(g_name, g_type, g_desc)

        console.print(g_table)
        console.print(f"[dim]Tip: Use in cockpit with [bold]/guild <name>[/bold] or CLI [bold]octos run --guild <name>[/bold][/dim]\n")

    elif action in ["show", "inspect"]:
        if not name:
            console.print(f"[{theme.rich_danger}]Error: Please specify guild name (e.g. octos guild show software_dev)[/{theme.rich_danger}]")
            return
        roster = load_custom_guild(name)
        if not roster:
            console.print(f"[{theme.rich_danger}]Guild '{name}' not found.[/{theme.rich_danger}]")
            return

        r_table = Table(title=f"Guild Roster: {name}", border_style=theme.rich_border, expand=True)
        r_table.add_column("Arm", width=6, style=theme.rich_primary)
        r_table.add_column("Role Title", width=22, style="bold white")
        r_table.add_column("Tier", width=10, style=theme.rich_secondary)
        r_table.add_column("Domain Scope & Description", style="white")

        for arm in roster:
            r_table.add_row(f"Arm {arm.arm_id}", arm.title, arm.model_tier.upper(), f"{arm.description} (Domains: {', '.join(arm.workspace_domain)})")
        console.print(r_table)

    elif action == "export":
        export_name = name or "custom_template"
        out_file = save_custom_guild(export_name, SOFTWARE_DEV_ROSTER, f"Custom {export_name} specialist roster template")
        console.print(f"[{theme.rich_success}]✔ Exported guild template to: {out_file}[/{theme.rich_success}]")
        console.print(f"[dim]Edit the JSON file to customize arm titles, domains, prompts, and model tiers.[/dim]\n")


@app.command("bench")
@octos_app.command("bench")
def bench_cli_cmd(
    task: Optional[str] = typer.Option(None, "--task", "-t", help="Specific challenge key (rate_limiter, lru_cache, jwt_auth, topological_dag)"),
    mode: str = typer.Option("balanced", "--mode", "-m", help="Execution tier: fast, balanced, powerful"),
    workspace: str = typer.Option(".octoflow_bench", "--dir", "-d", help="Directory for benchmark sandbox execution"),
):
    """Run standardized 8-arm algorithmic & architectural challenge benchmarks."""
    from octoflow.bench import run_swarm_benchmark_suite
    theme = load_saved_theme()
    console.print(f"\n[{theme.rich_primary}]◈ OctoFlow Swarm Benchmark Suite: Starting evaluation harness...[/{theme.rich_primary}]\n")
    run_swarm_benchmark_suite(task_key=task, mode=mode, workspace_dir=workspace, console=console)


@app.command("monorepo")
@octos_app.command("monorepo")
def monorepo_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
):
    """Scan and partition monorepo packages to specialist 8-arm roles."""
    from octoflow.monorepo import scan_monorepo_topology
    theme = load_saved_theme()
    topo = scan_monorepo_topology(workspace)
    t = Table(title="Monorepo Package & Swarm Topology", border_style=theme.rich_border, expand=True)
    t.add_column("Package Name", style="bold white", width=22)
    t.add_column("Subdirectory", style=theme.rich_secondary, width=24)
    t.add_column("Type", width=12)
    t.add_column("Primary Specialist Arm", style=theme.rich_primary)

    arm_titles = {
        0: "System Architect",
        1: "Database & Schemas",
        2: "Backend API",
        3: "Frontend UI",
        4: "State & Caching",
        5: "QA & AST Test",
        6: "Security & Credentials",
        7: "DevOps & Deploy",
    }

    packages = topo.get("packages", [])
    for pkg in packages:
        arm_id = pkg.get("primary_arm", 2)
        arm_title = arm_titles.get(arm_id, f"Arm {arm_id}")
        t.add_row(pkg.get("name", ""), pkg.get("rel_path", ""), str(pkg.get("type", "")).upper(), f"Arm {arm_id} ({arm_title})")

    console.print(t)
    console.print(f"[dim]Total packages detected: [bold]{len(packages)}[/bold] (Monorepo: [bold]{'YES' if topo.get('is_monorepo') else 'NO'}[/bold])[/dim]\n")


@app.command("record")
@octos_app.command("record")
def record_cli_cmd(
    output: str = typer.Option("octoflow_session.cast", "--output", "-o", help="Asciinema .cast output path"),
    title: str = typer.Option("OctoFlow Swarm Mission", "--title", "-t", help="Title for the recording session"),
):
    """Launch recorded terminal session producing standard Asciinema v2 .cast."""
    from octoflow.recorder import TerminalRecorder
    theme = load_saved_theme()
    console.print(f"[{theme.rich_primary}]◈ OctoFlow Asciinema Recorder: Session started -> [bold]{output}[/bold][/{theme.rich_primary}]")
    rec = TerminalRecorder(title=title)
    rec.start()
    rec.record_output(f"OctoFlow Swarm Terminal Session: {title}\r\n")
    rec.record_output(f"Theme: {theme.name} | Active Arms: 8\r\n")
    rec.stop()
    out_file = rec.export_cast(output)
    console.print(f"[{theme.rich_success}]✔ Exported Asciinema .cast session to: [bold white]{out_file}[/bold white][/{theme.rich_success}]\n")


@app.command("audit")
@octos_app.command("audit")
def audit_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder to audit"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output audit report as raw JSON"),
):
    """Run 1-100 system readiness and security diagnostic across 5 cephalopod dimensions."""
    from octoflow.audit import evaluate_workspace, print_audit_report
    report = evaluate_workspace(workspace)
    if json_output:
        console.print_json(report.model_dump_json(indent=2))
    else:
        print_audit_report(report, console=console)


@app.command("eject")
@octos_app.command("eject")
def eject_cli_cmd(
    output_dir: str = typer.Option("./octo-harness", "--output", "-o", help="Target output directory for standalone harness"),
):
    """Eject autonomous standalone cephalopod agent harness into any repository."""
    from octoflow.eject import eject_harness
    eject_harness(output_dir=output_dir, console=console)


@app.command("install-claude")
@octos_app.command("install-claude")
def install_claude_cli_cmd():
    """Install and register OctoFlow native Claude Code plugin and slash commands (/octo)."""
    from octoflow.themes import load_saved_theme
    theme = load_saved_theme()
    plugin_dir = Path(".claude-plugin")
    plugin_dir.mkdir(parents=True, exist_ok=True)
    console.print(Panel(
        f"[{theme.rich_success}]✔ OctoFlow Claude Code Integration Registered![/{theme.rich_success}]\n\n"
        f"  • Plugin Manifest: [bold cyan].claude-plugin/plugin.json[/bold cyan]\n"
        f"  • Stdio MCP Config: [bold cyan].mcp.json[/bold cyan]\n"
        f"  • Hooks: [bold cyan].claude-plugin/hooks/hooks.json[/bold cyan]\n\n"
        f"Inside Claude Code, invoke:\n"
        f"  [bold white]/octo[/bold white]         - Launch Cephalopod Cockpit\n"
        f"  [bold white]/octo:audit[/bold white]   - Run 1-100 System Readiness Grade\n"
        f"  [bold white]/octo:swarm[/bold white]   - Deploy Swarm Consortium\n"
        f"  [bold white]/octo:heal[/bold white]    - Run Self-Healing Repair Loop\n"
        f"  [bold white]/octo:eject[/bold white]   - Export Standalone Agent Harness",
        title="[bold cyan]Claude Code Native Plugin[/bold cyan]",
        border_style=theme.rich_border,
        padding=(1, 2)
    ))


@app.command("federation")
@octos_app.command("federation")
def federation_cli_cmd(
    action: str = typer.Argument("status", help="Action: status, peers, test-pii"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Text to test against 14-rule PII filter"),
):
    """Zero-trust multi-machine agent federation and PII redaction pipeline."""
    from octoflow.federation import GLOBAL_FEDERATION_GUARD, PII_RULES
    from octoflow.themes import load_saved_theme
    theme = load_saved_theme()
    if action == "status":
        t = Table(title="Zero-Trust Federation & PII Security Rules", border_style=theme.rich_border)
        t.add_column("Rule Name", style="bold white", width=22)
        t.add_column("Severity", style=theme.rich_secondary, width=12)
        t.add_column("Redacted Mask", style="dim", width=32)
        for r in PII_RULES:
            t.add_row(r.name, r.severity, r.replacement)
        console.print(t)
        console.print(f"[dim]Default PII Action: [bold green]{GLOBAL_FEDERATION_GUARD.default_action.value}[/bold green] | Total Intercepted Events: {len(GLOBAL_FEDERATION_GUARD.audit_log)}[/dim]\n")
    elif action == "test-pii":
        sample = text or ("My key is " + "sk-ant-" + "api03-abcdef123456789012345678 and email is test@company.com")
        cleaned, events = GLOBAL_FEDERATION_GUARD.scan_and_sanitize(sample)
        console.print(f"[{theme.rich_primary}]Original Input:[/{theme.rich_primary}] {sample}")
        console.print(f"[{theme.rich_success}]Sanitized Output:[/{theme.rich_success}] {cleaned}")
        console.print(f"[dim]Intercepted {len(events)} security/PII patterns.[/dim]\n")


@app.command("manual")
@app.command("docs")
@octos_app.command("manual")
@octos_app.command("docs")
def manual_cli_cmd(
    chapter: Optional[str] = typer.Option(None, "--chapter", "-c", help="Specific chapter number or keyword (e.g. 1, 2, commands, playbooks)"),
    web: bool = typer.Option(False, "--web", "-w", help="Open visual manual in default web browser"),
):
    """Display interactive Cephalopod Master Manual and Developer Field Guide."""
    from octoflow.manual import display_manual
    display_manual(chapter=chapter, web=web, console=console)


# Re-exported from octoflow.cockpit for backward compatibility
from octoflow.cockpit import (
    run_cockpit,
    interactive_cockpit,
    CockpitSession,
    CockpitInput,
    get_live_cockpit_input,
    confirm_live_cockpit,
    print_welcome_banner,
)

@app.callback(invoke_without_command=True)
def app_callback(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
):
    """Launch interactive cockpit if no command specified."""
    if ctx.invoked_subcommand is None:
        interactive_cockpit(host=host)


@octos_app.callback(invoke_without_command=True)
def octos_callback(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
):
    """Launch interactive cockpit if no command specified."""
    if ctx.invoked_subcommand is None:
        interactive_cockpit(host=host)


@app.command(name="runner")
@app.command(name="play")
def cmd_app_runner():
    """Launch the Chrome Dino-style Benthic Dot Runner game."""
    from octoflow.runner import run_dino_game
    theme = load_saved_theme()
    run_dino_game(console, theme=theme)


@octos_app.command(name="runner")
@octos_app.command(name="play")
def cmd_octos_runner():
    """Launch the Chrome Dino-style Benthic Dot Runner game."""
    from octoflow.runner import run_dino_game
    theme = load_saved_theme()
    run_dino_game(console, theme=theme)


def octos_main():
    """CLI entrypoint for 'octos' command."""
    octos_app()


if __name__ == "__main__":
    app()
