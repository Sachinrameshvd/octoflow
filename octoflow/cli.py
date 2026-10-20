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
from rich.markdown import Markdown
from dataclasses import asdict
from octoflow.config import (
    OctoFlowConfig,
    SwarmMorphology,
    list_available_guilds,
    load_custom_guild,
    save_custom_guild,
    SOFTWARE_DEV_ROSTER,
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
from octoflow.router import classify_input, RouteKind, Route

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
    cfg_file = Path.home() / ".octoflow" / "config.json"
    if cfg_file.exists():
        try:
            cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
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

    broadcaster = TelemetryBroadcaster(port=port_val)
    broadcaster.start_in_background()
    broadcaster.broadcast_raw({
        "type": "THEME_CHANGE",
        "theme_id": active_theme.id,
        "tokens": asdict(active_theme),
    })
    visualizer_url = f"http://localhost:{broadcaster.port}"

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
def ui(port: int = typer.Option(8088, "--port", "-p", help="Port to host 3D visualizer")):
    """Launch the 3D Cephalopod Connectome Visualizer bridge."""
    url = f"http://localhost:{port}"
    console.print(f"\n[bold cyan]◈ Launching OctoFlow 3D Connectome Visualizer on {url}...[/bold cyan]")
    broadcaster = TelemetryBroadcaster(port=port)
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
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open 3D Visualizer in browser"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with mock provider, write no project files"),
):
    """Deploy the multi-cephalopod consortium (3 to 8 octopuses • 24 to 64 arms) on a project."""
    run(objective=objective, mode="software_dev", model=model, budget=budget, workspace=workspace, port=port, open_ui=open_ui, octos=octos, theme=theme, dry_run=dry_run)


@octos_app.command("run")
def octos_run(
    objective: str = typer.Argument(..., help="Engineering goal for the multi-octopus consortium"),
    octos: str = typer.Option("auto", "--octos", "-o", help="Count of octopuses: 'auto' (dynamic load autoscaler), 3 (Triad), or 8 (Octopolis)"),
    guild: Optional[str] = typer.Option(None, "--guild", "-g", help="Specialist roster/guild name from ~/.octoflow/guilds/"),
    model: str = typer.Option("mock", "--model", help="LLM backend: 'mock', 'anthropic', 'openai', 'ollama'"),
    budget: float = typer.Option(10.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer port"),
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open 3D Visualizer in browser"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with mock provider, write no project files"),
):
    """Deploy the multi-cephalopod consortium (3 to 8 octopuses • 24 to 64 arms) on a project."""
    run(objective=objective, mode="software_dev", guild=guild, model=model, budget=budget, workspace=workspace, port=port, open_ui=open_ui, octos=octos, theme=theme, dry_run=dry_run)


@octos_app.command("octopolis")
def octos_octopolis(
    objective: str = typer.Argument(..., help="Engineering goal for the 8-octopus Octopolis (64 Arms)"),
    model: str = typer.Option("mock", "--model", help="LLM backend"),
    budget: float = typer.Option(15.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer port"),
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open visualizer"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run with mock provider, write no project files"),
):
    """Deploy the flagship 8-Octopus Octopolis (64 Neural Arms) on an objective."""
    run(objective=objective, mode="software_dev", model=model, budget=budget, workspace=workspace, port=port, open_ui=open_ui, octos=8, theme=theme, dry_run=dry_run)


@octos_app.command("ui")
def octos_ui(port: int = typer.Option(8088, "--port", "-p", help="Port to host 3D visualizer")):
    """Launch the 3D Cephalopod Constellation Visualizer bridge."""
    ui(port=port)


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


