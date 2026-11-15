"""MCP and MCP-Serve CLI commands for Model Context Protocol integration."""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from octoflow.onboarding import CURSOR_RULES_TEMPLATE, _merge_json_safely
from octoflow.themes import load_saved_theme

console = Console()


def install_mcp(
    workspace: str = ".",
    client: str = "claude-code",
    quiet: bool = False,
) -> dict[str, Any]:
    """Install and configure OctoFlow MCP server for Claude Code, Cursor, or Claude Desktop."""
    theme = load_saved_theme()
    ws_path = Path(workspace).resolve()
    cmd = "octos" if "octos" in sys.argv[0] else "octoflow"
    results: dict[str, Any] = {
        "claude_code": False,
        "workspace_mcp": False,
        "claude_desktop": False,
        "cursor": False,
        "configured_paths": [],
    }

    mcp_server_entry = {
        "command": cmd,
        "args": ["mcp"],
    }
    mcp_payload = {"mcpServers": {"octoflow": mcp_server_entry}}

    target = client.lower().strip()

    # 1. Claude Code CLI (~/.claude.json and workspace .mcp.json)
    if target in ("claude-code", "claude", "all"):
        # Global ~/.claude.json
        try:
            claude_home_cfg = Path.home() / ".claude.json"
            if _merge_json_safely(claude_home_cfg, mcp_payload, key_merger="mcpServers"):
                results["claude_code"] = True
                results["configured_paths"].append(str(claude_home_cfg))
        except Exception as e:
            if not quiet:
                console.print(f"[dim]Warning: Failed updating ~/.claude.json: {e}[/dim]")

        # Workspace-level .mcp.json
        try:
            ws_mcp = ws_path / ".mcp.json"
            if _merge_json_safely(ws_mcp, mcp_payload, key_merger="mcpServers"):
                results["workspace_mcp"] = True
                results["configured_paths"].append(str(ws_mcp))
        except Exception as e:
            if not quiet:
                console.print(f"[dim]Warning: Failed updating .mcp.json: {e}[/dim]")

        # Plugin manifest (.claude-plugin/plugin.json)
        try:
            plugin_dir = ws_path / ".claude-plugin"
            plugin_dir.mkdir(parents=True, exist_ok=True)
            manifest = plugin_dir / "plugin.json"
            manifest_data = {
                "name": "octoflow",
                "version": "0.2.0",
                "description": "OctoFlow Cephalopod Multi-Agent Coding Swarm with 64 Personas & RAG",
                "mcp": {
                    "command": cmd,
                    "args": ["mcp"],
                },
            }
            manifest.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
            results["configured_paths"].append(str(manifest))
        except Exception:
            pass

    # 2. Claude Desktop App
    if target in ("claude-desktop", "desktop", "all"):
        try:
            sys_name = platform.system()
            desktop_conf = None
            if sys_name == "Darwin":
                desktop_conf = (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Claude"
                    / "claude_desktop_config.json"
                )
            elif sys_name == "Windows":
                appdata = os.getenv("APPDATA")
                if appdata:
                    desktop_conf = Path(appdata) / "Claude" / "claude_desktop_config.json"
            else:
                desktop_conf = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

            if desktop_conf and _merge_json_safely(desktop_conf, mcp_payload, key_merger="mcpServers"):
                results["claude_desktop"] = True
                results["configured_paths"].append(str(desktop_conf))
        except Exception as e:
            if not quiet:
                console.print(f"[dim]Warning: Failed updating Claude Desktop config: {e}[/dim]")

    # 3. Cursor AI
    if target in ("cursor", "all"):
        try:
            cursor_file = ws_path / ".cursorrules"
            if not cursor_file.exists():
                cursor_file.write_text(CURSOR_RULES_TEMPLATE.strip() + "\n", encoding="utf-8")
                results["cursor"] = True
                results["configured_paths"].append(str(cursor_file))
            else:
                txt = cursor_file.read_text(encoding="utf-8")
                if "OctoFlow Cephalopod Swarm" not in txt:
                    cursor_file.write_text(
                        txt.rstrip() + "\n\n" + CURSOR_RULES_TEMPLATE.strip() + "\n",
                        encoding="utf-8",
                    )
                results["cursor"] = True
                results["configured_paths"].append(str(cursor_file))
        except Exception as e:
            if not quiet:
                console.print(f"[dim]Warning: Failed updating .cursorrules: {e}[/dim]")

    if not quiet:
        console.print()
        t = Table(title="OctoFlow Model Context Protocol (MCP) Integration", border_style=theme.rich_border)
        t.add_column("Client / Target", style="bold cyan")
        t.add_column("Status", style="bold green")
        t.add_column("Configuration Path", style="dim")

        if target in ("claude-code", "claude", "all"):
            t.add_row(
                "Claude Code (Global)",
                f"[{theme.rich_success}]✔ CONFIGURED[/]" if results["claude_code"] else "[dim]SKIPPED[/]",
                str(Path.home() / ".claude.json"),
            )
            t.add_row(
                "Claude Code (Project)",
                f"[{theme.rich_success}]✔ CONFIGURED[/]" if results["workspace_mcp"] else "[dim]SKIPPED[/]",
                str(ws_path / ".mcp.json"),
            )
        if target in ("claude-desktop", "desktop", "all"):
            t.add_row(
                "Claude Desktop",
                f"[{theme.rich_success}]✔ CONFIGURED[/]" if results["claude_desktop"] else "[dim]SKIPPED[/]",
                "claude_desktop_config.json",
            )
        if target in ("cursor", "all"):
            t.add_row(
                "Cursor AI",
                f"[{theme.rich_success}]✔ CONFIGURED[/]" if results["cursor"] else "[dim]SKIPPED[/]",
                str(ws_path / ".cursorrules"),
            )
        console.print(t)

        console.print(
            Panel(
                f"[{theme.rich_success}]✔ OctoFlow MCP Server Ready for {target.upper()}![/{theme.rich_success}]\n\n"
                f"  • Registered Tools: [bold white]12 Canonical Tools[/bold white] (Swarm, RAG, AST, 64 Personas)\n"
                f"  • Semantic Codebase Search: [bold cyan]octoflow_search_codebase[/bold cyan]\n"
                f"  • AST Connectome: [bold cyan]octoflow_search_symbols[/bold cyan], [bold cyan]octoflow_find_callers[/bold cyan]\n"
                f"  • Guild Switcher: [bold cyan]octoflow_switch_guild[/bold cyan] (64 Personas across 8 domains)\n"
                f"  • Stdio Command: [bold white]{cmd} mcp[/bold white]\n\n"
                f"Inside Claude Code, invoke:\n"
                f"  [bold white]/octo[/bold white]         - Launch Cephalopod Cockpit\n"
                f"  [bold white]/octo:audit[/bold white]   - Run 1-100 System Readiness Grade\n"
                f"  [bold white]/octo:swarm[/bold white]   - Deploy Swarm Consortium",
                title="[bold cyan]Claude Code MCP Suite[/bold cyan]",
                border_style=theme.rich_border,
                padding=(1, 2),
            )
        )

    return results


