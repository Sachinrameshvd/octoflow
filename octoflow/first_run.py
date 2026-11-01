"""Guided First-Run Onboarding Flow for OctoFlow (P6.1).

Detects environment readiness, guides the user with at most three questions,
executes a 60-second demo task under ~/.octoflow/demo, and persists
onboarding_completed in ~/.octoflow/config.json.
"""

import getpass
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from octoflow.budget import RunBudget
from octoflow.config import get_octoflow_dir, load_secure_config, save_secure_config
from octoflow.keyring_store import (
    is_keyring_available,
    resolve_api_key,
    set_keyring_key,
)
from octoflow.logging_config import get_log_file_path
from octoflow.settings import get_default_config_path, load_settings
from octoflow.themes import load_saved_theme

console = Console()


def get_ollama_base_url() -> str:
    """Return configured Ollama base URL or default localhost:11434."""
    return (
        os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OCTOFLOW_OLLAMA_URL")
        or "http://localhost:11434"
    ).rstrip("/")


def should_run_first_run_wizard() -> bool:
    """Determine whether to trigger the guided first-run onboarding flow."""
    # 1. Escape hatch
    if os.getenv("OCTOFLOW_SKIP_ONBOARDING") == "1":
        return False
    # 2. Non-interactive flag
    if os.getenv("OCTOFLOW_NONINTERACTIVE") == "1":
        return False
    # 3. Non-TTY runs never prompt
    if not sys.stdin.isatty():
        return False
    # 4. Check if onboarding completed or config exists
    cfg_file = get_default_config_path()
    if not cfg_file.exists():
        return True
    try:
        settings = load_settings(cfg_path=cfg_file)
        return not getattr(settings, "onboarding_completed", False)
    except Exception:
        return True


def check_environment(ollama_url: str | None = None) -> dict[str, Any]:
    """Inspect environment (Python, Git, Ollama daemon & model)."""
    base_ollama = (ollama_url or get_ollama_base_url()).rstrip("/")
    status = {
        "python_ok": sys.version_info >= (3, 10),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "git_ok": False,
        "git_version": "unknown",
        "ollama_ok": False,
        "ollama_url": base_ollama,
        "ollama_models": [],
        "has_coder_model": False,
    }

    # Check Git
    try:
        res = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=1.5)
        if res.returncode == 0:
            status["git_ok"] = True
            status["git_version"] = res.stdout.strip().replace("git version ", "")
    except Exception:
        pass

    # Check Ollama Daemon
    try:
        resp = httpx.get(f"{base_ollama}/api/tags", timeout=1.0)
        if resp.status_code == 200:
            status["ollama_ok"] = True
            data = resp.json()
            raw_models = [m.get("name", "") for m in data.get("models", [])]
            status["ollama_models"] = raw_models
            for m in raw_models:
                m_low = m.lower()
                if any(k in m_low for k in ("qwen2.5-coder", "coder", "deepseek-coder", "llama")):
                    status["has_coder_model"] = True
                    break
    except Exception:
        pass

    return status


def display_env_summary(env_status: dict[str, Any]) -> None:
    """Print compact status table with pass/fail and fix hints."""
    cur_theme = load_saved_theme()
    table = Table(
        title="◈ Environment Pre-Flight Diagnostics",
        border_style=cur_theme.rich_border,
        expand=True,
    )
    table.add_column("Subsystem", style=cur_theme.rich_primary, width=20)
    table.add_column("Status", width=12)
    table.add_column("Details & Fix Hints", style="white")

    # Python
    if env_status["python_ok"]:
        table.add_row(
            "Python Runtime",
            f"[{cur_theme.rich_success}]● PASS[/{cur_theme.rich_success}]",
            f"v{env_status['python_version']} (>= 3.10 required)",
        )
    else:
        table.add_row(
            "Python Runtime",
            f"[{cur_theme.rich_danger}]✖ FAIL[/{cur_theme.rich_danger}]",
            f"v{env_status['python_version']} -> Fix: Install Python >= 3.10",
        )

    # Git
    if env_status["git_ok"]:
        table.add_row(
            "Git Version Control",
            f"[{cur_theme.rich_success}]● PASS[/{cur_theme.rich_success}]",
            f"v{env_status['git_version']}",
        )
    else:
        table.add_row(
            "Git Version Control",
            f"[{cur_theme.rich_danger}]✖ FAIL[/{cur_theme.rich_danger}]",
            "Git not found -> Fix: Install Git from https://git-scm.com",
        )

    # Ollama
    if env_status["ollama_ok"]:
        if env_status["has_coder_model"]:
            models_preview = ", ".join(env_status["ollama_models"][:3])
            table.add_row(
                "Local Ollama",
                f"[{cur_theme.rich_success}]● PASS[/{cur_theme.rich_success}]",
                f"Reachable at {env_status['ollama_url']} ({models_preview})",
            )
        else:
            table.add_row(
                "Local Ollama",
                f"[{cur_theme.rich_warning}]▲ WARN[/{cur_theme.rich_warning}]",
                "Daemon online, but qwen2.5-coder:7b missing -> Fix: ollama pull qwen2.5-coder:7b (~4.7 GB)",
            )
    else:
        table.add_row(
            "Local Ollama",
            f"[{cur_theme.rich_primary}]○ INFO[/{cur_theme.rich_primary}]",
            f"Not reachable at {env_status['ollama_url']} -> Optional: ollama serve or install from https://ollama.com",
        )

    console.print(table)
    console.print()


