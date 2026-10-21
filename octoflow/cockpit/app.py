"""Interactive OctoFlow Cephalopod Cockpit Main REPL Application.

Coordinates the main terminal loop:
- Command classification via octoflow.router
- Direct shell pass-through and in-process cd navigation
- Non-blocking confirmation prompts
- Live frame rendering and benthic runner updates
- Swarm goal decomposition, conversation, and execution
"""

import getpass
import json
import math
import os
import readline
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from octoflow.cockpit.input import CockpitInput, get_live_cockpit_keys, get_live_cockpit_input
from octoflow.cockpit.render import (
    build_cockpit_grid,
    build_confirm_grid,
    print_welcome_banner,
)
from octoflow.cockpit.session import CockpitSession
from octoflow.cockpit.shell import confirm_live_cockpit, execute_cockpit_shell
from octoflow.config import (
    OctoFlowConfig,
    SwarmMorphology,
    get_octoflow_dir,
    list_available_guilds,
    load_custom_guild,
    load_secure_config,
    mask_credential,
    save_secure_config,
)
from octoflow.router import (
    Route,
    RouteKind,
    classify_input as route_classifier,
    execute_shell_route,
    log_command_history,
)
from octoflow.themes import (
    get_theme,
    list_themes,
    load_saved_theme,
    render_octoflow_3d_banner,
    save_theme_preference,
)


def prompt_user_str(console: Console, prompt_text: str = "") -> str:
    """Prompt user and read line using sys.stdin.readline without blocking read calls."""
    if prompt_text:
        console.print(prompt_text, end="")
    try:
        raw = sys.stdin.readline()
        return raw.strip() if raw else ""
    except (KeyboardInterrupt, EOFError):
        return ""


