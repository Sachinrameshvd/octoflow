"""Run, Train, and Octos-Run CLI commands for deploying cephalopod swarms."""

import os
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from octoflow.commands.dashboard import render_consortium_dashboard, render_dashboard
from octoflow.config import OctoFlowConfig, SwarmMorphology
from octoflow.outcome import ProviderExhaustedError, RunOutcome
from octoflow.themes import get_theme

console = Console()


def run(
    objective: str = typer.Argument(
        ..., help="High-level engineering or research goal for the swarm"
    ),
    mode: str = typer.Option(
        "software_dev",
        "--mode",
        "-m",
        help="Swarm mode: 'software_dev', 'aiml_research', 'fullstack_ai'",
    ),
    guild: str | None = typer.Option(
        None, "--guild", "-g", help="Specialist roster/guild name from ~/.octoflow/guilds/"
    ),
    model: str = typer.Option(
        "mock", "--model", help="LLM backend: 'mock', 'anthropic', 'openai', 'ollama'"
    ),
    budget: float = typer.Option(5.00, "--budget", "-b", help="Hard spending limit in dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer telemetry port"),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"
    ),
    open_ui: bool = typer.Option(
        False, "--open-ui", "--ui", help="Auto-open 3D Connectome Visualizer in default browser"
    ),
    octos: str = typer.Option(
        "1",
        "--octos",
        "-o",
        help="Count of octopuses: 'auto' (dynamic load autoscaler), 1 (Solo), 3 (Triad), or 8 (Octopolis)",
    ),
    theme: str | None = typer.Option(
        None,
        "--theme",
        "-t",
        help="Theme palette ('abyssal', 'catppuccin', 'tokyo-night', 'dracula', 'cyberpunk', 'nord', 'gruvbox', 'minimalist')",
    ),
    sandbox: str = typer.Option(
        "local",
        "--sandbox",
        "-s",
        help="Execution isolation: 'local' (host) or 'docker' (containerized)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run with mock provider, write no project files"
    ),
    allow_dirty: bool = typer.Option(
        False,
        "--allow-dirty",
        help="Allow running in a git repo with uncommitted changes (snapshots changes via git stash create)",
    ),
    init_git: bool = typer.Option(
        False,
        "--init-git",
        help="Automatically initialize git repository if workspace is not in a git repo",
    ),
    no_checkpoint: bool = typer.Option(
        False, "--no-checkpoint", help="Disable git checkpointing and branch creation"
    ),
    open_app: bool = typer.Option(
        False, "--open", help="Open primary service URL in browser after ignition readiness"
    ),
    max_tokens: int | None = typer.Option(
        None, "--max-tokens", help="Maximum tokens allowed across run"
    ),
    max_calls: int | None = typer.Option(
        None, "--max-calls", help="Maximum LLM calls allowed across run"
    ),
    timeout: int | None = typer.Option(None, "--timeout", help="Maximum wall time in seconds"),
    max_heal: int | None = typer.Option(None, "--max-heal", help="Maximum healing iterations"),
    no_limits: bool = typer.Option(
        False, "--no-limits", help="Disable all execution budget limits"
    ),
):
    """Deploy the cephalopod swarm (1 to 8 octopuses • 8 to 64 arms) to execute an objective."""
    # Lazy imports of heavy components
    from octoflow.conductor import SupraesophagealConductor, SwarmTelemetryEvent
    from octoflow.consortium import (
        OctosConsortium,
        estimate_elastic_octopus_count,
        get_consortium_guilds,
    )
    from octoflow.ignition import ProjectIgniter
    from octoflow.server import TelemetryBroadcaster
    from octoflow.settings import load_settings

    loaded_settings = load_settings()
    run_budget = loaded_settings.budget.model_copy()

    if no_limits:
        console.print(
            "[bold yellow]▲ Warning: --no-limits enabled. Execution limits are disabled.[/bold yellow]"
        )
        run_budget.max_tokens = None
        run_budget.max_llm_calls = None
        run_budget.max_wall_seconds = None
        run_budget.max_heal_iterations = None
        run_budget.max_files_written = None
    else:
        if max_tokens is not None:
            run_budget.max_tokens = max_tokens
        if max_calls is not None:
            run_budget.max_llm_calls = max_calls
        if timeout is not None:
            run_budget.max_wall_seconds = timeout
        if max_heal is not None:
            run_budget.max_heal_iterations = max_heal

    dry_val = dry_run if isinstance(dry_run, bool) else False
    orig_dry = os.environ.get("OCTOFLOW_DRY_RUN")
    is_dry = dry_val or (orig_dry == "1")
    if is_dry:
        os.environ["OCTOFLOW_DRY_RUN"] = "1"
        if model in ["mock", "anthropic", "openai"]:
            model = "mock"
    else:
        force_live = os.getenv("OCTOFLOW_FORCE_LIVE") == "1"
        is_testing = not force_live and (
            ("PYTEST_CURRENT_TEST" in os.environ)
            or ("pytest" in sys.modules)
            or (os.getenv("OCTOFLOW_TESTING") == "1")
        )
        if model == "mock" and not is_testing:
            console.print(
                "\n✖ [bold red][FAILED] Mock LLM provider requested without --dry-run. Pass --dry-run or configure a real provider.[/bold red]\n"
            )
            raise typer.Exit(code=2)

    selected_guild = guild or (
        mode if mode not in ["software_dev", "aiml_research", "fullstack_ai"] else None
    )
    if not selected_guild and (mode == "software_dev" or not mode):
        from octoflow.consortium import detect_morphology_from_objective

        morphology_enum = detect_morphology_from_objective(objective)
    else:
        morphology_enum = (
            SwarmMorphology.CUSTOM if selected_guild else SwarmMorphology(mode.lower())
        )
    port_val = 8088 if not isinstance(port, int) else port
    active_theme = get_theme(theme)
    sandbox_str = sandbox if isinstance(sandbox, str) else "local"
    config = OctoFlowConfig(
        morphology=morphology_enum,
        guild=selected_guild,
        model_provider=model,
        max_budget_dollars=budget,
        budget=run_budget,
        workspace_dir=workspace,
        telemetry_port=port_val,
        sandbox_mode=sandbox_str,
        dry_run=is_dry,
    )

    checkpoint_meta = None
    finalized = False
    if not is_dry:
        from octoflow.checkpoint import finalize_run, preflight_and_start_run

        try:
            checkpoint_meta = preflight_and_start_run(
                workspace_dir=workspace,
                goal=objective,
                mode=mode,
                model=model,
                dry_run=is_dry,
                allow_dirty=allow_dirty,
                init_git=init_git,
                no_checkpoint=no_checkpoint,
            )
        except ValueError as ve:
            console.print(f"\n✖ [bold red][FAILED] Checkpoint pre-flight failed:[/bold red] {ve}\n")
            raise typer.Exit(code=2)
        except Exception as e:
            console.print(f"\n✖ [bold red][FAILED] Checkpoint error:[/bold red] {e}\n")
            raise typer.Exit(code=2)

    host_str = host if isinstance(host, str) else "127.0.0.1"
    if host_str not in ("127.0.0.1", "localhost"):
        console.print(
            f"[{active_theme.rich_warning}]▲ WARNING: Binding telemetry server to '{host_str}' exposes the swarm to the network![/{active_theme.rich_warning}]"
        )
    broadcaster = TelemetryBroadcaster(port=port_val, host=host_str)
    broadcaster.start_in_background()
    broadcaster.broadcast_raw(
        {
            "type": "THEME_CHANGE",
            "theme_id": active_theme.id,
            "tokens": asdict(active_theme),
        }
    )
    visualizer_url = f"http://{host}:{broadcaster.port}"

    # -------------------------------------------------------------------------
    # ELASTIC AUTOSCALING RESOLUTION
    # -------------------------------------------------------------------------
    if str(octos).lower() in ["auto", "0"]:
        resolved_octos, rationale = estimate_elastic_octopus_count(objective, model_provider=model)
        console.print(
            f"\n◈ [bold cyan]Elastic Autoscaler:[/bold cyan] {rationale} -> Provisioning [bold green]{resolved_octos} Octopuses[/bold green] ({resolved_octos * 8} Neural Arms)"
        )
    else:
        try:
            resolved_octos = int(octos)
        except ValueError:
            resolved_octos, rationale = estimate_elastic_octopus_count(
                objective, model_provider=model
            )
            console.print(
                f"\n◈ [bold cyan]Elastic Autoscaler:[/bold cyan] {rationale} -> Provisioning [bold green]{resolved_octos} Octopuses[/bold green] ({resolved_octos * 8} Neural Arms)"
            )

    # -------------------------------------------------------------------------
    # MULTI-OCTOPUS CONSORTIUM MODE (resolved_octos > 1)
    # -------------------------------------------------------------------------
    if resolved_octos > 1:
        tier_name = "OCTOPOLIS" if resolved_octos >= 8 else "TRIAD"
        total_arms = resolved_octos * 8
        console.print(
            f"\n[bold cyan]◈ Launching OctosFlow Consortium with {resolved_octos} Octopuses ({total_arms} Neural Arms)...[/bold cyan]"
        )
        console.print(
            f"● [bold green]Live 3D Brain Visualizer:[/bold green] [bold cyan underline]{visualizer_url}[/bold cyan underline]"
        )
        console.print(
            "   [dim]● Cmd+Click the link above to watch the multi-octopus connectome fire live in your browser![/dim]\n"
        )

        if open_ui:
            import webbrowser

            try:
                webbrowser.open(visualizer_url)
            except Exception:
                pass

        octopus_states = {}
        roster_pool = get_consortium_guilds(morphology_enum, 8)
        for g in roster_pool:
            is_active = g.octopus_id < resolved_octos
            color_tag = (
                "cyan"
                if "00F0FF" in g.color_hex
                else (
                    "magenta"
                    if "EC4899" in g.color_hex
                    else (
                        "yellow"
                        if "F59E0B" in g.color_hex
                        else ("green" if "10B981" in g.color_hex else "blue")
                    )
                )
            )
            octopus_states[g.octopus_id] = {
                "title": g.title,
                "color_hex": g.color_hex,
                "color_tag": color_tag,
                "status": "INITIALIZING" if is_active else "STANDBY",
                "action": "Starting up neural core..."
                if is_active
                else "Synaptic reserve (cross-coalitions)",
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
            consortium = OctosConsortium(
                config=config,
                octopus_count=resolved_octos,
                telemetry_callback=on_consortium_telemetry,
            )
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
                res = consortium.run_consortium(
                    objective=objective, cycles_per_octopus=4, open_browser=open_app
                )

            if is_dry:
                console.print(
                    "\n◈ [bold yellow][DRY-RUN: no project files written][/bold yellow]\n"
                )
                raise typer.Exit(code=0)

            if checkpoint_meta and not finalized:
                from octoflow.checkpoint import finalize_run

                finalize_run(checkpoint_meta, success=True, goal=objective)
                finalized = True

            console.print("\n[bold green]✔ OCTOSFLOW CONSORTIUM MISSION COMPLETE![/bold green]")
            console.print(
                f"◈ Deployed: [bold cyan]{resolved_octos} Octopuses ({total_arms} Neural Arms)[/bold cyan]"
            )
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

                console.print(
                    Panel(
                        live_text, title="⚡ OCTOSFLOW PHASE 4 LIVE IGNITION", border_style="cyan"
                    )
                )
            else:
                console.print(
                    f"● 3D Brain Telemetry: [bold cyan underline]{visualizer_url}[/bold cyan underline]\n"
                )

            raise typer.Exit(code=0)
        except ProviderExhaustedError as pe:
            if checkpoint_meta and not finalized:
                from octoflow.checkpoint import finalize_run

                finalize_run(checkpoint_meta, success=False, goal=objective)
                finalized = True
            console.print(f"\n✖ [bold red][FAILED] {pe}[/bold red]\n")
            raise typer.Exit(code=2)
        except typer.Exit:
            raise
        except KeyboardInterrupt:
            if checkpoint_meta and not finalized:
                from octoflow.checkpoint import finalize_run

                finalize_run(checkpoint_meta, success=False, goal=objective)
                finalized = True
            console.print(
                "\n[bold yellow]· Consortium paused by user (Ctrl+C). Generated files preserved.[/bold yellow]\n"
            )
            raise typer.Exit(code=1)
        except Exception as e:
            if checkpoint_meta and not finalized:
                from octoflow.checkpoint import finalize_run

                finalize_run(checkpoint_meta, success=False, goal=objective)
                finalized = True
            log_dir = Path.home() / ".octoflow"
            log_dir.mkdir(parents=True, exist_ok=True)
            crash_log = log_dir / "last_error.log"
            with open(crash_log, "w") as f:
                traceback.print_exc(file=f)
            error_panel = Panel(
                Text.from_markup(
                    f"[bold red]▲ Consortium Encountered an Interrupt:[/bold red] [yellow]{e}[/yellow]"
                ),
                border_style="red",
            )
            console.print(error_panel)
            raise typer.Exit(code=2)

    # -------------------------------------------------------------------------
    # SINGLE OCTOPUS MODE (octos == 1)
    # -------------------------------------------------------------------------
    console.print(f"\n[bold cyan]◈ Launching OctoFlow Swarm in {mode.upper()} mode...[/bold cyan]")
    console.print(
        f"● [bold green]Live 3D Brain Visualizer:[/bold green] [bold cyan underline]{visualizer_url}[/bold cyan underline]"
    )
    console.print(
        "   [dim]● Cmd+Click the link above to watch the neural connectome & 8 arms fire live in your browser![/dim]\n"
    )

    if open_ui:
        import webbrowser

        try:
            webbrowser.open(visualizer_url)
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
                if result.get("status") in [
                    "completed",
                    "GLOBAL_QUIESCENCE",
                    "QUIESCENCE",
                ] or result.get("success"):
                    outcome = RunOutcome.COMPLETE
                else:
                    outcome = RunOutcome.FAILED

        files = (
            getattr(result, "files_written", [])
            if not isinstance(result, dict)
            else result.get("files_written", [])
        )
        prov = (
            getattr(result, "provider_used", "live")
            if not isinstance(result, dict)
            else result.get("provider_used", "live")
        )
        mod = (
            getattr(result, "model", "default")
            if not isinstance(result, dict)
            else result.get("model", "default")
        )

        if outcome == RunOutcome.COMPLETE or str(outcome).lower() == "complete":
            if checkpoint_meta and not finalized:
                from octoflow.checkpoint import finalize_run

                finalize_run(checkpoint_meta, success=True, files_written=files, goal=objective)
                finalized = True
            console.print(
                f"\n◈ [bold green][LIVE: {prov}:{mod}] COMPLETE, {len(files)} files written[/bold green]"
            )
            for f in files:
                console.print(f"  • {f}")
            console.print(
                f"● Final Tokens Consumed: {conductor.total_tokens_used:,} (vs. ~{conductor.estimated_chatty_tokens:,} chatty baseline)"
            )
            console.print(f"● Token Savings: [bold green]{tokens_saved[0]:.1f}%[/bold green]")
            console.print(f"● Total API Cost: ${conductor.total_cost:.4f}\n")

            # Live Phase 4 Ignition
            try:
                igniter = ProjectIgniter(workspace_dir=workspace)
                ign_manifest = igniter.ignite(objective=objective, open_browser=open_app)
                if (
                    ign_manifest
                    and ign_manifest.status in ("RUNNING", "READY")
                    and ign_manifest.primary_url
                ):
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

                    console.print(
                        Panel(
                            live_text,
                            title="⚡ OCTOFLOW PHASE 4 LIVE IGNITION",
                            border_style="cyan",
                        )
                    )

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
            if checkpoint_meta and not finalized:
                from octoflow.checkpoint import finalize_run

                finalize_run(checkpoint_meta, success=False, files_written=files, goal=objective)
                finalized = True
            reason = (
                getattr(result, "reason", "partial quiescence")
                if not isinstance(result, dict)
                else result.get("reason", "partial quiescence")
            )
            budget_line = ""
            if hasattr(result, "extra") and isinstance(result.extra, dict):
                budget_line = result.extra.get("budget_line", "")
            elif (
                isinstance(result, dict) and "extra" in result and isinstance(result["extra"], dict)
            ):
                budget_line = result["extra"].get("budget_line", "")
            ribbon = f"\n◈ [bold yellow][PARTIAL] {reason}[/bold yellow]"
            if budget_line:
                ribbon += f" • [dim]{budget_line}[/dim]"
            ribbon += "\n"
            console.print(ribbon)
            raise typer.Exit(code=1)
        else:
            if checkpoint_meta and not finalized:
                from octoflow.checkpoint import finalize_run

                finalize_run(checkpoint_meta, success=False, files_written=files, goal=objective)
                finalized = True
            reason = getattr(result, "reason", "model produced no file changes")
            console.print(f"\n✖ [bold red][FAILED] {reason}[/bold red]\n")
            raise typer.Exit(code=2)

    except ProviderExhaustedError as pe:
        if checkpoint_meta and not finalized:
            from octoflow.checkpoint import finalize_run

            finalize_run(checkpoint_meta, success=False, goal=objective)
            finalized = True
        console.print(f"\n✖ [bold red][FAILED] {pe}[/bold red]\n")
        raise typer.Exit(code=2)
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        if checkpoint_meta and not finalized:
            from octoflow.checkpoint import finalize_run

            finalize_run(checkpoint_meta, success=False, goal=objective)
            finalized = True
        console.print(
            "\n[bold yellow]· Swarm execution paused by user (Ctrl+C). Generated files preserved.[/bold yellow]\n"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        if checkpoint_meta and not finalized:
            from octoflow.checkpoint import finalize_run

            finalize_run(checkpoint_meta, success=False, goal=objective)
            finalized = True
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
        if checkpoint_meta and not finalized:
            try:
                from octoflow.checkpoint import finalize_run

                finalize_run(checkpoint_meta, success=False, goal=objective)
                finalized = True
            except Exception:
                pass
        if orig_dry is None:
            os.environ.pop("OCTOFLOW_DRY_RUN", None)
        else:
            os.environ["OCTOFLOW_DRY_RUN"] = orig_dry


def train(
    objective: str = typer.Argument(..., help="Model architecture and training objective"),
    model: str = typer.Option("mock", "--model", help="LLM backend"),
    budget: float = typer.Option(5.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run with mock provider, write no project files"
    ),
):
    """Shortcut command to run swarm in AIML_RESEARCH morphology."""
    run(
        objective=objective,
        mode="aiml_research",
        model=model,
        budget=budget,
        workspace=workspace,
        port=8088,
        dry_run=dry_run,
    )


def octos_run(
    objective: str = typer.Argument(..., help="Engineering goal for the multi-octopus consortium"),
    octos: str = typer.Option(
        "auto",
        "--octos",
        "-o",
        help="Count of octopuses: 'auto' (dynamic load autoscaler), 3 (Triad), or 8 (Octopolis)",
    ),
    guild: str | None = typer.Option(
        None, "--guild", "-g", help="Specialist roster/guild name from ~/.octoflow/guilds/"
    ),
    model: str = typer.Option(
        "mock", "--model", help="LLM backend: 'mock', 'anthropic', 'openai', 'ollama'"
    ),
    budget: float = typer.Option(10.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer port"),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"
    ),
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open 3D Visualizer in browser"),
    theme: str | None = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run with mock provider, write no project files"
    ),
    allow_dirty: bool = typer.Option(
        False,
        "--allow-dirty",
        help="Allow running on dirty working tree by snapshotting changes via git stash create",
    ),
    init_git: bool = typer.Option(
        False, "--init-git", help="Automatically initialize git repository in non-git workspace"
    ),
    no_checkpoint: bool = typer.Option(
        False, "--no-checkpoint", help="Disable git checkpointing and branch creation"
    ),
    open_app: bool = typer.Option(
        False, "--open", help="Open primary service URL in browser after ignition readiness"
    ),
    max_tokens: int | None = typer.Option(
        None, "--max-tokens", help="Maximum tokens allowed across run"
    ),
    max_calls: int | None = typer.Option(
        None, "--max-calls", help="Maximum LLM calls allowed across run"
    ),
    timeout: int | None = typer.Option(None, "--timeout", help="Maximum wall time in seconds"),
    max_heal: int | None = typer.Option(None, "--max-heal", help="Maximum healing iterations"),
    no_limits: bool = typer.Option(
        False, "--no-limits", help="Disable all execution budget limits"
    ),
):
    """Deploy the multi-cephalopod consortium (3 to 8 octopuses • 24 to 64 arms) on a project."""
    run(
        objective=objective,
        mode="software_dev",
        guild=guild,
        model=model,
        budget=budget,
        workspace=workspace,
        port=port,
        host=host,
        open_ui=open_ui,
        octos=octos,
        theme=theme,
        dry_run=dry_run,
        allow_dirty=allow_dirty,
        init_git=init_git,
        no_checkpoint=no_checkpoint,
        open_app=open_app,
        max_tokens=max_tokens,
        max_calls=max_calls,
        timeout=timeout,
        max_heal=max_heal,
        no_limits=no_limits,
    )


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register run and train commands with Typer apps."""
    app.command()(run)
    app.command()(train)
    octos_app.command("run")(octos_run)