def execute_demo_mission(
    chosen_provider: str,
    demo_dir: Path,
) -> tuple[bool, dict[str, Any], float]:
    """Execute the 60-second reverse_words demo mission in ~/.octoflow/demo."""
    from octoflow.conductor import SupraesophagealConductor
    from octoflow.config import OctoFlowConfig

    # Ensure clean demo directory
    if demo_dir.exists():
        shutil.rmtree(demo_dir, ignore_errors=True)
    demo_dir.mkdir(parents=True, exist_ok=True)

    demo_budget = RunBudget(
        max_tokens=8_000,
        max_llm_calls=6,
        max_wall_seconds=60,
        max_heal_iterations=1,
        max_files_written=3,
    )

    cfg = OctoFlowConfig(
        model_provider=chosen_provider,
        workspace_dir=str(demo_dir),
        budget=demo_budget,
        auto_git_checkpoint=False,
        enable_3d_telemetry=False,
        allow_mock=True,
        is_bench=True,
    )

    start_time = time.time()
    try:
        conductor = SupraesophagealConductor(config=cfg)
        result = conductor.run_swarm(
            objective="create a function that reverses words with a pytest test",
            max_cycles=1,
        )
        elapsed = time.time() - start_time
        outcome = result.get("outcome", "")
        success = outcome in ("complete", "partial") or len(result.get("files_written", [])) > 0
        return success, result, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        return False, {"error": str(e)}, elapsed


