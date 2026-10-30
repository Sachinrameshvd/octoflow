"""Install-Claude CLI command to register native Claude Code plugin and slash commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


def install_claude_cli_cmd():
    """Install and register OctoFlow native Claude Code plugin and slash commands (/octo)."""
    from octoflow.themes import load_saved_theme

    theme = load_saved_theme()
    plugin_dir = Path(".claude-plugin")
    plugin_dir.mkdir(parents=True, exist_ok=True)
    console.print(
        Panel(
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
            padding=(1, 2),
        )
    )


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register install-claude command with Typer apps."""
    app.command("install-claude")(install_claude_cli_cmd)
    octos_app.command("install-claude")(install_claude_cli_cmd)
