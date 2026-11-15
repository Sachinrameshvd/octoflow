"""Install-Claude CLI command to register native Claude Code plugin and slash commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


def install_claude_cli_cmd():
    """Install and register OctoFlow native Claude Code plugin and slash commands (/octo)."""
    from octoflow.commands.mcp import install_mcp

    install_mcp(workspace=".", client="claude-code")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register install-claude command with Typer apps."""
    app.command("install-claude")(install_claude_cli_cmd)
    octos_app.command("install-claude")(install_claude_cli_cmd)