def run_guided_first_run(
    yes: bool = False,
    launch_cockpit_after: bool = False,
    ollama_url: str | None = None,
) -> bool:
    """Run the guided first-run onboarding wizard."""
    cur_theme = load_saved_theme()
    is_tty = sys.stdin.isatty()
    is_noninteractive = (
        yes
        or (not is_tty)
        or (os.getenv("OCTOFLOW_NONINTERACTIVE") == "1")
    )

    # Welcome Banner
    banner_panel = Panel(
        f"[{cur_theme.rich_primary}]◈ Welcome to OctoFlow: Guided First Run[/{cur_theme.rich_primary}]\n"
        "[dim]Setting up your environment, selecting an LLM engine, and validating a 60s demo.[/dim]",
        border_style=cur_theme.rich_border,
    )
    console.print(banner_panel)
    console.print()

    # Step 1: Environment check
    env_status = check_environment(ollama_url=ollama_url)
    display_env_summary(env_status)

    # Step 2: Choose engine (Question 1)
    chosen_provider = "mock"
    chosen_model: str | None = None

    if is_noninteractive:
        if env_status["ollama_ok"] and (env_status["has_coder_model"] or len(env_status["ollama_models"]) > 0):
            chosen_provider = "ollama"
            chosen_model = env_status["ollama_models"][0] if env_status["ollama_models"] else "qwen2.5-coder:7b"
            console.print(f"[{cur_theme.rich_success}]● Non-interactive mode: Local Ollama detected and selected ({chosen_model}).[/{cur_theme.rich_success}]")
        else:
            chosen_provider = "mock"
            console.print(f"[{cur_theme.rich_primary}]● Non-interactive mode: Selecting dry-run demo (zero dependencies, 100% free).[/{cur_theme.rich_primary}]")
    else:
        # Interactive engine selection
        engine_table = Table(
            title="Step 1/3: Choose LLM Neural Engine",
            border_style=cur_theme.rich_border,
            expand=True,
        )
        engine_table.add_column("#", width=4, justify="center", style=cur_theme.rich_primary)
        engine_table.add_column("Engine Option", width=26, style="bold white")
        engine_table.add_column("Details & Privacy", style="white")

        engine_table.add_row(
            "1",
            "Local Ollama (Recommended)",
            "100% Free, private, runs on-device (qwen2.5-coder:7b)",
        )
        engine_table.add_row(
            "2",
            "Cloud API Key",
            "State-of-the-art frontier models (Anthropic, OpenAI, Gemini)",
        )
        engine_table.add_row(
            "3",
            "Dry-Run Demo",
            "Zero cost, zero API keys, simulated cephalopod active inference",
        )
        console.print(engine_table)

        default_opt = "1" if (env_status["ollama_ok"] and env_status["has_coder_model"]) else "3"
        prompt_msg = f"Select engine [1-3] (default {default_opt}): "
        choice = Prompt.ask(prompt_msg, choices=["1", "2", "3"], default=default_opt)

        if choice == "1":
            if not env_status["ollama_ok"]:
                console.print(f"[{cur_theme.rich_warning}]▲ Ollama daemon not reachable at {env_status['ollama_url']}.[/{cur_theme.rich_warning}]")
                console.print("  Fix: Install from [bold]https://ollama.com[/bold] and run [bold]ollama serve[/bold]")
                console.print("  Model command: [bold]ollama pull qwen2.5-coder:7b[/bold] (~4.7 GB)\n")
                console.print("[dim]Falling back to dry-run demo for this first run.[/dim]\n")
                chosen_provider = "mock"
            elif not env_status["has_coder_model"]:
                console.print(f"[{cur_theme.rich_warning}]▲ Ollama is running, but no coder model was found.[/{cur_theme.rich_warning}]")
                console.print("  Download command: [bold]ollama pull qwen2.5-coder:7b[/bold] (approx. ~4.7 GB)\n")
                console.print("[dim]Falling back to dry-run demo for this first run.[/dim]\n")
                chosen_provider = "mock"
            else:
                chosen_provider = "ollama"
                chosen_model = env_status["ollama_models"][0] if env_status["ollama_models"] else "qwen2.5-coder:7b"
                console.print(f"[{cur_theme.rich_success}]✔ Local Ollama selected ({chosen_model}).[/{cur_theme.rich_success}]\n")

        elif choice == "2":
            p_sub = Prompt.ask("Choose provider [1: Anthropic Claude, 2: OpenAI, 3: Google Gemini] (default 1): ", choices=["1", "2", "3"], default="1")
            p_map = {"1": "anthropic", "2": "openai", "3": "gemini"}
            prov_name = p_map.get(p_sub, "anthropic")
            key_entered = getpass.getpass(f"Paste {prov_name.upper()} API Key (press Enter to set via env var later): ").strip()

            if key_entered:
                if is_keyring_available():
                    use_keyring = Confirm.ask("Store API key securely in OS Keyring?", default=True)
                    if use_keyring:
                        set_keyring_key(prov_name, key_entered)
                        console.print(f"[{cur_theme.rich_success}]✔ Stored key in OS Keyring.[/{cur_theme.rich_success}]")
                    else:
                        existing = load_secure_config()
                        existing[f"{prov_name}_api_key"] = key_entered
                        save_secure_config(existing)
                        console.print(f"[{cur_theme.rich_warning}]▲ Stored key in ~/.octoflow/config.json (mode 0600).[/{cur_theme.rich_warning}]")
                else:
                    existing = load_secure_config()
                    existing[f"{prov_name}_api_key"] = key_entered
                    save_secure_config(existing)
                    console.print(f"[{cur_theme.rich_warning}]▲ Stored key in ~/.octoflow/config.json (mode 0600).[/{cur_theme.rich_warning}]")
                chosen_provider = prov_name
            else:
                console.print(f"[dim]Tip: You can export your key anytime via: export {prov_name.upper()}_API_KEY=\"...\"[/dim]")
                console.print("[dim]Using dry-run demo for this first run.[/dim]\n")
                chosen_provider = "mock"

        else:
            chosen_provider = "mock"
            console.print("[dim]Selected Dry-Run Demo: 100% simulated active-inference, zero dependencies.[/dim]\n")

    # Step 3: Run Demo Task (Question 2)
    demo_dir = get_octoflow_dir() / "demo"

    if not is_noninteractive:
        run_demo = Confirm.ask("Step 2/3: Ready to run 60-second reverse_words demo?", default=True)
        if not run_demo:
            console.print("[dim]Skipping demo task execution.[/dim]\n")
            _finish_onboarding(chosen_provider, chosen_model, is_noninteractive, launch_cockpit_after)
            return True

    console.print(f"\n[{cur_theme.rich_primary}]◈ Deploying 8-Arm Swarm in ~/.octoflow/demo...[/{cur_theme.rich_primary}]")
    console.print("[dim]Goal: 'create a function that reverses words with a pytest test'[/dim]\n")

    success, result, elapsed = execute_demo_mission(chosen_provider, demo_dir)

    # Failure handling path
    if not success and chosen_provider != "mock":
        console.print(f"[{cur_theme.rich_danger}]✖ Demo task failed using '{chosen_provider}' ({result.get('error') or result.get('reason')}).[/{cur_theme.rich_danger}]")
        console.print(f"  Log file: [bold]{get_log_file_path()}[/bold]")
        if not is_noninteractive:
            retry_mock = Confirm.ask("Would you like to fallback and verify in safe dry-run mode?", default=True)
            if retry_mock:
                chosen_provider = "mock"
                success, result, elapsed = execute_demo_mission(chosen_provider, demo_dir)

    # Display Demo Outcome Ribbon
    if success:
        files = result.get("files_written", [])
        tokens_used = result.get("tokens_consumed", 0)
        savings = result.get("token_reduction_pct", 0.0)
        cost = result.get("total_cost_dollars", 0.0)

        console.print(f"[{cur_theme.rich_success}]✔ OCTOFLOW FIRST-RUN DEMO COMPLETE ({elapsed:.2f}s)[/{cur_theme.rich_success}]")
        console.print(f"  • Files Created in {demo_dir}:")
        if files:
            for f in files:
                console.print(f"    - {f}")
        else:
            # Check directory directly
            for p in demo_dir.glob("*.py"):
                console.print(f"    - {p.name}")
        console.print(f"  • Token Ledger: {tokens_used:,} tokens (Saved {savings:.1f}% vs baseline)")
        if cost > 0:
            console.print(f"  • Estimated Cost: ${cost:.4f}")
        console.print()
    else:
        console.print(f"[{cur_theme.rich_warning}]▲ Demo finished with notice: {result.get('reason', 'incomplete')}. Log: {get_log_file_path()}[/{cur_theme.rich_warning}]\n")

    # Step 4: Save onboarding_completed & defaults, Question 3 (Visualizer)
    _finish_onboarding(chosen_provider, chosen_model, is_noninteractive, launch_cockpit_after)
    return True


