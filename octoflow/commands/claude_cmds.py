"""Claude Code CLI commands for 8-Arm SPARC execution and CLAUDE.md management."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from octoflow.claude_bridge import (
    compile_sparc_prompt,
    copy_to_clipboard,
    execute_claude_cli,
    generate_claude_md,
    get_claude_status,
)
from octoflow.commands.mcp import install_mcp
from octoflow.themes import load_saved_theme

console = Console()

claude_app = typer.Typer(
    name="claude",
    help="Direct Claude Code CLI integration, 8-Arm SPARC prompt runner, and CLAUDE.md sync.",
    no_args_is_help=True,
)


@claude_app.command("init")
def claude_init_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing CLAUDE.md completely"
    ),
) -> None:
    """Generate or update CLAUDE.md and register OctoFlow MCP server for Claude Code."""
    theme = load_saved_theme()
    ws = Path(workspace).resolve()

    console.print(
        f"\n[{theme.rich_primary}]◈ Initializing OctoFlow Cephalopod Protocol for Claude Code:[/{theme.rich_primary}] [bold white]{ws}[/bold white]\n"
    )

    # 1. Generate / sync CLAUDE.md
    target_md, modified = generate_claude_md(workspace=ws, force=force)

    # 2. Register MCP server in Claude Code
    mcp_res = install_mcp(workspace=str(ws), client="claude-code", quiet=True)

    t = Table(title="Claude Code Integration Status", border_style=theme.rich_border, expand=True)
    t.add_column("Surface", style="bold white", width=28)
    t.add_column("Status", width=14)
    t.add_column("Details", style="white")

    md_status = (
        f"[{theme.rich_success}]✓ CONFIGURED[/]"
        if modified
        else f"[{theme.rich_primary}]✓ SYNCHRONIZED[/]"
    )
    t.add_row(
        "CLAUDE.md Blueprint",
        md_status,
        f"{target_md.name} (8-Arm Neuro-Specialist Roster & Sensory Gating)",
    )

    claude_code_ok = mcp_res.get("claude_code", False) or mcp_res.get("workspace_mcp", False)
    mcp_status = (
        f"[{theme.rich_success}]✓ INJECTED[/]" if claude_code_ok else "[dim]SKIPPED[/]"
    )
    t.add_row(
        "Claude Code MCP Server",
        mcp_status,
        "Connected to octos mcp for multi-octopus tool execution",
    )

    console.print(t)
    console.print(
        f"\n[{theme.rich_success}]✓ Ready. Anthropic's Claude Code CLI (`claude`) will now automatically operate under OctoFlow 8-Arm SPARC discipline.[/{theme.rich_success}]\n"
    )


@claude_app.command("run")
def claude_run_cmd(
    goal: str = typer.Argument(..., help="Engineering or feature goal to execute with Claude Code"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    print_mode: bool = typer.Option(
        False, "--print", "-p", help="Run Claude in non-interactive print mode (for pipes/scripts)"
    ),
    dangerously_skip_permissions: bool = typer.Option(
        False, "--dangerously-skip-permissions", help="Bypass permission prompts (sandboxed)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Display the compiled command and prompt without executing"
    ),
) -> None:
    """Run official Claude Code CLI with the compiled OctoFlow 8-Arm SPARC prompt."""
    theme = load_saved_theme()
    ws = Path(workspace).resolve()

    # Ensure CLAUDE.md exists
    generate_claude_md(workspace=ws, force=False)

    status = get_claude_status(workspace=ws)
    if not status["claude_installed"]:
        console.print(
            "\n[bold yellow]▲ Claude Code CLI (`claude`) not detected in PATH.[/bold yellow]"
        )
        console.print(
            "[dim]Install it via:[/dim] [bold white]npm install -g @anthropic-ai/claude-code[/bold white]\n"
        )
        console.print(
            Panel(
                compile_sparc_prompt(goal, workspace=ws),
                title="[bold cyan]Compiled 8-Arm SPARC Prompt (Ready to Copy)[/bold cyan]",
                border_style=theme.rich_border,
            )
        )
        return

    if dry_run:
        prompt = compile_sparc_prompt(goal, workspace=ws)
        console.print(f"[{theme.rich_primary}]◈ [DRY-RUN] Executable:[/{theme.rich_primary}] [bold white]{status['claude_path']}[/bold white]")
        cmd_preview = f"claude {'-p ' if print_mode else ''}{'--dangerously-skip-permissions ' if dangerously_skip_permissions else ''}<PROMPT>"
        console.print(f"[{theme.rich_primary}]◈ [DRY-RUN] Command:[/{theme.rich_primary}] [dim]{cmd_preview}[/dim]\n")
        console.print(
            Panel(
                prompt,
                title="[bold cyan]8-Arm SPARC Prompt Preview[/bold cyan]",
                border_style=theme.rich_border,
            )
        )
        return

    if not print_mode:
        console.print(
            f"[{theme.rich_primary}]◈ Launching Claude Code CLI with 8-Arm SPARC Directive...[/{theme.rich_primary}]\n"
        )

    code = execute_claude_cli(
        goal=goal,
        print_mode=print_mode,
        dangerously_skip_permissions=dangerously_skip_permissions,
        dry_run=False,
        workspace=ws,
    )
    if code != 0:
        raise typer.Exit(code=code)


@claude_app.command("prompt")
def claude_prompt_cmd(
    goal: str = typer.Argument(..., help="Engineering goal to compile into an 8-Arm SPARC directive"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    copy: bool = typer.Option(
        False, "--copy", "-c", help="Copy the compiled prompt to system clipboard"
    ),
    raw: bool = typer.Option(
        False, "--raw", "-r", help="Print raw prompt without rich styling (ideal for unix pipes)"
    ),
) -> None:
    """Generate and display the compiled OctoFlow 8-Arm SPARC prompt for Claude."""
    theme = load_saved_theme()
    ws = Path(workspace).resolve()

    prompt = compile_sparc_prompt(goal, workspace=ws)

    if copy:
        copied = copy_to_clipboard(prompt)
        if copied:
            console.print(f"[{theme.rich_success}]✓ Copied 8-Arm SPARC prompt to clipboard.[/]\n")
        else:
            console.print("[dim]Note: Clipboard unavailable; outputting below.[/dim]\n")

    if raw:
        sys.stdout.write(prompt + "\n")
        sys.stdout.flush()
    else:
        console.print(
            Panel(
                prompt,
                title=f"[{theme.rich_primary}]OctoFlow 8-Arm SPARC Prompt Directive[/{theme.rich_primary}]",
                border_style=theme.rich_border,
            )
        )


@claude_app.command("status")
def claude_status_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
) -> None:
    """Inspect the status and health of the Claude Code integration."""
    theme = load_saved_theme()
    ws = Path(workspace).resolve()

    status = get_claude_status(workspace=ws)

    t = Table(title="OctoFlow ◈ Claude Code Integration Diagnostics", border_style=theme.rich_border, expand=True)
    t.add_column("Component", style="bold white", width=26)
    t.add_column("Health", width=14)
    t.add_column("Path / Details", style="white")

    if status["claude_installed"]:
        version_str = f" ({status['claude_version']})" if status["claude_version"] else ""
        t.add_row(
            "Claude Code CLI",
            f"[{theme.rich_success}]✓ INSTALLED[/]",
            f"{status['claude_path']}{version_str}",
        )
    else:
        t.add_row(
            "Claude Code CLI",
            "[bold yellow]○ NOT FOUND[/]",
            "npm install -g @anthropic-ai/claude-code",
        )

    if status["claude_md_exists"]:
        t.add_row(
            "CLAUDE.md Protocol",
            f"[{theme.rich_success}]✓ PRESENT[/]",
            status["claude_md_path"],
        )
    else:
        t.add_row(
            "CLAUDE.md Protocol",
            "[dim]○ MISSING[/]",
            "Run: octos claude init",
        )

    if status["mcp_configured"]:
        t.add_row(
            "OctoFlow MCP Server",
            f"[{theme.rich_success}]✓ CONNECTED[/]",
            ", ".join(status["mcp_paths"]),
        )
    else:
        t.add_row(
            "OctoFlow MCP Server",
            "[dim]○ NOT LINKED[/]",
            "Run: octos claude init",
        )

    console.print("\n", t, "\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register claude command group with Typer apps."""
    app.add_typer(claude_app, name="claude")
    octos_app.add_typer(claude_app, name="claude")