def has_usable_credentials(cfg: dict) -> bool:
    """Check environment variables and secure config for usable LLM credentials."""
    env_keys = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "XAI_API_KEY",
        "GROK_API_KEY",
        "DEEPSEEK_API_KEY",
    ]
    if any(bool(os.getenv(k)) for k in env_keys):
        return True
    cfg_keys = [
        "anthropic_api_key",
        "openai_api_key",
        "gemini_api_key",
        "grok_api_key",
        "deepseek_api_key",
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


def run_cockpit(
    host: str = "127.0.0.1",
    port: int = 8088,
    session: Optional[CockpitSession] = None,
    console: Optional[Console] = None,
) -> None:
    """Launch the interactive OctoFlow Cephalopod Cockpit REPL."""
    c = console or Console()
    cfg_file = get_octoflow_dir() / "config.json"
    saved_cfg = load_secure_config(cfg_file) if cfg_file.exists() else {}

    s = session or CockpitSession(host=host, port=port)
    s.theme = load_saved_theme()

    has_any_key = has_usable_credentials(saved_cfg)
    if not has_any_key:
        try:
            from octoflow.cli import run_setup_wizard

            run_setup_wizard(launch_after=False)
            if cfg_file.exists():
                saved_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
                has_any_key = has_usable_credentials(saved_cfg)
        except Exception:
            pass

    # Safe fallback if user has not configured any cloud keys
    s.current_model = saved_cfg.get("default_model", "mock" if not has_any_key else "anthropic")
    if not has_any_key and s.current_model not in ["mock", "ollama"]:
        s.current_model = "mock"
    s.current_octos = "auto"
    s.current_guild = saved_cfg.get("default_guild", "software_dev")
    s.current_budget = float(saved_cfg.get("default_budget", 10.00))
    s.workspace = Path.cwd().resolve()
    s.previous_workspace = s.workspace

    # Start visualizer bridge in background
    from octoflow.server import TelemetryBroadcaster
    broadcaster = TelemetryBroadcaster(port=s.port, host=s.host)
    broadcaster.start_in_background()
    broadcaster.broadcast_raw({
        "type": "THEME_CHANGE",
        "theme_id": s.theme.id,
        "tokens": asdict(s.theme),
    })
    s.broadcaster = broadcaster
    s.visualizer_url = f"http://localhost:{broadcaster.port}"

    COMMANDS = [
        "/help", "/manual", "/docs", "/setup", "/doctor", "/init", "/init-ide",
        "/init-action", "/ci", "/review-pr", "/heal", "/triage", "/notify",
        "/export", "/report", "/plan", "/ask", "/talk", "/theme", "/model",
        "/octos", "/guild", "/guard", "/hooks", "/rag", "/audit", "/eject",
        "/federation", "/install-claude", "/bench", "/monorepo", "/record",
        "/runner", "/play", "/banner", "/screensaver", "/ignite", "/diff",
        "/commit", "/rollback", "/undo", "/ui", "/memory", "/status",
        "/budget", "/clear", "/exit", "/quit",
    ]
    THEME_NAMES = list(list_themes().keys())
    MODELS = ["anthropic", "openai", "gemini", "grok", "deepseek", "ollama", "mock"]
    OCTOS_MODES = ["auto", "1", "3", "8"]
    ARM_NAMES = [
        "0", "1", "2", "3", "4", "5", "6", "7", "architect", "database",
        "backend", "frontend", "state", "qa", "security", "devops",
    ]

    def completer(text, state):
        try:
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
                matches = [cmd for cmd in COMMANDS if cmd.startswith(text)]
            return matches[state] if state < len(matches) else None
        except Exception:
            return None

    try:
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
    except Exception:
        pass

    while s.running:
        try:
            raw_input_obj = get_live_cockpit_keys(
                session=s,
                console=c,
                commands=COMMANDS,
            )
            paste_count = getattr(raw_input_obj, "paste_line_count", 1)
            route = route_classifier(
                str(raw_input_obj),
                workspace=s.workspace,
                paste_line_count=paste_count,
            )
            if route.kind == RouteKind.EMPTY:
                continue

            # Non-blocking confirmation gate for destructive or explicit commands
            if route.needs_confirmation:
                confirmed = confirm_live_cockpit(route, session=s, console=c)
                if not confirmed:
                    c.print(f"[{s.theme.rich_danger}]✖ Execution aborted by user.[/{s.theme.rich_danger}]\n")
                    continue

            user_input = route.command

            # Direct Shell Pass-Through
            if route.kind in [RouteKind.SHELL_SIMPLE, RouteKind.SHELL_EXPLICIT]:
                execute_cockpit_shell(route, session=s, console=c)
                continue

            # Auto-normalize slashless commands to ensure seamless cockpit routing
            first_word = user_input.split()[0].lower() if user_input.split() else ""
            if first_word and not user_input.startswith("/"):
                known_slash_commands = {
                    "manual", "screensaver", "banner", "setup", "doctor", "init",
                    "init-ide", "init-action", "ci", "heal", "triage", "notify",
                    "audit", "eject", "federation", "install-claude", "plan",
                    "ask", "talk", "theme", "model", "octos", "guild", "bench",
                    "monorepo", "record", "runner", "guard", "hooks", "rag",
                    "budget", "ignite", "diff", "commit", "rollback", "undo",
                    "ui", "memory", "status", "llm",
                }
                if first_word in known_slash_commands:
                    user_input = "/" + user_input

            if user_input in ["/exit", "/quit", "exit", "quit", ":q"]:
                c.print(f"[{s.theme.rich_success}]◈ Swarm returning to benthic depths. Farewell![/{s.theme.rich_success}]")
                s.running = False
                break

            elif user_input in ["/clear", "clear", "cls"]:
                print_welcome_banner(s, c, animate=False)
                continue

            elif user_input in ["/screensaver", "screensaver"]:
                from octoflow.themes import play_banner_continuous

                c.clear()
                play_banner_continuous(
                    c,
                    s.theme,
                    delay=0.045,
                    prompt_message="Press [Enter] or any key to return to Cockpit",
                )
                print_welcome_banner(s, c, animate=False)
                continue

            elif user_input.startswith("/banner") or user_input in ["banner", "/intro", "intro"]:
                if any(k in user_input.lower() for k in ["loop", "continuous", "-c", "--continuous"]):
                    from octoflow.themes import play_banner_continuous

                    c.clear()
                    play_banner_continuous(
                        c,
                        s.theme,
                        delay=0.045,
                        prompt_message="Press [Enter] or any key to return to Cockpit",
                    )
                    print_welcome_banner(s, c, animate=False)
                else:
                    print_welcome_banner(s, c, animate=True)
                continue

            elif user_input in ["/runner", "/play", "runner", "play"]:
                from octoflow.runner import play_runner_animation, run_dino_game

                if sys.stdin.isatty():
                    run_dino_game(c, theme=s.theme)
                    print_welcome_banner(s, c, animate=False)
                else:
                    play_runner_animation(c, theme=s.theme, cycles=1)
                continue

            elif user_input in ["/help", "help", "?"]:
                help_table = Table(title="OctoFlow Interactive Commands", border_style=s.theme.rich_border, expand=True)
                help_table.add_column("Command", style=s.theme.rich_primary, width=20)
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
                c.print(help_table)
                continue

            elif user_input in [
                "/setup", "setup", "/config", "config",
                "./octo setup", "octo setup", "./octos setup", "octos setup",
            ]:
                from octoflow.cli import run_setup_wizard

                run_setup_wizard(launch_after=False)
                if cfg_file.exists():
                    try:
                        saved_cfg = load_secure_config(cfg_file)
                        s.current_model = saved_cfg.get("default_model", s.current_model)
                        s.current_budget = float(saved_cfg.get("default_budget", s.current_budget))
                    except Exception:
                        pass
                s.theme = load_saved_theme()
                print_welcome_banner(s, c, animate=False)
                continue

            elif user_input.startswith("/llm"):
                cfg_data = {}
                if cfg_file.exists():
                    try:
                        cfg_data = load_secure_config(cfg_file)
                    except Exception:
                        cfg_data = {}
                pool = cfg_data.get("llm_pool", [])

                parts = user_input.split()
                subcmd = parts[1].lower() if len(parts) > 1 else "list"

                if subcmd in ["add", "new", "+"]:
                    c.print("\n[bold cyan]-- Add LLM to Failover Cascade Pool --[/bold cyan]")
                    c.print("[dim]Select only the provider you own or want to use (not compulsory to add all):[/dim]\n")
                    c.print("  [1] Google Gemini (gemini-2.0-flash)")
                    c.print("  [2] xAI Grok (grok-2-1212)")
                    c.print("  [3] DeepSeek (deepseek-chat / R1)")
                    c.print("  [4] OpenAI (gpt-4o / o3-mini)")
                    c.print("  [5] Anthropic Claude (claude-3-5-sonnet)")
                    c.print("  [6] Ollama (Free Local AI)")
                    c.print("  [7] Custom Endpoint (vLLM / LM Studio / Self-Hosted)")

                    p_choice = prompt_user_str(c, "\n[bold cyan]Select provider [1-7]: [/bold cyan]")
                    p_map = {
                        "1": ("gemini", "Google Gemini 2.0 Flash", "gemini-2.0-flash", "https://generativelanguage.googleapis.com/v1beta"),
                        "2": ("grok", "xAI Grok-2", "grok-2-1212", "https://api.x.ai/v1"),
                        "3": ("deepseek", "DeepSeek-V3", "deepseek-chat", "https://api.deepseek.com/v1"),
                        "4": ("openai", "OpenAI GPT-4o", "gpt-4o", "https://api.openai.com/v1"),
                        "5": ("anthropic", "Anthropic Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022", "https://api.anthropic.com/v1"),
                        "6": ("ollama", "Local Ollama", "qwen2.5-coder:7b", "http://localhost:11434"),
                        "7": ("custom", "Custom Endpoint", "custom-model", "http://localhost:8000/v1"),
                    }
                    prov, name, d_model, d_url = p_map.get(
                        p_choice,
                        ("gemini", "Google Gemini 2.0 Flash", "gemini-2.0-flash", "https://generativelanguage.googleapis.com/v1beta"),
                    )

                    custom_url = prompt_user_str(c, f"[bold cyan]Endpoint URL [default: {d_url}]: [/bold cyan]") or d_url
                    custom_model = prompt_user_str(c, f"[bold cyan]Model name [default: {d_model}]: [/bold cyan]") or d_model
                    try:
                        api_key = getpass.getpass("API Key (leave blank for local / no-auth): ").strip()
                    except Exception:
                        api_key = prompt_user_str(c, "[bold cyan]API Key (leave blank for local / no-auth): [/bold cyan]")

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
                    save_secure_config(cfg_data, cfg_file)
                    c.print(f"[bold green]Added {name} to cascade pool as Priority #{len(pool)}.[/bold green]\n")

                elif subcmd in ["clear", "reset"]:
                    cfg_data["llm_pool"] = []
                    save_secure_config(cfg_data, cfg_file)
                    c.print("[yellow]Cleared all LLM cascade pool entries.[/yellow]\n")

                else:
                    if not pool:
                        c.print("\n[yellow]No custom LLM cascade pool configured yet.[/yellow]")
                        c.print("Run [bold cyan]/llm add[/bold cyan] to connect your Gemini, Grok, DeepSeek, OpenAI, Claude, or local Ollama endpoint.\n")
                    else:
                        table = Table(title="Configured LLM Failover Cascade Pool", border_style=s.theme.rich_border, expand=True)
                        table.add_column("Priority", style="bold cyan", width=10)
                        table.add_column("Provider / Name", style="white", width=28)
                        table.add_column("Model", style="white", width=24)
                        table.add_column("Endpoint URL", style="dim")
                        table.add_column("Key Status", style="magenta", width=14)

                        for idx, item in enumerate(pool):
                            raw_k = item.get("api_key") or ""
                            k_disp = mask_credential(raw_k) if raw_k else "None/Local"
                            table.add_row(
                                f"[#{idx+1}]",
                                item.get("name", item.get("provider")),
                                item.get("model", "default"),
                                item.get("base_url", "Default"),
                                k_disp,
                            )
                        c.print()
                        c.print(table)
                        c.print("[dim]Commands: /llm add (add another endpoint) | /llm clear (clear pool)[/dim]\n")
                continue

            elif user_input in ["/doctor", "doctor"]:
                from octoflow.cli import run_doctor

                run_doctor(workspace=str(s.workspace))
                continue

            elif user_input in ["/init", "/init-ide"]:
                from octoflow.onboarding import onboard_ide

                c.print(f"\n[{s.theme.rich_primary}]◈ Auto-Onboarding Omni-IDE Surfaces for Workspace...[/{s.theme.rich_primary}]")
                res = onboard_ide(workspace=str(s.workspace))
                t = Table(title="Omni-IDE Developer Surface Status", border_style=s.theme.rich_border, expand=True)
                t.add_column("Developer Surface", style="bold white", width=28)
                t.add_column("Status", width=14)
                t.add_column("Configuration Details", style="white")

                t.add_row("Cursor AI (.cursorrules)", f"[{s.theme.rich_success}]✔ CONFIGURED[/]" if res["cursor"] else "[dim]SKIPPED[/]", "8-Arm Swarm delegation rules & architecture heuristics")
                t.add_row("Claude Code CLI (~/.claude.json)", f"[{s.theme.rich_success}]✔ INJECTED[/]" if res["claude_code"] else "[dim]SKIPPED[/]", "Direct MCP connection for multi-file swarm execution")
                t.add_row("Claude Desktop App", f"[{s.theme.rich_success}]✔ INJECTED[/]" if res["claude_desktop"] else "[dim]NOT FOUND[/]", "Desktop UI connectome MCP tool integration")
                t.add_row("VS Code (.vscode/tasks.json)", f"[{s.theme.rich_success}]✔ CONFIGURED[/]" if res["vscode_tasks"] else "[dim]SKIPPED[/]", "4 Command Palette shortcut tasks (Cockpit, Guard, UI, Doctor)")
                t.add_row("Git Pre-Commit Hook", f"[{s.theme.rich_success}]✔ INSTALLED[/]" if res["git_hooks"] else "[dim]SKIPPED[/]", "Swarm Guard AST validation & secret leak protection")

                c.print(t)
                c.print(f"[{s.theme.rich_success}]✔ Omni-IDE onboarding completed in <1s. Zero manual configuration required![/{s.theme.rich_success}]\n")
                continue

            elif user_input.startswith("/plan"):
                parts = user_input.split(maxsplit=1)
                plan_goal = parts[1].strip() if len(parts) > 1 else ""
                if not plan_goal:
                    plan_goal = prompt_user_str(c, f"[{s.theme.rich_primary}]Enter objective to blueprint: [/{s.theme.rich_primary}]")
                if not plan_goal:
                    continue

                c.print(f"\n[{s.theme.rich_primary}]◈ Architect Decomposing 8-Arm Neural Blueprint...[/{s.theme.rich_primary}]\n")
                from octoflow.conductor import SupraesophagealConductor
                m_enum = SwarmMorphology.CUSTOM if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(s.current_guild)
                plan_conductor = SupraesophagealConductor(
                    config=OctoFlowConfig(
                        workspace_dir=str(s.workspace),
                        model_provider=s.current_model,
                        morphology=m_enum,
                        guild=s.current_guild if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                    )
                )
                sub_goals = plan_conductor.decompose_objective(plan_goal)
                roster = plan_conductor.config.get_roster()

                plan_table = Table(title=f"8-Arm Mission Blueprint: '{plan_goal[:50]}'", border_style=s.theme.rich_border, expand=True)
                plan_table.add_column("Arm", width=6, style=s.theme.rich_primary)
                plan_table.add_column("Guild Role", width=22, style="bold white")
                plan_table.add_column("Tier", width=12, style=s.theme.rich_secondary)
                plan_table.add_column("Assigned Arm Objective", style="white")

                for arm_id in range(8):
                    role_cfg = roster[arm_id] if arm_id < len(roster) else None
                    role_title = role_cfg.title if role_cfg else f"Arm {arm_id}"
                    tier = getattr(role_cfg, "model_tier", "balanced")
                    goal_text = sub_goals.get(arm_id, "Idle")
                    clean_goal = goal_text.split(" (Existing Codebase Context:")[0]
                    plan_table.add_row(f"Arm {arm_id}", role_title, tier.upper(), clean_goal)

                c.print(plan_table)
                confirm = prompt_user_str(c, f"\n[{s.theme.rich_primary}]Deploy swarm with this 8-arm blueprint? (Y/edit/cancel): [/{s.theme.rich_primary}]").lower()
                if confirm in ["", "y", "yes"]:
                    user_input = plan_goal
                elif confirm in ["e", "edit"]:
                    adjusted = prompt_user_str(c, f"[{s.theme.rich_primary}]Enter modified objective instructions: [/{s.theme.rich_primary}]")
                    if adjusted:
                        user_input = f"{plan_goal} (Note: {adjusted})"
                    else:
                        continue
                else:
                    c.print("[dim]Mission blueprint cancelled.[/dim]\n")
                    continue

            elif user_input.startswith("/ask"):
                from octoflow.conductor import SupraesophagealConductor
                parts = user_input.split(maxsplit=2)
                m_enum = SwarmMorphology.CUSTOM if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(s.current_guild)
                active_conductor = SupraesophagealConductor(
                    config=OctoFlowConfig(
                        workspace_dir=str(s.workspace),
                        model_provider=s.current_model,
                        morphology=m_enum,
                        guild=s.current_guild if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                    )
                )
                if len(parts) == 1:
                    c.print(f"[{s.theme.rich_primary}]Tip: Ask any question directly or target an arm: [bold]/ask <arm_or_role> <question>[/bold][/{s.theme.rich_primary}]\n")
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

                c.print(Panel(
                    Markdown(resp),
                    title=f"[{s.theme.rich_primary}]● {p_title} [Arm {p_id}][/{s.theme.rich_primary}] [dim](in consultation with {s_title})[/dim]",
                    border_style=s.theme.rich_border,
                ))
                c.print()
                continue

            elif user_input.startswith("/talk"):
                from octoflow.conductor import SupraesophagealConductor
                parts = user_input.split(maxsplit=1)
                target_ident = parts[1].strip() if len(parts) > 1 else "0"
                m_enum = SwarmMorphology.CUSTOM if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(s.current_guild)
                active_conductor = SupraesophagealConductor(
                    config=OctoFlowConfig(
                        workspace_dir=str(s.workspace),
                        model_provider=s.current_model,
                        morphology=m_enum,
                        guild=s.current_guild if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                    )
                )
                arm = active_conductor.get_arm(target_ident) or active_conductor.arms[0]
                c.print(f"[{s.theme.rich_success}]Connected 1-on-1 with [bold]{arm.role.title}[/bold] (Arm {arm.arm_id}). Type [bold]/exit[/bold] to return to cockpit.[/{s.theme.rich_success}]")
                while True:
                    try:
                        sub_q = prompt_user_str(c, f"[{s.theme.rich_secondary}][{arm.role.title}:Arm {arm.arm_id}] ❯ [/{s.theme.rich_secondary}]")
                        if not sub_q:
                            continue
                        if sub_q in ["/exit", "exit", "/quit", "quit"]:
                            c.print(f"[{s.theme.rich_primary}]Returned to main cockpit.[/{s.theme.rich_primary}]\n")
                            break
                        hits = active_conductor.memory.search_codebase(sub_q, top_k=2)
                        rag_ctx = "\n".join(f"{h['file_path']}:\n{h['snippet']}" for h in hits) if hits else ""
                        sub_resp = arm.answer_query(sub_q, context=rag_ctx)
                        c.print(Panel(Markdown(sub_resp), border_style=s.theme.rich_border))
                        c.print()
                    except (KeyboardInterrupt, EOFError):
                        c.print()
                        break
                continue

            elif user_input.startswith("/theme") or user_input == "theme" or user_input.startswith("theme "):
                if user_input.startswith("theme"):
                    user_input = "/" + user_input
                parts = user_input.split(maxsplit=1)
                if len(parts) == 1:
                    if sys.stdin.isatty() and sys.stdout.isatty():
                        from octoflow.theme_selector import run_interactive_theme_picker

                        s.theme = run_interactive_theme_picker(c, initial_theme=s.theme, broadcaster=s.broadcaster)
                        print_welcome_banner(s, c, animate=True)
                        c.print(f"[{s.theme.rich_success}]✔ Palette active: [bold]{s.theme.name}[/bold] ({s.theme.description})[/{s.theme.rich_success}]\n")
                        continue
                    themes_all = list_themes()
                    theme_table = Table(title="◈ Available Developer Palettes", border_style=s.theme.rich_border, expand=True)
                    theme_table.add_column("#", width=4, style=s.theme.rich_primary)
                    theme_table.add_column("Theme ID", style="bold white", width=16)
                    theme_table.add_column("Name", style="white", width=22)
                    theme_table.add_column("Palette Swatch", width=14)
                    theme_table.add_column("Description", style="dim")

                    for idx, (t_id, t_obj) in enumerate(themes_all.items(), 1):
                        is_active = " [bold green]✔ ACTIVE[/]" if t_id == s.theme.id else ""
                        swatch = f"[{t_obj.rich_primary}]●[/{t_obj.rich_primary}] [{t_obj.rich_secondary}]●[/{t_obj.rich_secondary}] [{t_obj.rich_success}]●[/{t_obj.rich_success}] [{t_obj.rich_warning}]●[/{t_obj.rich_warning}]"
                        theme_table.add_row(str(idx), t_id + is_active, t_obj.name, swatch, t_obj.description)

                    c.print(theme_table)
                    c.print(f"[dim]Tip: Switch by typing [bold]/theme <id>[/bold] (e.g. [cyan]/theme catppuccin[/cyan])[/dim]\n")
                else:
                    new_theme_name = parts[1].strip()
                    s.theme = get_theme(new_theme_name)
                    save_theme_preference(s.theme.id)
                    if s.broadcaster:
                        s.broadcaster.broadcast_raw({
                            "type": "THEME_CHANGE",
                            "theme_id": s.theme.id,
                            "tokens": asdict(s.theme),
                        })
                    print_welcome_banner(s, c, animate=True)
                    c.print(f"[{s.theme.rich_success}]✔ Switched palette to: [bold]{s.theme.name}[/bold] ({s.theme.description})[/{s.theme.rich_success}]")
                    c.print(f"[dim]Saved to ~/.octoflow/theme.json and synchronized with 3D Visualizer.[/dim]\n")
                continue

            elif user_input.startswith("/model"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    s.current_model = parts[1].strip().lower()
                    c.print(f"[{s.theme.rich_success}]✔ LLM core updated to: [bold]{s.current_model.upper()}[/bold][/{s.theme.rich_success}]\n")
                else:
                    c.print(f"[yellow]Current model:[/yellow] {s.current_model}. Options: mock, anthropic, openai, ollama\n")
                continue

            elif user_input.startswith("/octos"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    s.current_octos = parts[1].strip().lower()
                    c.print(f"[{s.theme.rich_success}]✔ Swarm scaling tier set to: [bold]{s.current_octos.upper()}[/bold][/{s.theme.rich_success}]\n")
                else:
                    c.print(f"[yellow]Current tier:[/yellow] {s.current_octos}. Options: auto, 1 (Solo), 3 (Triad), 8 (Octopolis)\n")
                continue

            elif user_input.startswith("/budget"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    try:
                        s.current_budget = float(parts[1].strip().replace("$", ""))
                        c.print(f"[{s.theme.rich_success}]✔ Spending ceiling set to: [bold]${s.current_budget:.2f}[/bold][/{s.theme.rich_success}]\n")
                    except ValueError:
                        c.print(f"[{s.theme.rich_danger}]Invalid budget format. Use e.g. /budget 15.00[/{s.theme.rich_danger}]\n")
                else:
                    c.print(f"[yellow]Current budget:[/yellow] ${s.current_budget:.2f}\n")
                continue

            elif user_input == "/ui":
                import webbrowser

                try:
                    webbrowser.open(s.visualizer_url)
                except Exception:
                    pass
                c.print(f"[{s.theme.rich_primary}]● 3D Cephalopod Constellation visualizer active at: [underline]{s.visualizer_url}[/underline][/{s.theme.rich_primary}]\n")
                continue

            elif user_input == "/ignite":
                from octoflow.ignition import ProjectIgniter
                c.print(f"[{s.theme.rich_primary}]⚡ Igniting project runtime services in {s.workspace}...[/{s.theme.rich_primary}]")
                igniter = ProjectIgniter(workspace_dir=str(s.workspace))
                manifest = igniter.ignite()
                if manifest.primary_url:
                    c.print(f"[{s.theme.rich_success}]✔ Primary Live Service:[/{s.theme.rich_success}] {manifest.primary_url}")
                if manifest.api_docs_url:
                    c.print(f"[{s.theme.rich_success}]✔ API Docs Live:[/{s.theme.rich_success}] {manifest.api_docs_url}")
                if manifest.status == "FAILED" or manifest.error_message:
                    c.print(f"[{s.theme.rich_warning}]▲ Notice: {manifest.error_message}[/{s.theme.rich_warning}]")
                else:
                    c.print(f"[{s.theme.rich_success}]✔ Runtime online: [bold]{manifest.title}[/bold] ({manifest.service_type})[/{s.theme.rich_success}]")
                c.print()
                continue

            elif user_input == "/diff":
                res = subprocess.run(["git", "diff"], cwd=str(s.workspace), capture_output=True, text=True)
                if res.stdout.strip():
                    from rich.syntax import Syntax

                    syntax = Syntax(res.stdout, "diff", theme="monokai", line_numbers=True)
                    c.print(syntax)
                else:
                    c.print("[dim]No uncommitted git changes in workspace.[/dim]\n")
                continue

            elif user_input.startswith("/commit"):
                parts = user_input.split(maxsplit=1)
                msg = parts[1].strip() if len(parts) > 1 else ""
                res = subprocess.run(["git", "status", "--porcelain"], cwd=str(s.workspace), capture_output=True, text=True)
                if not res.stdout.strip():
                    c.print("[dim]No uncommitted changes in workspace to commit.[/dim]\n")
                    continue
                if not msg:
                    msg = prompt_user_str(c, f"[{s.theme.rich_primary}]Enter commit message: [/{s.theme.rich_primary}]")
                    if not msg:
                        msg = "swarm enhancements"
                commit_msg = f"feat(octos): {msg}"
                subprocess.run(["git", "add", "-A"], cwd=str(s.workspace), check=False)
                c_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(s.workspace), capture_output=True, text=True)
                if c_res.returncode == 0:
                    c.print(f"[{s.theme.rich_success}]✔ Committed workspace changes: [bold]{commit_msg}[/bold][/{s.theme.rich_success}]\n")
                else:
                    c.print(f"[{s.theme.rich_danger}]Commit note: {c_res.stderr.strip() or c_res.stdout.strip()}[/{s.theme.rich_danger}]\n")
                continue

            elif user_input in ["/rollback", "/undo"]:
                chk_file = Path.home() / ".octoflow" / "last_checkpoint.json"
                if not chk_file.exists():
                    c.print("[dim]No prior checkpoint found to rollback.[/dim]\n")
                    continue
                try:
                    chk_data = json.loads(chk_file.read_text(encoding="utf-8"))
                    target_head = chk_data.get("head")
                    obj = chk_data.get("objective", "previous mission")
                    c.print(f"[{s.theme.rich_warning}]▲ Rollback: Reverting workspace changes from objective '[bold]{obj[:45]}[/bold]'...[/{s.theme.rich_warning}]")
                    if target_head:
                        subprocess.run(["git", "reset", "--hard", target_head], cwd=str(s.workspace), capture_output=True)
                        subprocess.run(["git", "clean", "-fd"], cwd=str(s.workspace), capture_output=True)
                        c.print(f"[{s.theme.rich_success}]✔ Cleanly reverted workspace to checkpoint ({target_head[:8]}).[/{s.theme.rich_success}]\n")
                    else:
                        c.print("[yellow]Checkpoint recorded but no git commit hash was available.[/yellow]\n")
                except Exception as rb_err:
                    c.print(f"[{s.theme.rich_danger}]Rollback error: {rb_err}[/{s.theme.rich_danger}]\n")
                continue

            elif user_input == "/memory":
                mem_path = Path.home() / ".octoflow" / "vertical_lobe.json"
                if mem_path.exists():
                    try:
                        data = json.loads(mem_path.read_text(encoding="utf-8"))
                        entries = data.get("entries", [])
                        c.print(f"[{s.theme.rich_primary}]◈ Vertical Lobe Memory ({len(entries)} Hebbian Heuristics):[/{s.theme.rich_primary}]")
                        for idx, e in enumerate(entries[:5], 1):
                            c.print(f"  {idx}. [bold]{e.get('signature', 'General')}[/bold]: {e.get('guidance', '')[:80]}...")
                        c.print()
                    except Exception as err:
                        c.print(f"[dim]Could not parse memory: {err}[/dim]\n")
                else:
                    c.print("[dim]Vertical Lobe memory initialized; no persisted heuristics yet.[/dim]\n")
                continue

            elif user_input == "/status":
                c.print(f"[{s.theme.rich_primary}]◈ Cephalopod Swarm Status:[/{s.theme.rich_primary}]")
                c.print(f"  • Model: [bold]{s.current_model}[/bold]")
                c.print(f"  • Guild / Roster: [bold]{s.current_guild}[/bold]")
                c.print(f"  • Octopuses: [bold]{s.current_octos}[/bold]")
                c.print(f"  • Budget Limit: [bold]${s.current_budget:.2f}[/bold]")
                c.print(f"  • Theme: [bold]{s.theme.name}[/bold]")
                c.print(f"  • Workspace: {s.workspace}")
                c.print(f"  • Visualizer URL: {s.visualizer_url}\n")
                continue

            elif user_input.startswith("/guild"):
                parts = user_input.split(maxsplit=1)
                if len(parts) == 1:
                    guilds = list_available_guilds()
                    g_table = Table(title="Specialist 8-Arm Guilds & Rosters", border_style=s.theme.rich_border, expand=True)
                    g_table.add_column("Guild Name", style="bold white", width=18)
                    g_table.add_column("Type", style=s.theme.rich_secondary, width=12)
                    g_table.add_column("Description", style="white")

                    for g_name, g_desc in guilds.items():
                        is_active = " [bold green]✔ ACTIVE[/]" if g_name == s.current_guild else ""
                        g_type = "Built-In" if g_name in ["software_dev", "aiml_research", "fullstack_ai"] else "Community"
                        g_table.add_row(g_name + is_active, g_type, g_desc)

                    c.print(g_table)
                    c.print(f"[dim]Tip: Switch guild by typing [bold]/guild <name>[/bold] (e.g. [cyan]/guild aiml_research[/cyan])[/dim]\n")
                else:
                    target_guild = parts[1].strip()
                    roster_chk = load_custom_guild(target_guild)
                    if roster_chk:
                        s.current_guild = target_guild
                        c.print(f"[{s.theme.rich_success}]✔ Active specialist guild switched to: [bold]{s.current_guild}[/bold][/{s.theme.rich_success}]\n")
                    else:
                        c.print(f"[{s.theme.rich_danger}]Guild '{target_guild}' not found. Use /guild to list available rosters.[/{s.theme.rich_danger}]\n")
                continue

            elif user_input == "/guard":
                from octoflow.cli import run_guard

                run_guard(workspace=str(s.workspace))
                continue

            elif user_input == "/hooks":
                from octoflow.cli import install_git_hooks

                install_git_hooks(workspace=str(s.workspace))
                continue

            elif user_input.startswith("/rag") or user_input.startswith("/search"):
                from octoflow.memory import VerticalLobeMemory
                parts = user_input.split(maxsplit=1)
                vl = VerticalLobeMemory()
                num_chunks = vl.index_codebase(str(s.workspace))
                if len(parts) == 1:
                    c.print(f"[{s.theme.rich_success}]✔ Episodic Codebase Vector RAG: Indexed [bold]{num_chunks}[/bold] code chunks across workspace.[/{s.theme.rich_success}]")
                    c.print(f"[dim]Tip: Search codebase semantically using [bold]/rag <query>[/bold] (e.g. /rag auth token)[/dim]\n")
                else:
                    q = parts[1].strip()
                    hits = vl.search_codebase(q, top_k=4)
                    if not hits:
                        c.print(f"[yellow]No semantic matches found for query: '{q}'[/yellow]\n")
                    else:
                        r_table = Table(title=f"Episodic Vector Hits for '{q}'", border_style=s.theme.rich_border, expand=True)
                        r_table.add_column("Score", width=8, style=s.theme.rich_primary)
                        r_table.add_column("File", width=28, style="bold white")
                        r_table.add_column("Lines", width=12, style=s.theme.rich_secondary)
                        r_table.add_column("Snippet Preview", style="dim")
                        for h in hits:
                            sym = f" ({h['symbol']})" if h.get("symbol") else ""
                            r_table.add_row(f"{h['score']:.3f}", f"{h['file_path']}{sym}", f"L{h['start_line']}-{h['end_line']}", h['snippet'].splitlines()[0][:60] if h['snippet'] else "")
                        c.print(r_table)
                        c.print()
                continue

            elif user_input in ["/ci", "/review-pr"]:
                from octoflow.ci import review_pull_request

                c.print(f"\n[{s.theme.rich_primary}]● OctoFlow Swarm Guard: Auditing Pull Request Diff...[/{s.theme.rich_primary}]\n")
                res = review_pull_request(workspace=str(s.workspace), write_summary=False)
                t = Table(title="OctoFlow Swarm Guard PR Audit", border_style=s.theme.rich_border, expand=True)
                t.add_column("Ganglia Arm", style="bold white", width=22)
                t.add_column("Role Scope", style=s.theme.rich_secondary, width=20)
                t.add_column("Status", width=12)
                t.add_column("Audit Findings", style="white")

                arm6_ok = not any("CRITICAL" in f for f in res["arm6_findings"])
                arm5_ok = not any("CRITICAL" in f for f in res["arm5_findings"])
                arm0_ok = not any("Inverted" in f for f in res["arm0_findings"])

                t.add_row("Arm 6: Security", "Credentials & Injection", f"[{s.theme.rich_success}]✔ PASSED[/]" if arm6_ok else f"[{s.theme.rich_danger}]✖ BLOCKED[/]", " • ".join(res["arm6_findings"]))
                t.add_row("Arm 5: QA & AST", "Syntax & Test Coverage", f"[{s.theme.rich_success}]✔ PASSED[/]" if arm5_ok else f"[{s.theme.rich_danger}]✖ BLOCKED[/]", " • ".join(res["arm5_findings"]))
                t.add_row("Arm 0: Architect", "Topology & Contracts", f"[{s.theme.rich_success}]✔ PASSED[/]" if arm0_ok else f"[{s.theme.rich_warning}]ℹ ADVISORY[/]", " • ".join(res["arm0_findings"]))
                c.print(t)
                if res["hard_block"]:
                    c.print(f"\n[{s.theme.rich_danger}]✖ Merge Blocked: Critical security vulnerabilities or AST syntax errors detected.[/{s.theme.rich_danger}]\n")
                else:
                    c.print(f"\n[{s.theme.rich_success}]✔ Swarm Verdict: READY TO MERGE. Zero merge hazards detected.[/{s.theme.rich_success}]\n")
                continue

            elif user_input == "/init-action":
                from octoflow.ci import generate_github_action_workflow

                wf_path = generate_github_action_workflow(str(s.workspace))
                c.print(f"\n[{s.theme.rich_success}]✔ Generated GitHub Actions Workflow:[/{s.theme.rich_success}] [bold white]{wf_path}[/bold white]")
                c.print(f"[dim]Every Pull Request will now automatically trigger Arm 6 (Security), Arm 5 (QA/AST), and Arm 0 (Architect) audits.[/dim]\n")
                continue

            elif user_input in ["/export", "/report"] or user_input.startswith("/export ") or user_input.startswith("/report "):
                from octoflow.report import collect_mission_audit_data, generate_html_audit_report

                parts = user_input.split(maxsplit=1)
                custom_out = parts[1].strip() if len(parts) > 1 else None
                c.print(f"\n[{s.theme.rich_primary}]◈ Generating Standalone HTML Swarm Mission Audit...[/{s.theme.rich_primary}]")
                hist = s.broadcaster.get_history() if s.broadcaster else []
                m_data = collect_mission_audit_data(workspace=str(s.workspace), telemetry_events=hist)
                out_path = generate_html_audit_report(m_data, output_path=custom_out, theme_id=s.theme.id)
                c.print(f"[{s.theme.rich_success}]✔ Exported Standalone Audit Report:[/{s.theme.rich_success}] [bold white]{out_path}[/bold white]")
                c.print(f"[dim]100% self-contained single-file HTML • Zero external CDN dependencies • Connectome replay included.[/dim]")
                open_ans = prompt_user_str(c, f"[{s.theme.rich_primary}]Open report in browser? (Y/n): [/{s.theme.rich_primary}]").lower()
                if open_ans in ["", "y", "yes"]:
                    import webbrowser

                    webbrowser.open(f"file://{out_path.resolve()}")
                c.print()
                continue

            elif user_input in ["/heal", "/fix"] or user_input.startswith("/heal ") or user_input.startswith("/fix "):
                from octoflow.healing import self_heal_workspace

                c.print(f"\n[{s.theme.rich_primary}]◈ OctoFlow Autonomous Self-Healing: Running test suite and diagnosing...[/{s.theme.rich_primary}]\n")
                m_enum = SwarmMorphology.CUSTOM if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(s.current_guild)
                heal_cfg = OctoFlowConfig(
                    workspace_dir=str(s.workspace),
                    model_provider=s.current_model,
                    morphology=m_enum,
                    guild=s.current_guild if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
                )
                res = self_heal_workspace(workspace_dir=str(s.workspace), config=heal_cfg)
                t = Table(title="OctoFlow Self-Healing Summary", border_style=s.theme.rich_border, expand=True)
                t.add_column("Property", style=s.theme.rich_secondary, width=20)
                t.add_column("Value", style="bold white")
                status_str = f"[{s.theme.rich_success}]✔ HEALED & PASSING[/]" if res["success"] else f"[{s.theme.rich_danger}]✖ UNRESOLVED[/]"
                t.add_row("Status", status_str)
                t.add_row("Framework", res["framework"].upper())
                t.add_row("Attempts Used", str(res["attempts"]))
                t.add_row("Repaired Files", ", ".join(res["repaired_files"]) if res["repaired_files"] else "None (tests passing)")
                t.add_row("Result Note", res["message"])
                c.print(t)
                c.print()
                continue

            elif user_input in ["/triage", "/review", "/diff-review"]:
                from octoflow.triage import triage_workspace_diffs

                c.print(f"\n[{s.theme.rich_primary}]◈ OctoFlow Patch Triage: Reviewing uncommitted changes...[/{s.theme.rich_primary}]")
                res = triage_workspace_diffs(workspace_dir=str(s.workspace), interactive=True, console=c)
                c.print(f"\n[{s.theme.rich_success}]✔ {res['message']}[/{s.theme.rich_success}]\n")
                continue

            elif user_input.startswith("/notify") or user_input.startswith("/alert"):
                from octoflow.notify import send_mission_notification

                parts = user_input.split(maxsplit=1)
                msg_text = parts[1].strip() if len(parts) > 1 else "Cockpit Mission Update"
                ok = send_mission_notification(custom_message=msg_text)
                if ok:
                    c.print(f"[{s.theme.rich_success}]✔ Successfully dispatched alert to team webhook.[/{s.theme.rich_success}]\n")
                else:
                    c.print(f"[{s.theme.rich_warning}]▲ Webhook dispatch skipped: Set webhook_url in ~/.octoflow/config.json or pass --url.[/{s.theme.rich_warning}]\n")
                continue

            elif user_input in ["/audit", "audit"] or user_input.startswith("/audit "):
                from octoflow.audit import evaluate_workspace, print_audit_report

                c.print(f"\n[{s.theme.rich_primary}]◈ Running 100-Point Cephalopod MetaHarness Audit...[/{s.theme.rich_primary}]")
                rep = evaluate_workspace(str(s.workspace))
                print_audit_report(rep, console=c)
                continue

            elif user_input in ["/eject", "eject"] or user_input.startswith("/eject "):
                from octoflow.eject import eject_harness

                parts = user_input.split(maxsplit=1)
                target_out = parts[1].strip() if len(parts) > 1 else "./octo-harness"
                eject_harness(output_dir=target_out, console=c)
                continue

            elif user_input in ["/install-claude", "install-claude"]:
                from octoflow.cli import install_claude_cli_cmd

                install_claude_cli_cmd()
                continue

            elif user_input.startswith("/federation"):
                parts = user_input.split()
                act = parts[1] if len(parts) > 1 else "status"
                from octoflow.federation import GLOBAL_FEDERATION_GUARD, PII_RULES

                if act == "status":
                    t = Table(title="Zero-Trust Federation & PII Security Rules", border_style=s.theme.rich_border)
                    t.add_column("Rule Name", style="bold white", width=22)
                    t.add_column("Severity", style=s.theme.rich_secondary, width=12)
                    t.add_column("Redacted Mask", style="dim", width=32)
                    for r in PII_RULES:
                        t.add_row(r.name, r.severity, r.replacement)
                    c.print(t)
                    c.print(f"[dim]Default PII Action: [bold green]{GLOBAL_FEDERATION_GUARD.default_action.value}[/bold green] | Total Intercepted Events: {len(GLOBAL_FEDERATION_GUARD.audit_log)}[/dim]\n")
                elif act in ["test", "test-pii"]:
                    sample = " ".join(parts[2:]) if len(parts) > 2 else ("My key is " + "sk-ant-" + "api03-abcdef123456789012345678 and email is test@company.com")
                    cleaned, events = GLOBAL_FEDERATION_GUARD.scan_and_sanitize(sample)
                    c.print(f"[{s.theme.rich_primary}]Original Input:[/{s.theme.rich_primary}] {sample}")
                    c.print(f"[{s.theme.rich_success}]Sanitized Output:[/{s.theme.rich_success}] {cleaned}")
                    c.print(f"[dim]Intercepted {len(events)} security/PII patterns.[/dim]\n")
                continue

            elif user_input in ["/manual", "/docs", "manual", "docs"] or user_input.startswith("/manual ") or user_input.startswith("/docs "):
                from octoflow.manual import display_manual

                parts = user_input.split(maxsplit=1)
                ch = parts[1].strip() if len(parts) > 1 else None
                display_manual(chapter=ch, console=c)
                continue

            elif user_input in ["/bench", "/benchmark"] or user_input.startswith("/bench ") or user_input.startswith("/benchmark "):
                from octoflow.bench import run_swarm_benchmark_suite

                parts = user_input.split(maxsplit=1)
                task_k = parts[1].strip() if len(parts) > 1 else None
                c.print(f"\n[{s.theme.rich_primary}]◈ OctoFlow Swarm Benchmark Suite: Starting evaluation harness...[/{s.theme.rich_primary}]\n")
                run_swarm_benchmark_suite(task_key=task_k, console=c)
                continue

            elif user_input in ["/monorepo", "/packages"]:
                from octoflow.monorepo import scan_monorepo_topology

                topo = scan_monorepo_topology(str(s.workspace))
                t = Table(title="Monorepo Package & Swarm Topology", border_style=s.theme.rich_border, expand=True)
                t.add_column("Package Name", style="bold white", width=22)
                t.add_column("Subdirectory", style=s.theme.rich_secondary, width=24)
                t.add_column("Type", width=12)
                t.add_column("Primary Specialist Arm", style=s.theme.rich_primary)

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
                c.print(t)
                c.print(f"[dim]Total packages detected: [bold]{len(packages)}[/bold] (Monorepo: [bold]{'YES' if topo.get('is_monorepo') else 'NO'}[/bold])[/dim]\n")
                continue

            elif user_input.startswith("/record"):
                from octoflow.recorder import TerminalRecorder

                parts = user_input.split(maxsplit=1)
                cast_out = parts[1].strip() if len(parts) > 1 else "octoflow_mission.cast"
                rec = TerminalRecorder(title="OctoFlow Interactive Mission")
                rec.start()
                rec.record_output(f"OctoFlow Interactive Terminal Session: {s.workspace}\r\n")
                rec.record_output(f"Theme: {s.theme.name} | Swarm: {s.current_octos}\r\n")
                rec.stop()
                saved_cast = rec.export_cast(cast_out)
                c.print(f"[{s.theme.rich_success}]✔ Exported Asciinema .cast session to: [bold white]{saved_cast}[/bold white][/{s.theme.rich_success}]\n")
                continue

            # Intelligent Conversational Reflex: Check if user input is an Inquiry vs Action
            from octoflow.conductor import SupraesophagealConductor
            m_enum = SwarmMorphology.CUSTOM if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else SwarmMorphology(s.current_guild)
            active_conductor = SupraesophagealConductor(
                config=OctoFlowConfig(
                    workspace_dir=str(s.workspace),
                    model_provider=s.current_model,
                    morphology=m_enum,
                    guild=s.current_guild if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None,
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
                    title=f"[{s.theme.rich_primary}]● {p_title} [Arm {p_id}][/{s.theme.rich_primary}] [dim](in consultation with {s_title})[/dim]",
                    border_style=s.theme.rich_border,
                    subtitle="[dim]Ask follow-up questions, or provide an action directive to deploy the swarm.[/dim]",
                )
                c.print(resp_panel)
                c.print()
                continue

            # Check git branch safety for existing codebases
            try:
                b_chk = subprocess.run(["git", "branch", "--show-current"], cwd=str(s.workspace), capture_output=True, text=True, timeout=1)
                curr_branch = b_chk.stdout.strip()
                if curr_branch in ["main", "master"]:
                    import re

                    clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', user_input.lower())[:24].strip('-')
                    safe_branch = f"octos/{clean_slug or 'task'}"
                    c.print(f"[{s.theme.rich_warning}]▲  Branch Protection: You are on production branch '[bold]{curr_branch}[/bold]'.[/{s.theme.rich_warning}]")
                    branch_ans = prompt_user_str(c, f"[{s.theme.rich_primary}]Switch to safety branch '[bold]{safe_branch}[/bold]'? (Y/n): [/{s.theme.rich_primary}]").lower()
                    if branch_ans in ["", "y", "yes"]:
                        sw_out = subprocess.run(["git", "checkout", "-b", safe_branch], cwd=str(s.workspace), capture_output=True, text=True)
                        if sw_out.returncode == 0:
                            c.print(f"[{s.theme.rich_success}]✔ Switched to protection branch: [bold]{safe_branch}[/bold][/{s.theme.rich_success}]\n")
            except Exception:
                pass

            # Pre-mission git checkpoint for /rollback
            try:
                rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(s.workspace), capture_output=True, text=True, timeout=1)
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
            c.print(f"\n[{s.theme.rich_primary}]◈ Deploying Swarm on Objective:[/{s.theme.rich_primary}] [bold white]{user_input}[/bold white]\n")

            try:
                from octoflow.cli import run as swarm_run

                resolved_mode = "custom" if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else s.current_guild
                resolved_guild = s.current_guild if s.current_guild not in ["software_dev", "aiml_research", "fullstack_ai"] else None
                swarm_run(
                    objective=user_input,
                    mode=resolved_mode,
                    guild=resolved_guild,
                    model=s.current_model,
                    budget=s.current_budget,
                    workspace=str(s.workspace),
                    port=s.port,
                    open_ui=False,
                    octos=s.current_octos,
                    theme=s.theme.id,
                    sandbox="local",
                )
            except Exception as swarm_err:
                c.print(f"[{s.theme.rich_danger}]Swarm execution note: {swarm_err}[/{s.theme.rich_danger}]")

            # Post-execution Action Ribbon
            ribbon_text = Text.from_markup(
                f"[{s.theme.rich_success}]◈ Mission Phase Concluded.[/{s.theme.rich_success}]\n"
                f"  Quick Actions:  "
                f"[{s.theme.rich_primary}]/ignite[/] (Preview App)  •  "
                f"[{s.theme.rich_secondary}]/diff[/] (Inspect Changes)  •  "
                f"[{s.theme.rich_warning}]/rollback[/] (Undo Changes)  •  "
                f"[{s.theme.rich_accent}]/ui[/] (3D Connectome)  •  "
                f"[white]Type next goal to continue[/]"
            )
            c.print(Panel(ribbon_text, border_style=s.theme.rich_border))
            c.print()

        except KeyboardInterrupt:
            c.print(f"\n[yellow]⚡ Swarm paused (Ctrl+C). Type /exit to quit.[/yellow]\n")
        except EOFError:
            break


# Backward-compatible alias
interactive_cockpit = run_cockpit