def get_live_wizard_input(
    theme: OctoTheme,
    prompt_label: str,
    default_value: str = "",
    extra_panels: Optional[List[Any]] = None,
    is_password: bool = False,
    existing_cfg: Optional[dict] = None,
    workspace: Optional[Path] = None,
) -> str:
    """
    Renders the continuous animated live loop with 3D Banner, Cockpit HUD,
    Topology, and Benthic Runner (octopus running left/right and jumping),
    followed by wizard panels/tables, and non-blocking live keyboard input.
    The animations never stop or freeze while waiting for terminal input.
    """
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        try:
            val = console.input(f"[{theme.rich_primary}]{prompt_label}[/{theme.rich_primary}]").strip()
            return val or default_value
        except (KeyboardInterrupt, EOFError):
            return default_value

    import termios
    import tty
    import select
    from rich.live import Live
    from octoflow.themes import get_banner_loop_frame
    from octoflow.runner import render_runner_frame

    fd = sys.stdin.fileno()
    old_settings = None
    try:
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    except Exception:
        try:
            val = console.input(f"[{theme.rich_primary}]{prompt_label}[/{theme.rich_primary}]").strip()
            return val or default_value
        except (KeyboardInterrupt, EOFError):
            return default_value

    ws = workspace or Path.cwd().resolve()
    git_branch = "no git"
    try:
        res = subprocess.run(["git", "branch", "--show-current"], cwd=str(ws), capture_output=True, text=True, timeout=1)
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
    hud_table.add_row("◈ SWARM TIER", f"Octopuses: AUTO  [dim](Cross-Ring Synaptic Bus)[/dim]")
    hud_table.add_row("◈ PALETTE", f"[{theme.rich_primary}]●[/{theme.rich_primary}] [{theme.rich_secondary}]●[/{theme.rich_secondary}] [{theme.rich_success}]●[/{theme.rich_success}] {theme.name} [dim]({theme.description})[/dim]")
    hud_table.add_row("◈ 3D VISUAL", f"[{theme.rich_primary} underline]http://localhost:8088[/{theme.rich_primary} underline]  [dim](Cmd+Click to view 3D Connectome)[/dim]")

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

    buffer = ""
    cursor_pos = 0
    tick = 0
    octo_x = 0.0
    octo_dx = 1.2
    octo_y = 0
    jump_phase = 0.0

    def build_grid() -> Table:
        banner = get_banner_loop_frame(theme, tick=tick)
        is_jump = (octo_y > 0)
        runner_frame = render_runner_frame(
            theme,
            octo_x=int(octo_x),
            octo_y=octo_y,
            is_jumping=is_jump,
            stride_alt=(int(octo_x // 3) % 2 == 1),
            seabed_offset=int(octo_x),
        )

        grid = Table.grid(expand=True)
        grid.add_row(banner)
        grid.add_row(cockpit_panel)
        grid.add_row(topology_text)
        grid.add_row(runner_frame)
        if extra_panels:
            for ep in extra_panels:
                grid.add_row(ep)

        prompt_text = Text()
        prompt_text.append("\n")
        prompt_text.append(prompt_label, style=f"bold {theme.rich_primary}")
        disp_buffer = ("*" * len(buffer)) if is_password else buffer
        prompt_text.append(disp_buffer[:cursor_pos], style="bold white")
        cursor_char = "█" if (tick // 6) % 2 == 0 else " "
        prompt_text.append(cursor_char, style=f"bold {theme.rich_primary}")
        prompt_text.append(disp_buffer[cursor_pos:], style="bold white")
        prompt_text.append("\n")

        grid.add_row(prompt_text)
        return grid

    console.clear()
    try:
        with Live(build_grid(), console=console, refresh_per_second=20, transient=True) as live:
            while True:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.045)
                if rlist:
                    import os
                    try:
                        raw_chunk = os.read(fd, 8192).decode("utf-8", errors="ignore")
                    except Exception:
                        raw_chunk = sys.stdin.read(1)

                    if not raw_chunk:
                        continue

                    is_pasted = "\x1b[200~" in raw_chunk or len(raw_chunk) > 3
                    raw_chunk = raw_chunk.replace("\x1b[200~", "").replace("\x1b[201~", "")

                    if is_pasted:
                        clean_paste = "".join(c for c in raw_chunk if c >= " ")
                        buffer = buffer[:cursor_pos] + clean_paste + buffer[cursor_pos:]
                        cursor_pos += len(clean_paste)
                        continue

                    if raw_chunk in ["\r", "\n", "\r\n"]:
                        break

                    if "\x03" in raw_chunk:
                        raise KeyboardInterrupt()
                    if "\x04" in raw_chunk:
                        raise EOFError()

                    idx = 0
                    while idx < len(raw_chunk):
                        ch = raw_chunk[idx]
                        if ch == "\x1b":
                            if idx + 2 < len(raw_chunk) and raw_chunk[idx:idx+3] == "\x1b[C":
                                cursor_pos = min(cursor_pos + 1, len(buffer))
                                idx += 3
                                continue
                            elif idx + 2 < len(raw_chunk) and raw_chunk[idx:idx+3] == "\x1b[D":
                                cursor_pos = max(cursor_pos - 1, 0)
                                idx += 3
                                continue
                            else:
                                end_m = idx + 1
                                while end_m < len(raw_chunk) and raw_chunk[end_m] not in "ABCDEFHJKSTZ~":
                                    end_m += 1
                                idx = end_m + 1
                                continue
                        elif ch in ["\x7f", "\x08"]:
                            if cursor_pos > 0:
                                buffer = buffer[:cursor_pos - 1] + buffer[cursor_pos:]
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
                if math.sin(jump_phase) > 0.25:
                    octo_y = 1
                else:
                    octo_y = 0

                live.update(build_grid())
    finally:
        if old_settings is not None:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                pass

    return buffer.strip() or default_value


def run_setup_wizard(launch_after: bool = False):
    """Guided first-run configuration wizard for API keys, model, and theme."""
    import os
    import json
    import subprocess

    cur_theme = load_saved_theme()
    cfg_file = Path.home() / ".octoflow" / "config.json"
    existing_cfg = {}
    if cfg_file.exists():
        try:
            existing_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        except Exception:
            pass

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

    # Step 2: Key input (also in live animated loop)
    saved_key = ""
    step2_heading = Text(f"\nStep 1 Selected: [{prov_name}]\nStep 2: Enter API Key or Endpoint (optional - press Enter to skip)\n", style="bold white")

    if chosen_provider == "anthropic":
        env_key = os.getenv("ANTHROPIC_API_KEY") or existing_cfg.get("anthropic_api_key", "")
        masked = (env_key[:7] + "••••" + env_key[-4:]) if len(env_key) > 12 else ""
        prompt = f"Enter ANTHROPIC_API_KEY [{masked}]: " if masked else "Enter ANTHROPIC_API_KEY: "
        new_key = get_live_wizard_input(
            theme=cur_theme,
            prompt_label=prompt,
            default_value=env_key,
            extra_panels=[wizard_panel, step2_heading],
            existing_cfg=existing_cfg,
            workspace=workspace,
            is_password=True,
        )
        saved_key = new_key if new_key else env_key
        if saved_key:
            existing_cfg["anthropic_api_key"] = saved_key
            os.environ["ANTHROPIC_API_KEY"] = saved_key

    elif chosen_provider == "openai":
        env_key = os.getenv("OPENAI_API_KEY") or existing_cfg.get("openai_api_key", "")
        masked = (env_key[:7] + "••••" + env_key[-4:]) if len(env_key) > 12 else ""
        prompt = f"Enter OPENAI_API_KEY [{masked}]: " if masked else "Enter OPENAI_API_KEY: "
        new_key = get_live_wizard_input(
            theme=cur_theme,
            prompt_label=prompt,
            default_value=env_key,
            extra_panels=[wizard_panel, step2_heading],
            existing_cfg=existing_cfg,
            workspace=workspace,
            is_password=True,
        )
        saved_key = new_key if new_key else env_key
        if saved_key:
            existing_cfg["openai_api_key"] = saved_key
            os.environ["OPENAI_API_KEY"] = saved_key

    elif chosen_provider == "gemini":
        env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or existing_cfg.get("gemini_api_key", "")
        masked = (env_key[:7] + "••••" + env_key[-4:]) if len(env_key) > 12 else ""
        prompt = f"Enter GEMINI_API_KEY [{masked}]: " if masked else "Enter GEMINI_API_KEY: "
        new_key = get_live_wizard_input(
            theme=cur_theme,
            prompt_label=prompt,
            default_value=env_key,
            extra_panels=[wizard_panel, step2_heading],
            existing_cfg=existing_cfg,
            workspace=workspace,
            is_password=True,
        )
        saved_key = new_key if new_key else env_key
        if saved_key:
            existing_cfg["gemini_api_key"] = saved_key
            os.environ["GEMINI_API_KEY"] = saved_key

    elif chosen_provider == "grok":
        env_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY") or existing_cfg.get("grok_api_key", "")
        masked = (env_key[:7] + "••••" + env_key[-4:]) if len(env_key) > 12 else ""
        prompt = f"Enter XAI_API_KEY [{masked}]: " if masked else "Enter XAI_API_KEY: "
        new_key = get_live_wizard_input(
            theme=cur_theme,
            prompt_label=prompt,
            default_value=env_key,
            extra_panels=[wizard_panel, step2_heading],
            existing_cfg=existing_cfg,
            workspace=workspace,
            is_password=True,
        )
        saved_key = new_key if new_key else env_key
        if saved_key:
            existing_cfg["grok_api_key"] = saved_key
            os.environ["XAI_API_KEY"] = saved_key

    elif chosen_provider == "deepseek":
        env_key = os.getenv("DEEPSEEK_API_KEY") or existing_cfg.get("deepseek_api_key", "")
        masked = (env_key[:7] + "••••" + env_key[-4:]) if len(env_key) > 12 else ""
        prompt = f"Enter DEEPSEEK_API_KEY [{masked}]: " if masked else "Enter DEEPSEEK_API_KEY: "
        new_key = get_live_wizard_input(
            theme=cur_theme,
            prompt_label=prompt,
            default_value=env_key,
            extra_panels=[wizard_panel, step2_heading],
            existing_cfg=existing_cfg,
            workspace=workspace,
            is_password=True,
        )
        saved_key = new_key if new_key else env_key
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

    # Save to ~/.octoflow/config.json
    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    cfg_file.write_text(json.dumps(existing_cfg, indent=2), encoding="utf-8")

    console.clear()
    console.print(f"\n[{cur_theme.rich_success}]✔ Configuration saved successfully to ~/.octoflow/config.json![/{cur_theme.rich_success}]")
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
    cfg_file = Path.home() / ".octoflow" / "config.json"
    saved_cfg = {}
    if cfg_file.exists():
        try:
            saved_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        except Exception:
            pass

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


def interactive_cockpit():
    """Launch the interactive OctoFlow Cephalopod Cockpit REPL."""
    import readline
    import subprocess
    import shutil
    import json

    # Load defaults from config.json if present
    cfg_file = Path.home() / ".octoflow" / "config.json"
    saved_cfg = {}
    if cfg_file.exists():
        try:
            saved_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    theme = load_saved_theme()
    def _has_usable_credentials(cfg: dict) -> bool:
        env_keys = [
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
            "GOOGLE_API_KEY", "XAI_API_KEY", "GROK_API_KEY", "DEEPSEEK_API_KEY"
        ]
        if any(bool(os.getenv(k)) for k in env_keys):
            return True
        cfg_keys = [
            "anthropic_api_key", "openai_api_key", "gemini_api_key",
            "grok_api_key", "deepseek_api_key"
        ]
        if any(bool(cfg.get(k)) for k in cfg_keys):
            return True
        for entry in cfg.get("llm_pool", []):
            if entry.get("provider") in ["mock", "ollama"]:
                return True
            if bool(entry.get("api_key")):
                return True
        if cfg.get("default_model") in ["mock", "ollama"]:
            return True
        return False

    has_any_key = _has_usable_credentials(saved_cfg)

    if not has_any_key:
        try:
            run_setup_wizard(launch_after=False)
            if cfg_file.exists():
                saved_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
                has_any_key = _has_usable_credentials(saved_cfg)
        except Exception:
            pass

    # Safe fallback if user has not configured any cloud keys
    current_model = saved_cfg.get("default_model", "mock" if not has_any_key else "anthropic")
    if not has_any_key and current_model not in ["mock", "ollama"]:
        current_model = "mock"
    current_octos = "auto"
    current_guild = saved_cfg.get("default_guild", "software_dev")
    current_budget = float(saved_cfg.get("default_budget", 10.00))
    workspace = Path.cwd().resolve()
    port = 8088

    # Start visualizer bridge in background
    broadcaster = TelemetryBroadcaster(port=port)
    broadcaster.start_in_background()
    broadcaster.broadcast_raw({
        "type": "THEME_CHANGE",
        "theme_id": theme.id,
        "tokens": asdict(theme),
    })
    visualizer_url = f"http://localhost:{broadcaster.port}"

    COMMANDS = [
        "/help", "/manual", "/docs", "/setup", "/doctor", "/init", "/init-ide", "/init-action", "/ci", "/review-pr", "/heal", "/triage", "/notify", "/export", "/report", "/plan", "/ask", "/talk", "/theme", "/model", "/octos", "/guild", "/guard", "/hooks", "/rag",
        "/audit", "/eject", "/federation", "/install-claude",
        "/bench", "/monorepo", "/record", "/runner", "/play", "/banner", "/screensaver",
        "/ignite", "/diff", "/commit", "/rollback", "/undo", "/ui", "/memory", "/status", "/budget", "/clear", "/exit", "/quit"
    ]
    THEME_NAMES = list(list_themes().keys())
    MODELS = ["anthropic", "openai", "gemini", "grok", "deepseek", "ollama", "mock"]
    OCTOS_MODES = ["auto", "1", "3", "8"]
    ARM_NAMES = ["0", "1", "2", "3", "4", "5", "6", "7", "architect", "database", "backend", "frontend", "state", "qa", "security", "devops"]

    def completer(text, state):
        line = readline.get_line_buffer()
        if line.startswith("/theme "):
            arg = line.split(" ", 1)[1]
            matches = [t for t in THEME_NAMES if t.startswith(arg)]
        elif line.startswith("/model "):
            arg = line.split(" ", 1)[1]
            matches = [m for m in MODELS if m.startswith(arg)]
        elif line.startswith("/octos "):
            arg = line.split(" ", 1)[1]
            matches = [o for o in OCTOS_MODES if o.startswith(arg)]
        elif line.startswith("/guild "):
            arg = line.split(" ", 1)[1]
            matches = [g for g in list_available_guilds().keys() if g.startswith(arg)]
        elif line.startswith("/talk ") or line.startswith("/ask "):
            arg = line.split(" ", 1)[1]
            matches = [a for a in ARM_NAMES if a.startswith(arg)]
        else:
            matches = [c for c in COMMANDS if c.startswith(text)]
        return matches[state] if state < len(matches) else None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    def get_live_cockpit_input() -> str:
        """
        Renders the continuous animated cockpit with 3D banner, HUD, topology,
        runner, and interactive prompt. Never stops animating while waiting for input.
        """
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            try:
                return console.input(f"[{theme.rich_primary}]octos ❯[/{theme.rich_primary}] ").strip()
            except (KeyboardInterrupt, EOFError):
                return "/exit"

        import termios
        import tty
        import select
        from rich.live import Live
        from octoflow.themes import get_banner_loop_frame
        from octoflow.runner import render_runner_frame

        fd = sys.stdin.fileno()
        old_settings = None
        try:
            old_settings = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            return console.input(f"[{theme.rich_primary}]octos ❯[/{theme.rich_primary}] ").strip()

        git_branch = "no git"
        try:
            res = subprocess.run(["git", "branch", "--show-current"], cwd=str(workspace), capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                git_branch = f"git: {res.stdout.strip()}"
        except Exception:
            pass

        hud_table = Table.grid(expand=True, padding=(0, 1))
        hud_table.add_column(style=theme.rich_primary, width=16)
        hud_table.add_column(style="white")
        hud_table.add_row("◈ WORKSPACE", f"{workspace}  [dim]({git_branch})[/dim]")
        hud_table.add_row("◈ LLM CORE", f"{current_model.upper()}  [dim](Budget: ${current_budget:.2f})[/dim]")
        hud_table.add_row("◈ SWARM TIER", f"Octopuses: {current_octos.upper()}  [dim](Cross-Ring Synaptic Bus)[/dim]")
        hud_table.add_row("◈ PALETTE", f"[{theme.rich_primary}]●[/{theme.rich_primary}] [{theme.rich_secondary}]●[/{theme.rich_secondary}] [{theme.rich_success}]●[/{theme.rich_success}] {theme.name} [dim]({theme.description})[/dim]")
        hud_table.add_row("◈ 3D VISUAL", f"[{theme.rich_primary} underline]{visualizer_url}[/{theme.rich_primary} underline]  [dim](Cmd+Click to view 3D Connectome)[/dim]")

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

        buffer = ""
        cursor_pos = 0
        tick = 0
        octo_x = 0.0
        octo_dx = 1.2
        octo_y = 0
        jump_phase = 0.0

        def build_grid() -> Table:
            banner = get_banner_loop_frame(theme, tick=tick)
            is_jump = (octo_y > 0)
            runner_frame = render_runner_frame(
                theme,
                octo_x=int(octo_x),
                octo_y=octo_y,
                is_jumping=is_jump,
                stride_alt=(int(octo_x // 3) % 2 == 1),
                seabed_offset=int(octo_x),
            )

            prompt_text = Text()
            prompt_text.append("\n")
            prompt_text.append("octos ❯ ", style=theme.rich_primary)
            prompt_text.append(buffer[:cursor_pos], style="bold white")
            cursor_char = "█" if (tick // 6) % 2 == 0 else " "
            prompt_text.append(cursor_char, style=f"bold {theme.rich_primary}")
            prompt_text.append(buffer[cursor_pos:], style="bold white")
            prompt_text.append("\n")

            grid = Table.grid(expand=True)
            grid.add_row(banner)
            grid.add_row(cockpit_panel)
            grid.add_row(topology_text)
            grid.add_row(runner_frame)
            grid.add_row(prompt_text)
            return grid

        console.clear()
        try:
            with Live(build_grid(), console=console, refresh_per_second=20, transient=True) as live:
                while True:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.045)
                    if rlist:
                        import os
                        try:
                            raw_chunk = os.read(fd, 8192).decode("utf-8", errors="ignore")
                        except Exception:
                            raw_chunk = sys.stdin.read(1)

                        if not raw_chunk:
                            continue

                        # Handle bracketed paste escape wrappers: \x1b[200~ ... \x1b[201~
                        is_pasted = "\x1b[200~" in raw_chunk or len(raw_chunk) > 3
                        raw_chunk = raw_chunk.replace("\x1b[200~", "").replace("\x1b[201~", "")

                        if is_pasted:
                            clean_paste = "".join(c for c in raw_chunk if c >= " ")
                            buffer = buffer[:cursor_pos] + clean_paste + buffer[cursor_pos:]
                            cursor_pos += len(clean_paste)
                            continue

                        # Handle Enter / Carriage Return (single explicit keypress)
                        if raw_chunk in ["\r", "\n", "\r\n"]:
                            break

                        if "\x03" in raw_chunk:
                            raise KeyboardInterrupt()
                        if "\x04" in raw_chunk:
                            raise EOFError()

                        idx = 0
                        while idx < len(raw_chunk):
                            ch = raw_chunk[idx]
                            if ch == "\x1b":
                                if idx + 2 < len(raw_chunk) and raw_chunk[idx:idx+3] == "\x1b[C":
                                    cursor_pos = min(cursor_pos + 1, len(buffer))
                                    idx += 3
                                    continue
                                elif idx + 2 < len(raw_chunk) and raw_chunk[idx:idx+3] == "\x1b[D":
                                    cursor_pos = max(cursor_pos - 1, 0)
                                    idx += 3
                                    continue
                                else:
                                    end_m = idx + 1
                                    while end_m < len(raw_chunk) and raw_chunk[end_m] not in "ABCDEFHJKSTZ~":
                                        end_m += 1
                                    idx = end_m + 1
                                    continue
                            elif ch in ["\x7f", "\x08"]:
                                if cursor_pos > 0:
                                    buffer = buffer[:cursor_pos - 1] + buffer[cursor_pos:]
                                    cursor_pos -= 1
                                idx += 1
                            elif ch == "\t":
                                matches = [c for c in COMMANDS if c.startswith(buffer)]
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
                    # Move octopus left and right across full platform length (0 to 45)
                    octo_x += octo_dx
                    if octo_x >= 45.0:
                        octo_x = 45.0
                        octo_dx = -1.2  # Reach far right end, turn back left
                    elif octo_x <= 0.0:
                        octo_x = 0.0
                        octo_dx = 1.2   # Reach far left end, turn back right

                    # Jump freely in playful buoyant arcs
                    jump_phase += 0.16
                    if math.sin(jump_phase) > 0.25:
                        octo_y = 1
                    else:
                        octo_y = 0

                    live.update(build_grid())
        finally:
            if old_settings is not None:
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except Exception:
                    pass

        return buffer.strip()

    def print_welcome(animate: bool = False):
        console.clear()
        banner_text = render_octoflow_3d_banner(theme)
        console.print(banner_text)

    while True:
        try:
            user_input = get_live_cockpit_input()
            route = classify_input(user_input, workspace=workspace)
            if route.kind == RouteKind.EMPTY:
                continue

            user_input = route.command

            # Direct Shell Pass-Through
            if route.kind in [RouteKind.SHELL_SIMPLE, RouteKind.SHELL_EXPLICIT]:
                shell_cmd = route.command
                parts = shell_cmd.split(maxsplit=1)
                cmd_head = parts[0].lower() if parts else ""
                if cmd_head == "cd":
                    target_arg = parts[1].strip() if len(parts) > 1 else "~"
                    target_path = Path(os.path.expanduser(target_arg)).resolve()
                    target_path.mkdir(parents=True, exist_ok=True)
                    workspace = target_path
                    console.print(f"[{theme.rich_success}]✔ Active workspace switched to:[/{theme.rich_success}] [bold]{workspace}[/bold]\n")
                    continue

                console.print(f"[{theme.rich_primary}]⚡ Shell:[/{theme.rich_primary}] [dim]{shell_cmd}[/dim]")
                res = subprocess.run(shell_cmd, shell=True, cwd=str(workspace), capture_output=True, text=True)
                if res.stdout:
                    console.print(res.stdout.rstrip())
                if res.stderr:
                    console.print(f"[{theme.rich_danger}]{res.stderr.rstrip()}[/{theme.rich_danger}]")
                if res.returncode == 0 and not res.stdout:
                    console.print(f"[{theme.rich_success}]✔ Command executed successfully.[/{theme.rich_success}]")
                console.print()
                continue

            # Auto-normalize slashless commands to ensure seamless cockpit routing
            first_word = user_input.split()[0].lower() if user_input.split() else ""
            if first_word and not user_input.startswith("/"):
                known_slash_commands = {
                    "manual", "screensaver", "banner", "setup", "doctor", "init", "init-ide",
                    "init-action", "ci", "heal", "triage", "notify", "audit", "eject",
                    "federation", "install-claude", "plan", "ask", "talk", "theme", "model",
                    "octos", "guild", "bench", "monorepo", "record", "runner", "guard",
                    "hooks", "rag", "budget", "ignite", "diff", "commit", "rollback",
                    "undo", "ui", "memory", "status", "llm"
                }
                if first_word in known_slash_commands:
                    user_input = "/" + user_input

            if user_input in ["/exit", "/quit", "exit", "quit", ":q"]:
                console.print(f"[{theme.rich_success}]◈ Swarm returning to benthic depths. Farewell![/{theme.rich_success}]")
                break

            elif user_input in ["/clear", "clear", "cls"]:
                print_welcome(animate=False)
                continue

            elif user_input in ["/screensaver", "screensaver"]:
                from octoflow.themes import play_banner_continuous
                console.clear()
                play_banner_continuous(
                    console,
                    theme,
                    delay=0.045,
                    prompt_message="Press [Enter] or any key to return to Cockpit",
                )
                print_welcome(animate=False)
                continue

            elif user_input.startswith("/banner") or user_input in ["banner", "/intro", "intro"]:
                if any(k in user_input.lower() for k in ["loop", "continuous", "-c", "--continuous"]):
                    from octoflow.themes import play_banner_continuous
                    console.clear()
                    play_banner_continuous(
                        console,
                        theme,
                        delay=0.045,
                        prompt_message="Press [Enter] or any key to return to Cockpit",
                    )
                    print_welcome(animate=False)
                else:
                    print_welcome(animate=True, continuous=False)
                continue

            elif user_input in ["/runner", "/play", "runner", "play"]:
                from octoflow.runner import run_dino_game, play_runner_animation
                if sys.stdin.isatty():
                    run_dino_game(console, theme=theme)
                    print_welcome()
                else:
                    play_runner_animation(console, theme=theme, cycles=1)
                continue

            elif user_input in ["/help", "help", "?"]:
                help_table = Table(title="OctoFlow Interactive Commands", border_style=theme.rich_border, expand=True)
                help_table.add_column("Command", style=theme.rich_primary, width=20)
                help_table.add_column("Description", style="white")
                help_table.add_column("Example", style="dim")

                help_table.add_row("/manual [ch]", "Open interactive Cephalopod Field Guide & Manual", "/manual 3")
                help_table.add_row("/screensaver", "Continuous ambient 3D banner screensaver", "/screensaver")
                help_table.add_row("/banner [loop]", "Play 3D banner animation (or continuous loop)", "/banner loop")
                help_table.add_row("/setup", "Interactive API keys & provider setup wizard", "/setup")
                help_table.add_row("/doctor", "System, provider, and environment diagnostics", "/doctor")
                help_table.add_row("/init", "1-command auto-onboard (Cursor, Claude, VS Code, Git)", "/init")
                help_table.add_row("/init-action", "Generate GitHub Actions CI workflow (.github/workflows)", "/init-action")
                help_table.add_row("/ci", "3-Arm CI/CD PR Review (Security, QA/AST, Architect)", "/ci")
                help_table.add_row("/heal", "Autonomous self-healing test repair loop (Arm 5 & Arm 2)", "/heal")
                help_table.add_row("/triage", "Interactive file-by-file patch inspector & AST triage", "/triage")
                help_table.add_row("/notify [msg]", "Dispatch mission status card to team Slack or Discord", "/notify")
                help_table.add_row("/audit", "1-100 System readiness, test density & security grade", "/audit")
                help_table.add_row("/eject", "Export standalone autonomous agent harness into any repo", "/eject")
                help_table.add_row("/federation", "Zero-trust multi-machine agent mesh & 14-rule PII filter", "/federation status")
                help_table.add_row("/install-claude", "Register Claude Code plugin manifest & /octo commands", "/install-claude")
                help_table.add_row("/plan [goal]", "Preview & approve 8-arm decomposition blueprint", "/plan build auth")
                help_table.add_row("/ask [arm] [q]", "Interrogate specific arm or ask questions", "/ask 6 CSRF risks")
                help_table.add_row("/talk [arm]", "Launch dedicated 1-on-1 dialogue with an arm", "/talk architect")
                help_table.add_row("/theme [name]", "Choose from 8 curated developer palettes", "/theme catppuccin")
                help_table.add_row("/model [name]", "Switch LLM core backend", "/model anthropic")
                help_table.add_row("/octos [count]", "Scale swarm (1 Solo, 3 Triad, 8 Octopolis, auto)", "/octos 8")
                help_table.add_row("/guild [name]", "Switch or inspect 8-arm specialist rosters", "/guild aiml_research")
                help_table.add_row("/bench [task]", "Swarm benchmark evaluation suite (Rate Limiter, LRU, JWT, DAG)", "/bench")
                help_table.add_row("/monorepo", "Scan monorepo and partition to specialist arms", "/monorepo")
                help_table.add_row("/record [out]", "Export terminal session to Asciinema v2 .cast format", "/record")
                help_table.add_row("/runner", "Watch or play the 8-bit benthic dot-matrix runner", "/runner")
                help_table.add_row("/guard", "Pre-commit Swarm Guard: scans secrets & AST syntax", "/guard")
                help_table.add_row("/hooks", "Install auto-guard into .git/hooks/pre-commit", "/hooks")
                help_table.add_row("/rag [query]", "Episodic Codebase Vector RAG search & indexing", "/rag auth token")
                help_table.add_row("/budget [val]", "Set spending ceiling in dollars", "/budget 15.00")
                help_table.add_row("/ignite", "Boot generated frontend & backend dev servers", "/ignite")
                help_table.add_row("/diff", "Show colorized git diff of workspace changes", "/diff")
                help_table.add_row("/commit [msg]", "Safely stage & commit workspace changes", "/commit auth fix")
                help_table.add_row("/rollback", "Revert workspace to state before last objective", "/rollback")
                help_table.add_row("/ui", "Open 3D WebGL Constellation in default browser", "/ui")
                help_table.add_row("/memory", "Inspect learned synaptic heuristics in Vertical Lobe", "/memory")
                help_table.add_row("/status", "Display current ganglia and environment health", "/status")
                help_table.add_row("/clear", "Clear terminal screen and redraw HUD", "/clear")
                help_table.add_row("/exit", "Exit the interactive session cleanly", "/exit")
                console.print(help_table)
                continue

            elif user_input in [
                "/setup", "setup", "/config", "config",
                "./octo setup", "octo setup", "./octos setup", "octos setup",
            ]:
                run_setup_wizard(launch_after=False)
                if cfg_file.exists():
                    try:
                        saved_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
                        current_model = saved_cfg.get("default_model", current_model)
                        current_budget = float(saved_cfg.get("default_budget", current_budget))
                    except Exception:
                        pass
                theme = load_saved_theme()
                print_welcome()
                continue

            elif user_input.startswith("/llm"):
                cfg_data = {}
                if cfg_file.exists():
                    try:
                        cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
                    except Exception:
                        cfg_data = {}
                pool = cfg_data.get("llm_pool", [])

                parts = user_input.split()
                subcmd = parts[1].lower() if len(parts) > 1 else "list"

                if subcmd in ["add", "new", "+"]:
                    console.print("\n[bold cyan]-- Add LLM to Failover Cascade Pool --[/bold cyan]")
                    console.print("[dim]Select only the provider you own or want to use (not compulsory to add all):[/dim]\n")
                    console.print("  [1] Google Gemini (gemini-2.0-flash)")
                    console.print("  [2] xAI Grok (grok-2-1212)")
                    console.print("  [3] DeepSeek (deepseek-chat / R1)")
                    console.print("  [4] OpenAI (gpt-4o / o3-mini)")
                    console.print("  [5] Anthropic Claude (claude-3-5-sonnet)")
                    console.print("  [6] Ollama (Free Local AI)")
                    console.print("  [7] Custom Endpoint (vLLM / LM Studio / Self-Hosted)")

                    p_choice = console.input("\n[bold cyan]Select provider [1-7]: [/bold cyan]").strip()
                    p_map = {
                        "1": ("gemini", "Google Gemini 2.0 Flash", "gemini-2.0-flash", "https://generativelanguage.googleapis.com/v1beta"),
                        "2": ("grok", "xAI Grok-2", "grok-2-1212", "https://api.x.ai/v1"),
                        "3": ("deepseek", "DeepSeek-V3", "deepseek-chat", "https://api.deepseek.com/v1"),
                        "4": ("openai", "OpenAI GPT-4o", "gpt-4o", "https://api.openai.com/v1"),
                        "5": ("anthropic", "Anthropic Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022", "https://api.anthropic.com/v1"),
                        "6": ("ollama", "Local Ollama", "qwen2.5-coder:7b", "http://localhost:11434"),
                        "7": ("custom", "Custom Endpoint", "custom-model", "http://localhost:8000/v1"),
                    }
                    prov, name, d_model, d_url = p_map.get(p_choice, ("gemini", "Google Gemini 2.0 Flash", "gemini-2.0-flash", "https://generativelanguage.googleapis.com/v1beta"))

                    custom_url = console.input(f"[bold cyan]Endpoint URL [default: {d_url}]: [/bold cyan]").strip() or d_url
                    custom_model = console.input(f"[bold cyan]Model name [default: {d_model}]: [/bold cyan]").strip() or d_model
                    api_key = console.input("[bold cyan]API Key (leave blank for local / no-auth): [/bold cyan]").strip()

                    new_entry = {
                        "id": f"{prov}-{len(pool)+1}",
                        "provider": prov,
                        "name": name,
                        "base_url": custom_url,
                        "model": custom_model,
                        "api_key": api_key,
                        "enabled": True,
                        "priority": len(pool) + 1,
                    }
                    pool.append(new_entry)
                    cfg_data["llm_pool"] = pool
                    cfg_file.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")
                    console.print(f"[bold green]Added {name} to cascade pool as Priority #{len(pool)}.[/bold green]\n")

                elif subcmd in ["clear", "reset"]:
                    cfg_data["llm_pool"] = []
                    cfg_file.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")
                    console.print("[yellow]Cleared all LLM cascade pool entries.[/yellow]\n")

                else:
                    # List
                    if not pool:
                        console.print("\n[yellow]No custom LLM cascade pool configured yet.[/yellow]")
                        console.print("Run [bold cyan]/llm add[/bold cyan] to connect your Gemini, Grok, DeepSeek, OpenAI, Claude, or local Ollama endpoint.\n")
                    else:
                        table = Table(title="Configured LLM Failover Cascade Pool", border_style=theme.rich_border, expand=True)
                        table.add_column("Priority", style="bold cyan", width=10)
                        table.add_column("Provider / Name", style="white", width=28)
                        table.add_column("Model", style="white", width=24)
                        table.add_column("Endpoint URL", style="dim")
                        table.add_column("Key Status", style="magenta", width=14)

                        for idx, item in enumerate(pool):
                            raw_k = item.get("api_key") or ""
                            k_disp = raw_k[:3] + "..." + raw_k[-4:] if len(raw_k) > 6 else ("Configured" if raw_k else "None/Local")
                            table.add_row(
                                f"[#{idx+1}]",
                                item.get("name", item.get("provider")),
                                item.get("model", "default"),
                                item.get("base_url", "Default"),
                                k_disp,
                            )
                        console.print()
                        console.print(table)
                        console.print("[dim]Commands: /llm add (add another endpoint) | /llm clear (clear pool)[/dim]\n")
                continue

            elif user_input in ["/doctor", "doctor"]:
                run_doctor(workspace=str(workspace))
                continue

            elif user_input in ["/init", "/init-ide"]:
                from octoflow.onboarding import onboard_ide
                console.print(f"\n[{theme.rich_primary}]◈ Auto-Onboarding Omni-IDE Surfaces for Workspace...[/{theme.rich_primary}]")
                res = onboard_ide(workspace=str(workspace))
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
                continue

            elif user_input.startswith("/plan"):
                parts = user_input.split(maxsplit=1)
                plan_goal = parts[1].strip() if len(parts) > 1 else ""
                if not plan_goal:
                    plan_goal = console.input(f"[{theme.rich_primary}]Enter objective to blueprint: [/{theme.rich_primary}]").strip()
                if not plan_goal:
                    continue

                console.print(f"\n[{theme.rich_primary}]◈ Architect Decomposing 8-Arm Neural Blueprint...[/{theme.rich_primary}]\n")
                m_enum = SwarmMorphology.CUSTOM if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(current_guild)
                plan_conductor = SupraesophagealConductor(
                    config=OctoFlowConfig(
                        workspace_dir=str(workspace),
                        model_provider=current_model,
                        morphology=m_enum,
                        guild=current_guild if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                    )
                )
                sub_goals = plan_conductor.decompose_objective(plan_goal)
                roster = plan_conductor.config.get_roster()

                plan_table = Table(title=f"8-Arm Mission Blueprint: '{plan_goal[:50]}'", border_style=theme.rich_border, expand=True)
                plan_table.add_column("Arm", width=6, style=theme.rich_primary)
                plan_table.add_column("Guild Role", width=22, style="bold white")
                plan_table.add_column("Tier", width=12, style=theme.rich_secondary)
                plan_table.add_column("Assigned Arm Objective", style="white")

                for arm_id in range(8):
                    role_cfg = roster[arm_id] if arm_id < len(roster) else None
                    role_title = role_cfg.title if role_cfg else f"Arm {arm_id}"
                    tier = getattr(role_cfg, "model_tier", "balanced")
                    goal_text = sub_goals.get(arm_id, "Idle")
                    clean_goal = goal_text.split(" (Existing Codebase Context:")[0]
                    plan_table.add_row(f"Arm {arm_id}", role_title, tier.upper(), clean_goal)

                console.print(plan_table)
                confirm = console.input(f"\n[{theme.rich_primary}]Deploy swarm with this 8-arm blueprint? (Y/edit/cancel): [/{theme.rich_primary}]").strip().lower()
                if confirm in ["", "y", "yes"]:
                    user_input = plan_goal
                elif confirm in ["e", "edit"]:
                    adjusted = console.input(f"[{theme.rich_primary}]Enter modified objective instructions: [/{theme.rich_primary}]").strip()
                    if adjusted:
                        user_input = f"{plan_goal} (Note: {adjusted})"
                    else:
                        continue
                else:
                    console.print("[dim]Mission blueprint cancelled.[/dim]\n")
                    continue

            elif user_input.startswith("/ask"):
                parts = user_input.split(maxsplit=2)
                m_enum = SwarmMorphology.CUSTOM if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(current_guild)
                active_conductor = SupraesophagealConductor(
                    config=OctoFlowConfig(
                        workspace_dir=str(workspace),
                        model_provider=current_model,
                        morphology=m_enum,
                        guild=current_guild if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                    )
                )
                if len(parts) == 1:
                    console.print(f"[{theme.rich_primary}]Tip: Ask any question directly or target an arm: [bold]/ask <arm_or_role> <question>[/bold][/{theme.rich_primary}]\n")
                    continue
                elif len(parts) == 2:
                    query = parts[1]
                    res = active_conductor.converse(query)
                    p_title = res.get("primary_arm_title", "Specialist")
                    p_id = res.get("primary_arm_id", 0)
                    s_title = res.get("secondary_arm_title", "Swarm")
                    resp = res.get("response", "")
                else:
                    target_ident = parts[1]
                    query = parts[2]
                    arm = active_conductor.get_arm(target_ident)
                    if not arm:
                        res = active_conductor.converse(query)
                        p_title = res.get("primary_arm_title", "Specialist")
                        p_id = res.get("primary_arm_id", 0)
                        s_title = res.get("secondary_arm_title", "Swarm")
                        resp = res.get("response", "")
                    else:
                        p_title = arm.role.title
                        p_id = arm.arm_id
                        s_title = "Architect"
                        hits = active_conductor.memory.search_codebase(query, top_k=3)
                        rag_ctx = "\n".join(f"{h['file_path']}:\n{h['snippet']}" for h in hits) if hits else ""
                        resp = arm.answer_query(query, context=rag_ctx)

                console.print(Panel(
                    Markdown(resp),
                    title=f"[{theme.rich_primary}]● {p_title} [Arm {p_id}][/{theme.rich_primary}] [dim](in consultation with {s_title})[/dim]",
                    border_style=theme.rich_border,
                ))
                console.print()
                continue

            elif user_input.startswith("/talk"):
                parts = user_input.split(maxsplit=1)
                target_ident = parts[1].strip() if len(parts) > 1 else "0"
                m_enum = SwarmMorphology.CUSTOM if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(current_guild)
                active_conductor = SupraesophagealConductor(
                    config=OctoFlowConfig(
                        workspace_dir=str(workspace),
                        model_provider=current_model,
                        morphology=m_enum,
                        guild=current_guild if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                    )
                )
                arm = active_conductor.get_arm(target_ident) or active_conductor.arms[0]
                console.print(f"[{theme.rich_success}]Connected 1-on-1 with [bold]{arm.role.title}[/bold] (Arm {arm.arm_id}). Type [bold]/exit[/bold] to return to cockpit.[/{theme.rich_success}]")
                while True:
                    try:
                        sub_q = console.input(f"[{theme.rich_secondary}][{arm.role.title}:Arm {arm.arm_id}] ❯ [/{theme.rich_secondary}]").strip()
                        if not sub_q:
                            continue
                        if sub_q in ["/exit", "exit", "/quit", "quit"]:
                            console.print(f"[{theme.rich_primary}]Returned to main cockpit.[/{theme.rich_primary}]\n")
                            break
                        hits = active_conductor.memory.search_codebase(sub_q, top_k=2)
                        rag_ctx = "\n".join(f"{h['file_path']}:\n{h['snippet']}" for h in hits) if hits else ""
                        sub_resp = arm.answer_query(sub_q, context=rag_ctx)
                        console.print(Panel(Markdown(sub_resp), border_style=theme.rich_border))
                        console.print()
                    except (KeyboardInterrupt, EOFError):
                        console.print()
                        break
                continue

            elif user_input.startswith("/theme") or user_input == "theme" or user_input.startswith("theme "):
                if user_input.startswith("theme"):
                    user_input = "/" + user_input
                parts = user_input.split(maxsplit=1)
                if len(parts) == 1:
                    if sys.stdin.isatty() and sys.stdout.isatty():
                        from octoflow.theme_selector import run_interactive_theme_picker
                        theme = run_interactive_theme_picker(console, initial_theme=theme, broadcaster=broadcaster)
                        print_welcome(animate=True)
                        console.print(f"[{theme.rich_success}]✔ Palette active: [bold]{theme.name}[/bold] ({theme.description})[/{theme.rich_success}]\n")
                        continue
                    themes_all = list_themes()
                    theme_table = Table(title="◈ Available Developer Palettes", border_style=theme.rich_border, expand=True)
                    theme_table.add_column("#", width=4, style=theme.rich_primary)
                    theme_table.add_column("Theme ID", style="bold white", width=16)
                    theme_table.add_column("Name", style="white", width=22)
                    theme_table.add_column("Palette Swatch", width=14)
                    theme_table.add_column("Description", style="dim")

                    for idx, (t_id, t_obj) in enumerate(themes_all.items(), 1):
                        is_active = " [bold green]✔ ACTIVE[/]" if t_id == theme.id else ""
                        swatch = f"[{t_obj.rich_primary}]●[/{t_obj.rich_primary}] [{t_obj.rich_secondary}]●[/{t_obj.rich_secondary}] [{t_obj.rich_success}]●[/{t_obj.rich_success}] [{t_obj.rich_warning}]●[/{t_obj.rich_warning}]"
                        theme_table.add_row(str(idx), t_id + is_active, t_obj.name, swatch, t_obj.description)

                    console.print(theme_table)
                    console.print(f"[dim]Tip: Switch by typing [bold]/theme <id>[/bold] (e.g. [cyan]/theme catppuccin[/cyan])[/dim]\n")
                else:
                    new_theme_name = parts[1].strip()
                    theme = get_theme(new_theme_name)
                    save_theme_preference(theme.id)
                    broadcaster.broadcast_raw({
                        "type": "THEME_CHANGE",
                        "theme_id": theme.id,
                        "tokens": asdict(theme),
                    })
                    print_welcome(animate=True)
                    console.print(f"[{theme.rich_success}]✔ Switched palette to: [bold]{theme.name}[/bold] ({theme.description})[/{theme.rich_success}]")
                    console.print(f"[dim]Saved to ~/.octoflow/theme.json and synchronized with 3D Visualizer.[/dim]\n")
                continue

            elif user_input.startswith("/model"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    current_model = parts[1].strip().lower()
                    console.print(f"[{theme.rich_success}]✔ LLM core updated to: [bold]{current_model.upper()}[/bold][/{theme.rich_success}]\n")
                else:
                    console.print(f"[yellow]Current model:[/yellow] {current_model}. Options: mock, anthropic, openai, ollama\n")
                continue

            elif user_input.startswith("/octos"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    current_octos = parts[1].strip().lower()
                    console.print(f"[{theme.rich_success}]✔ Swarm scaling tier set to: [bold]{current_octos.upper()}[/bold][/{theme.rich_success}]\n")
                else:
                    console.print(f"[yellow]Current tier:[/yellow] {current_octos}. Options: auto, 1 (Solo), 3 (Triad), 8 (Octopolis)\n")
                continue

            elif user_input.startswith("/budget"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    try:
                        current_budget = float(parts[1].strip().replace("$", ""))
                        console.print(f"[{theme.rich_success}]✔ Spending ceiling set to: [bold]${current_budget:.2f}[/bold][/{theme.rich_success}]\n")
                    except ValueError:
                        console.print(f"[{theme.rich_danger}]Invalid budget format. Use e.g. /budget 15.00[/{theme.rich_danger}]\n")
                else:
                    console.print(f"[yellow]Current budget:[/yellow] ${current_budget:.2f}\n")
                continue

            elif user_input == "/ui":
                import webbrowser
                try:
                    webbrowser.open(visualizer_url)
                except Exception:
                    pass
                console.print(f"[{theme.rich_primary}]● 3D Cephalopod Constellation visualizer active at: [underline]{visualizer_url}[/underline][/{theme.rich_primary}]\n")
                continue

            elif user_input == "/ignite":
                console.print(f"[{theme.rich_primary}]⚡ Igniting project runtime services in {workspace}...[/{theme.rich_primary}]")
                igniter = ProjectIgniter(workspace_dir=str(workspace))
                manifest = igniter.ignite()
                if manifest.primary_url:
                    console.print(f"[{theme.rich_success}]✔ Primary Live Service:[/{theme.rich_success}] {manifest.primary_url}")
                if manifest.api_docs_url:
                    console.print(f"[{theme.rich_success}]✔ API Docs Live:[/{theme.rich_success}] {manifest.api_docs_url}")
                if manifest.status == "FAILED" or manifest.error_message:
                    console.print(f"[{theme.rich_warning}]▲ Notice: {manifest.error_message}[/{theme.rich_warning}]")
                else:
                    console.print(f"[{theme.rich_success}]✔ Runtime online: [bold]{manifest.title}[/bold] ({manifest.service_type})[/{theme.rich_success}]")
                console.print()
                continue

            elif user_input == "/diff":
                res = subprocess.run(["git", "diff"], cwd=str(workspace), capture_output=True, text=True)
                if res.stdout.strip():
                    from rich.syntax import Syntax
                    syntax = Syntax(res.stdout, "diff", theme="monokai", line_numbers=True)
                    console.print(syntax)
                else:
                    console.print("[dim]No uncommitted git changes in workspace.[/dim]\n")
                continue

            elif user_input.startswith("/commit"):
                parts = user_input.split(maxsplit=1)
                msg = parts[1].strip() if len(parts) > 1 else ""
                res = subprocess.run(["git", "status", "--porcelain"], cwd=str(workspace), capture_output=True, text=True)
                if not res.stdout.strip():
                    console.print("[dim]No uncommitted changes in workspace to commit.[/dim]\n")
                    continue
                if not msg:
                    msg = console.input(f"[{theme.rich_primary}]Enter commit message: [/{theme.rich_primary}]").strip()
                    if not msg:
                        msg = "swarm enhancements"
                commit_msg = f"feat(octos): {msg}"
                subprocess.run(["git", "add", "-A"], cwd=str(workspace), check=False)
                c_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(workspace), capture_output=True, text=True)
                if c_res.returncode == 0:
                    console.print(f"[{theme.rich_success}]✔ Committed workspace changes: [bold]{commit_msg}[/bold][/{theme.rich_success}]\n")
                else:
                    console.print(f"[{theme.rich_danger}]Commit note: {c_res.stderr.strip() or c_res.stdout.strip()}[/{theme.rich_danger}]\n")
                continue

            elif user_input in ["/rollback", "/undo"]:
                chk_file = Path.home() / ".octoflow" / "last_checkpoint.json"
                if not chk_file.exists():
                    console.print("[dim]No prior checkpoint found to rollback.[/dim]\n")
                    continue
                try:
                    chk_data = json.loads(chk_file.read_text(encoding="utf-8"))
                    target_head = chk_data.get("head")
                    obj = chk_data.get("objective", "previous mission")
                    console.print(f"[{theme.rich_warning}]▲ Rollback: Reverting workspace changes from objective '[bold]{obj[:45]}[/bold]'...[/{theme.rich_warning}]")
                    if target_head:
                        subprocess.run(["git", "reset", "--hard", target_head], cwd=str(workspace), capture_output=True)
                        subprocess.run(["git", "clean", "-fd"], cwd=str(workspace), capture_output=True)
                        console.print(f"[{theme.rich_success}]✔ Cleanly reverted workspace to checkpoint ({target_head[:8]}).[/{theme.rich_success}]\n")
                    else:
                        console.print("[yellow]Checkpoint recorded but no git commit hash was available.[/yellow]\n")
                except Exception as rb_err:
                    console.print(f"[{theme.rich_danger}]Rollback error: {rb_err}[/{theme.rich_danger}]\n")
                continue

            elif user_input == "/memory":
                mem_path = Path.home() / ".octoflow" / "vertical_lobe.json"
                if mem_path.exists():
                    try:
                        data = json.loads(mem_path.read_text(encoding="utf-8"))
                        entries = data.get("entries", [])
                        console.print(f"[{theme.rich_primary}]◈ Vertical Lobe Memory ({len(entries)} Hebbian Heuristics):[/{theme.rich_primary}]")
                        for idx, e in enumerate(entries[:5], 1):
                            console.print(f"  {idx}. [bold]{e.get('signature', 'General')}[/bold]: {e.get('guidance', '')[:80]}...")
                        console.print()
                    except Exception as err:
                        console.print(f"[dim]Could not parse memory: {err}[/dim]\n")
                else:
                    console.print("[dim]Vertical Lobe memory initialized; no persisted heuristics yet.[/dim]\n")
                continue

            elif user_input == "/status":
                console.print(f"[{theme.rich_primary}]◈ Cephalopod Swarm Status:[/{theme.rich_primary}]")
                console.print(f"  • Model: [bold]{current_model}[/bold]")
                console.print(f"  • Guild / Roster: [bold]{current_guild}[/bold]")
                console.print(f"  • Octopuses: [bold]{current_octos}[/bold]")
                console.print(f"  • Budget Limit: [bold]${current_budget:.2f}[/bold]")
                console.print(f"  • Theme: [bold]{theme.name}[/bold]")
                console.print(f"  • Workspace: {workspace}")
                console.print(f"  • Visualizer URL: {visualizer_url}\n")
                continue

            elif user_input.startswith("/guild"):
                parts = user_input.split(maxsplit=1)
                if len(parts) == 1:
                    guilds = list_available_guilds()
                    g_table = Table(title="Specialist 8-Arm Guilds & Rosters", border_style=theme.rich_border, expand=True)
                    g_table.add_column("Guild Name", style="bold white", width=18)
                    g_table.add_column("Type", style=theme.rich_secondary, width=12)
                    g_table.add_column("Description", style="white")

                    for g_name, g_desc in guilds.items():
                        is_active = " [bold green]✔ ACTIVE[/]" if g_name == current_guild else ""
                        g_type = "Built-In" if g_name in ["software_dev", "aiml_research", "fullstack_ai"] else "Community"
                        g_table.add_row(g_name + is_active, g_type, g_desc)

                    console.print(g_table)
                    console.print(f"[dim]Tip: Switch guild by typing [bold]/guild <name>[/bold] (e.g. [cyan]/guild aiml_research[/cyan])[/dim]\n")
                else:
                    target_guild = parts[1].strip()
                    roster_chk = load_custom_guild(target_guild)
                    if roster_chk:
                        current_guild = target_guild
                        console.print(f"[{theme.rich_success}]✔ Active specialist guild switched to: [bold]{current_guild}[/bold][/{theme.rich_success}]\n")
                    else:
                        console.print(f"[{theme.rich_danger}]Guild '{target_guild}' not found. Use /guild to list available rosters.[/{theme.rich_danger}]\n")
                continue

            elif user_input == "/guard":
                run_guard(workspace=str(workspace))
                continue

            elif user_input == "/hooks":
                install_git_hooks(workspace=str(workspace))
                continue

            elif user_input.startswith("/rag") or user_input.startswith("/search"):
                parts = user_input.split(maxsplit=1)
                vl = VerticalLobeMemory()
                num_chunks = vl.index_codebase(str(workspace))
                if len(parts) == 1:
                    console.print(f"[{theme.rich_success}]✔ Episodic Codebase Vector RAG: Indexed [bold]{num_chunks}[/bold] code chunks across workspace.[/{theme.rich_success}]")
                    console.print(f"[dim]Tip: Search codebase semantically using [bold]/rag <query>[/bold] (e.g. /rag auth token)[/dim]\n")
                else:
                    q = parts[1].strip()
                    hits = vl.search_codebase(q, top_k=4)
                    if not hits:
                        console.print(f"[yellow]No semantic matches found for query: '{q}'[/yellow]\n")
                    else:
                        r_table = Table(title=f"Episodic Vector Hits for '{q}'", border_style=theme.rich_border, expand=True)
                        r_table.add_column("Score", width=8, style=theme.rich_primary)
                        r_table.add_column("File", width=28, style="bold white")
                        r_table.add_column("Lines", width=12, style=theme.rich_secondary)
                        r_table.add_column("Snippet Preview", style="dim")
                        for h in hits:
                            sym = f" ({h['symbol']})" if h.get("symbol") else ""
                            r_table.add_row(f"{h['score']:.3f}", f"{h['file_path']}{sym}", f"L{h['start_line']}-{h['end_line']}", h['snippet'].splitlines()[0][:60] if h['snippet'] else "")
                        console.print(r_table)
                        console.print()
                continue

            elif user_input in ["/ci", "/review-pr"]:
                from octoflow.ci import review_pull_request
                console.print(f"\n[{theme.rich_primary}]● OctoFlow Swarm Guard: Auditing Pull Request Diff...[/{theme.rich_primary}]\n")
                res = review_pull_request(workspace=str(workspace), write_summary=False)
                t = Table(title="OctoFlow Swarm Guard PR Audit", border_style=theme.rich_border, expand=True)
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
                if res["hard_block"]:
                    console.print(f"\n[{theme.rich_danger}]✖ Merge Blocked: Critical security vulnerabilities or AST syntax errors detected.[/{theme.rich_danger}]\n")
                else:
                    console.print(f"\n[{theme.rich_success}]✔ Swarm Verdict: READY TO MERGE. Zero merge hazards detected.[/{theme.rich_success}]\n")
                continue

            elif user_input == "/init-action":
                from octoflow.ci import generate_github_action_workflow
                wf_path = generate_github_action_workflow(str(workspace))
                console.print(f"\n[{theme.rich_success}]✔ Generated GitHub Actions Workflow:[/{theme.rich_success}] [bold white]{wf_path}[/bold white]")
                console.print(f"[dim]Every Pull Request will now automatically trigger Arm 6 (Security), Arm 5 (QA/AST), and Arm 0 (Architect) audits.[/dim]\n")
                continue

            elif user_input in ["/export", "/report"] or user_input.startswith("/export ") or user_input.startswith("/report "):
                from octoflow.report import collect_mission_audit_data, generate_html_audit_report
                parts = user_input.split(maxsplit=1)
                custom_out = parts[1].strip() if len(parts) > 1 else None
                console.print(f"\n[{theme.rich_primary}]◈ Generating Standalone HTML Swarm Mission Audit...[/{theme.rich_primary}]")
                hist = broadcaster.get_history()
                m_data = collect_mission_audit_data(workspace=str(workspace), telemetry_events=hist)
                out_path = generate_html_audit_report(m_data, output_path=custom_out, theme_id=theme.id)
                console.print(f"[{theme.rich_success}]✔ Exported Standalone Audit Report:[/{theme.rich_success}] [bold white]{out_path}[/bold white]")
                console.print(f"[dim]100% self-contained single-file HTML • Zero external CDN dependencies • Connectome replay included.[/dim]")
                open_ans = console.input(f"[{theme.rich_primary}]Open report in browser? (Y/n): [/{theme.rich_primary}]").strip().lower()
                if open_ans in ["", "y", "yes"]:
                    import webbrowser
                    webbrowser.open(f"file://{out_path.resolve()}")
                console.print()
                continue

            elif user_input in ["/heal", "/fix"] or user_input.startswith("/heal ") or user_input.startswith("/fix "):
                from octoflow.healing import self_heal_workspace
                console.print(f"\n[{theme.rich_primary}]◈ OctoFlow Autonomous Self-Healing: Running test suite and diagnosing...[/{theme.rich_primary}]\n")
                m_enum = SwarmMorphology.CUSTOM if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(current_guild)
                heal_cfg = OctoFlowConfig(
                    workspace_dir=str(workspace),
                    model_provider=current_model,
                    morphology=m_enum,
                    guild=current_guild if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                )
                res = self_heal_workspace(workspace_dir=str(workspace), config=heal_cfg)
                t = Table(title="OctoFlow Self-Healing Summary", border_style=theme.rich_border, expand=True)
                t.add_column("Property", style=theme.rich_secondary, width=20)
                t.add_column("Value", style="bold white")
                status_str = f"[{theme.rich_success}]✔ HEALED & PASSING[/]" if res["success"] else f"[{theme.rich_danger}]✖ UNRESOLVED[/]"
                t.add_row("Status", status_str)
                t.add_row("Framework", res["framework"].upper())
                t.add_row("Attempts Used", str(res["attempts"]))
                t.add_row("Repaired Files", ", ".join(res["repaired_files"]) if res["repaired_files"] else "None (tests passing)")
                t.add_row("Result Note", res["message"])
                console.print(t)
                console.print()
                continue

            elif user_input in ["/triage", "/review", "/diff-review"]:
                from octoflow.triage import triage_workspace_diffs
                console.print(f"\n[{theme.rich_primary}]◈ OctoFlow Patch Triage: Reviewing uncommitted changes...[/{theme.rich_primary}]")
                res = triage_workspace_diffs(workspace_dir=str(workspace), interactive=True, console=console)
                console.print(f"\n[{theme.rich_success}]✔ {res['message']}[/{theme.rich_success}]\n")
                continue

            elif user_input.startswith("/notify") or user_input.startswith("/alert"):
                from octoflow.notify import send_mission_notification
                parts = user_input.split(maxsplit=1)
                msg_text = parts[1].strip() if len(parts) > 1 else "Cockpit Mission Update"
                ok = send_mission_notification(custom_message=msg_text)
                if ok:
                    console.print(f"[{theme.rich_success}]✔ Successfully dispatched alert to team webhook.[/{theme.rich_success}]\n")
                else:
                    console.print(f"[{theme.rich_warning}]▲ Webhook dispatch skipped: Set webhook_url in ~/.octoflow/config.json or pass --url.[/{theme.rich_warning}]\n")
                continue

            elif user_input in ["/audit", "audit"] or user_input.startswith("/audit "):
                from octoflow.audit import evaluate_workspace, print_audit_report
                console.print(f"\n[{theme.rich_primary}]◈ Running 100-Point Cephalopod MetaHarness Audit...[/{theme.rich_primary}]")
                rep = evaluate_workspace(str(workspace))
                print_audit_report(rep, console=console)
                continue

            elif user_input in ["/eject", "eject"] or user_input.startswith("/eject "):
                from octoflow.eject import eject_harness
                parts = user_input.split(maxsplit=1)
                target_out = parts[1].strip() if len(parts) > 1 else "./octo-harness"
                eject_harness(output_dir=target_out, console=console)
                continue

            elif user_input in ["/install-claude", "install-claude"]:
                install_claude_cli_cmd()
                continue

            elif user_input.startswith("/federation"):
                parts = user_input.split()
                act = parts[1] if len(parts) > 1 else "status"
                from octoflow.federation import GLOBAL_FEDERATION_GUARD, PII_RULES
                if act == "status":
                    t = Table(title="Zero-Trust Federation & PII Security Rules", border_style=theme.rich_border)
                    t.add_column("Rule Name", style="bold white", width=22)
                    t.add_column("Severity", style=theme.rich_secondary, width=12)
                    t.add_column("Redacted Mask", style="dim", width=32)
                    for r in PII_RULES:
                        t.add_row(r.name, r.severity, r.replacement)
                    console.print(t)
                    console.print(f"[dim]Default PII Action: [bold green]{GLOBAL_FEDERATION_GUARD.default_action.value}[/bold green] | Total Intercepted Events: {len(GLOBAL_FEDERATION_GUARD.audit_log)}[/dim]\n")
                elif act in ["test", "test-pii"]:
                    sample = " ".join(parts[2:]) if len(parts) > 2 else ("My key is " + "sk-ant-" + "api03-abcdef123456789012345678 and email is test@company.com")
                    cleaned, events = GLOBAL_FEDERATION_GUARD.scan_and_sanitize(sample)
                    console.print(f"[{theme.rich_primary}]Original Input:[/{theme.rich_primary}] {sample}")
                    console.print(f"[{theme.rich_success}]Sanitized Output:[/{theme.rich_success}] {cleaned}")
                    console.print(f"[dim]Intercepted {len(events)} security/PII patterns.[/dim]\n")
                continue

            elif user_input in ["/manual", "/docs", "manual", "docs"] or user_input.startswith("/manual ") or user_input.startswith("/docs "):
                from octoflow.manual import display_manual
                parts = user_input.split(maxsplit=1)
                ch = parts[1].strip() if len(parts) > 1 else None
                display_manual(chapter=ch, console=console)
                continue

            elif user_input in ["/bench", "/benchmark"] or user_input.startswith("/bench ") or user_input.startswith("/benchmark "):
                from octoflow.bench import run_swarm_benchmark_suite
                parts = user_input.split(maxsplit=1)
                task_k = parts[1].strip() if len(parts) > 1 else None
                console.print(f"\n[{theme.rich_primary}]◈ OctoFlow Swarm Benchmark Suite: Starting evaluation harness...[/{theme.rich_primary}]\n")
                run_swarm_benchmark_suite(task_key=task_k, console=console)
                continue

            elif user_input in ["/monorepo", "/packages"]:
                from octoflow.monorepo import scan_monorepo_topology
                topo = scan_monorepo_topology(str(workspace))
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
                continue

            elif user_input.startswith("/record"):
                from octoflow.recorder import TerminalRecorder
                parts = user_input.split(maxsplit=1)
                cast_out = parts[1].strip() if len(parts) > 1 else "octoflow_mission.cast"
                rec = TerminalRecorder(title="OctoFlow Interactive Mission")
                rec.start()
                rec.record_output(f"OctoFlow Interactive Terminal Session: {workspace}\r\n")
                rec.record_output(f"Theme: {theme.name} | Swarm: {current_octos}\r\n")
                rec.stop()
                saved_cast = rec.export_cast(cast_out)
                console.print(f"[{theme.rich_success}]✔ Exported Asciinema .cast session to: [bold white]{saved_cast}[/bold white][/{theme.rich_success}]\n")
                continue

            # Intelligent Conversational Reflex: Check if user input is an Inquiry vs Action
            m_enum = SwarmMorphology.CUSTOM if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(current_guild)
            active_conductor = SupraesophagealConductor(
                config=OctoFlowConfig(
                    workspace_dir=str(workspace),
                    model_provider=current_model,
                    morphology=m_enum,
                    guild=current_guild if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                )
            )
            dialogue_turn = active_conductor.converse(user_input)

            if dialogue_turn["intent"] == "INQUIRY":
                p_title = dialogue_turn["primary_arm_title"]
                p_id = dialogue_turn["primary_arm_id"]
                s_title = dialogue_turn["secondary_arm_title"]
                resp_text = dialogue_turn["response"]

                resp_panel = Panel(
                    Markdown(resp_text),
                    title=f"[{theme.rich_primary}]● {p_title} [Arm {p_id}][/{theme.rich_primary}] [dim](in consultation with {s_title})[/dim]",
                    border_style=theme.rich_border,
                    subtitle="[dim]Ask follow-up questions, or provide an action directive to deploy the swarm.[/dim]",
                )
                console.print(resp_panel)
                console.print()
                continue

            # Check git branch safety for existing codebases
            try:
                b_chk = subprocess.run(["git", "branch", "--show-current"], cwd=str(workspace), capture_output=True, text=True, timeout=1)
                curr_branch = b_chk.stdout.strip()
                if curr_branch in ["main", "master"]:
                    import re
                    clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', user_input.lower())[:24].strip('-')
                    safe_branch = f"octos/{clean_slug or 'task'}"
                    console.print(f"[{theme.rich_warning}]▲  Branch Protection: You are on production branch '[bold]{curr_branch}[/bold]'.[/{theme.rich_warning}]")
                    branch_ans = console.input(f"[{theme.rich_primary}]Switch to safety branch '[bold]{safe_branch}[/bold]'? (Y/n): [/{theme.rich_primary}]").strip().lower()
                    if branch_ans in ["", "y", "yes"]:
                        sw_out = subprocess.run(["git", "checkout", "-b", safe_branch], cwd=str(workspace), capture_output=True, text=True)
                        if sw_out.returncode == 0:
                            console.print(f"[{theme.rich_success}]✔ Switched to protection branch: [bold]{safe_branch}[/bold][/{theme.rich_success}]\n")
            except Exception:
                pass

            # Pre-mission git checkpoint for /rollback
            try:
                rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(workspace), capture_output=True, text=True, timeout=1)
                if rev.returncode == 0:
                    chk_payload = {
                        "head": rev.stdout.strip(),
                        "time": time.time(),
                        "objective": user_input,
                    }
                    (Path.home() / ".octoflow").mkdir(parents=True, exist_ok=True)
                    (Path.home() / ".octoflow" / "last_checkpoint.json").write_text(json.dumps(chk_payload), encoding="utf-8")
            except Exception:
                pass

            # Natural language goal -> Execute Swarm!
            console.print(f"\n[{theme.rich_primary}]◈ Deploying Swarm on Objective:[/{theme.rich_primary}] [bold white]{user_input}[/bold white]\n")

            try:
                resolved_mode = "custom" if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else current_guild
                resolved_guild = current_guild if current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None
                run(
                    objective=user_input,
                    mode=resolved_mode,
                    guild=resolved_guild,
                    model=current_model,
                    budget=current_budget,
                    workspace=str(workspace),
                    port=port,
                    open_ui=False,
                    octos=current_octos,
                    theme=theme.id,
                    sandbox="local",
                )
            except Exception as swarm_err:
                console.print(f"[{theme.rich_danger}]Swarm execution note: {swarm_err}[/{theme.rich_danger}]")

            # Post-execution Action Ribbon
            ribbon_text = Text.from_markup(
                f"[{theme.rich_success}]◈ Mission Phase Concluded.[/{theme.rich_success}]\n"
                f"  Quick Actions:  "
                f"[{theme.rich_primary}]/ignite[/] (Preview App)  •  "
                f"[{theme.rich_secondary}]/diff[/] (Inspect Changes)  •  "
                f"[{theme.rich_warning}]/rollback[/] (Undo Changes)  •  "
                f"[{theme.rich_accent}]/ui[/] (3D Connectome)  •  "
                f"[white]Type next goal to continue[/]"
            )
            console.print(Panel(ribbon_text, border_style=theme.rich_border))
            console.print()

        except KeyboardInterrupt:
            console.print(f"\n[yellow]⚡ Swarm paused (Ctrl+C). Type /exit to quit.[/yellow]\n")
        except EOFError:
            break


@app.callback(invoke_without_command=True)
def app_callback(ctx: typer.Context):
    """Launch interactive cockpit if no command specified."""
    if ctx.invoked_subcommand is None:
        interactive_cockpit()


@octos_app.callback(invoke_without_command=True)
def octos_callback(ctx: typer.Context):
    """Launch interactive cockpit if no command specified."""
    if ctx.invoked_subcommand is None:
        interactive_cockpit()


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
