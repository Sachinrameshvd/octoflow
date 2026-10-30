"""Setup CLI command for interactive first-run configuration wizard."""

import getpass
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from octoflow.cockpit import get_live_wizard_input, interactive_cockpit
from octoflow.config import (
    get_octoflow_dir,
    load_secure_config,
    mask_credential,
    save_secure_config,
)
from octoflow.themes import load_saved_theme, save_theme_preference

console = Console()


def run_setup_wizard(launch_after: bool = False):
    """Guided first-run configuration wizard for API keys, model, and theme."""
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

    table = Table(
        title="◈ Supported LLM Neural Engines", border_style=cur_theme.rich_border, expand=True
    )
    table.add_column("#", width=4, justify="center", style=cur_theme.rich_primary)
    table.add_column("Provider", width=22, style="bold white")
    table.add_column("Recommended Model", width=24, style=cur_theme.rich_secondary)
    table.add_column("Best Suited For", style="white")

    table.add_row(
        "1",
        Text("[Anthropic Claude]"),
        "claude-3-5-sonnet",
        "State-of-the-art coding & autonomous reasoning",
    )
    table.add_row(
        "2", Text("[OpenAI]"), "gpt-4o / o3-mini", "High speed, broad tool calling & code synthesis"
    )
    table.add_row(
        "3",
        Text("[Google Gemini]"),
        "gemini-2.0-flash",
        "Massive context window & rapid code generation",
    )
    table.add_row(
        "4", Text("[xAI Grok]"), "grok-2", "Low-latency inference & mathematical reasoning"
    )
    table.add_row(
        "5",
        Text("[DeepSeek]"),
        "deepseek-chat (V3/R1)",
        "High-performance coding at economical cost",
    )
    table.add_row(
        "6",
        Text("[Local Ollama]"),
        "qwen2.5-coder / llama3",
        "100% Free, offline & private on local Mac",
    )
    table.add_row(
        "7", Text("[Mock Mode]"), "deterministic-mock", "Offline test harness (zero cost, dry run)"
    )

    step1_heading = Text("\nStep 1: Choose Primary LLM Core Provider", style="bold white")

    # Live animated input for provider selection
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
    step2_heading = Text(
        f"\nStep 1 Selected: [{prov_name}]\nStep 2: Enter API Key or Endpoint (optional - press Enter to skip)\n",
        style="bold white",
    )

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
        env_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or existing_cfg.get("gemini_api_key", "")
        )
        saved_key = _prompt_secret_key("GEMINI_API_KEY", env_key)
        if saved_key:
            existing_cfg["gemini_api_key"] = saved_key
            os.environ["GEMINI_API_KEY"] = saved_key

    elif chosen_provider == "grok":
        env_key = (
            os.getenv("XAI_API_KEY")
            or os.getenv("GROK_API_KEY")
            or existing_cfg.get("grok_api_key", "")
        )
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
        "ollama": (
            "Local Ollama",
            "qwen2.5-coder:32b",
            existing_cfg.get("ollama_base_url", "http://localhost:11434"),
        ),
    }
    if chosen_provider in entry_defs:
        p_name, p_model, p_url = entry_defs[chosen_provider]
        pool_idx = next(
            (i for i, e in enumerate(pool) if e.get("provider") == chosen_provider), None
        )
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
    theme_map = {
        "1": "abyssal",
        "2": "catppuccin",
        "3": "tokyo-night",
        "4": "dracula",
        "5": "nord",
        "6": "minimalist",
    }
    new_theme_id = theme_map.get(theme_choice, "catppuccin")
    save_theme_preference(new_theme_id)
    existing_cfg["default_theme"] = new_theme_id

    # Save to ~/.octoflow/config.json with 0600 mode
    save_secure_config(existing_cfg, cfg_file)

    console.clear()
    console.print(
        f"\n[{cur_theme.rich_success}]◈ Configuration saved successfully to ~/.octoflow/config.json![/{cur_theme.rich_success}]"
    )
    console.print(f"  • Provider: [bold]{chosen_provider.upper()}[/bold]")
    console.print(f"  • Theme: [bold]{new_theme_id}[/bold]")
    console.print("[dim]Transitioning into live cephalopod console...[/dim]\n")

    if launch_after:
        interactive_cockpit()


def setup_cli_cmd():
    """Launch the interactive OctoFlow Setup Wizard."""
    run_setup_wizard(launch_after=True)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register setup command with Typer apps."""
    app.command("setup")(setup_cli_cmd)
    octos_app.command("setup")(setup_cli_cmd)