def _finish_onboarding(
    chosen_provider: str,
    chosen_model: str | None,
    is_noninteractive: bool,
    launch_cockpit_after: bool,
) -> None:
    """Save onboarding completed flag, chosen defaults, and prompt for visualizer."""
    cur_theme = load_saved_theme()
    cfg_file = get_default_config_path()
    cfg_data = load_secure_config(cfg_file) or {}

    cfg_data["onboarding_completed"] = True
    cfg_data["default_provider"] = chosen_provider
    if chosen_model:
        cfg_data["default_model"] = chosen_model

    save_secure_config(cfg_data, cfg_file)
    console.print(f"[{cur_theme.rich_success}]✔ Configuration saved: onboarding completed![/{cur_theme.rich_success}]\n")

    # Question 3: Visualizer
    if not is_noninteractive:
        open_viz = Confirm.ask("Step 3/3: Open 3D Visualizer on http://localhost:8088?", default=False)
        if open_viz:
            console.print(f"[{cur_theme.rich_accent}]● 3D Visualizer URL: [bold underline]http://localhost:8088[/bold underline][/{cur_theme.rich_accent}]")
            try:
                import webbrowser
                webbrowser.open("http://localhost:8088")
            except Exception:
                pass

    if launch_cockpit_after:
        from octoflow.cockpit import interactive_cockpit
        console.print("[dim]Transitioning into interactive cephalopod cockpit...[/dim]\n")
        interactive_cockpit()


def first_run_cli_cmd(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Run non-interactively picking Ollama if available else dry-run"
    ),
):
    """Run the guided first-run onboarding wizard."""
    run_guided_first_run(yes=yes, launch_cockpit_after=False)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register first-run command with Typer CLI apps."""
    app.command("first-run")(first_run_cli_cmd)
    octos_app.command("first-run")(first_run_cli_cmd)