def mcp_serve(workspace: str = typer.Option(".", "--dir", "-d", help="Workspace directory")):
    """Run OctoFlow as a Model Context Protocol (MCP) server for Claude Code and Cursor."""
    import asyncio

    from octoflow.mcp import OctoFlowMCPServer

    server = OctoFlowMCPServer(workspace_dir=workspace)
    asyncio.run(server.run_stdio())


def mcp_cli_cmd(
    ctx: typer.Context,
    workspace: str = typer.Option(
        ".", "--dir", "-d", help="Workspace directory for the MCP server"
    ),
):
    """Start OctoFlow as a Model Context Protocol (MCP) JSON-RPC 2.0 stdio server for Claude Code and Cursor."""
    raw_args = list(ctx.args or [])
    if raw_args and raw_args[0] == "install":
        client = "claude-code"
        ws = workspace
        idx = 1
        while idx < len(raw_args):
            arg = raw_args[idx]
            if arg in ("--client", "-c") and idx + 1 < len(raw_args):
                client = raw_args[idx + 1]
                idx += 2
            elif arg.startswith("--client="):
                client = arg.split("=", 1)[1]
                idx += 1
            elif arg in ("--dir", "-d") and idx + 1 < len(raw_args):
                ws = raw_args[idx + 1]
                idx += 2
            elif arg.startswith("--dir="):
                ws = arg.split("=", 1)[1]
                idx += 1
            else:
                idx += 1
        install_mcp(workspace=ws, client=client)
        return

    import asyncio

    from octoflow.mcp import OctoFlowMCPServer

    server = OctoFlowMCPServer(workspace_dir=workspace)
    try:
        asyncio.run(server.run_stdio())
    except (KeyboardInterrupt, EOFError):
        pass


def register_mcp_serve(app: typer.Typer) -> None:
    """Register mcp-serve command with primary app."""
    app.command(name="mcp-serve")(mcp_serve)


def register_mcp(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register mcp command with both apps."""
    app.command("mcp", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(mcp_cli_cmd)
    octos_app.command("mcp", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(mcp_cli_cmd)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register mcp and mcp-serve commands with Typer apps."""
    register_mcp_serve(app)
    register_mcp(app, octos_app)
