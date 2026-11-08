"""Init CLI command for auto-configuring IDE surfaces and GitHub Actions."""

import typer
from rich.console import Console
from rich.table import Table

from octoflow.themes import load_saved_theme

console = Console()


def init_ide_cli_cmd(
    workspace: str = typer.Option(
        ".", "--dir", "-d", help="Project workspace directory to onboard"
    ),
):
    """Auto-configure Cursor (.cursorrules), Claude (MCP), VS Code (tasks), and Git (hooks)."""
    from octoflow.onboarding import onboard_ide

    theme = load_saved_theme()
    console.print(
        f"\n[{theme.rich_primary}]◈ Auto-Onboarding Omni-IDE Surfaces for Workspace:[/{theme.rich_primary}] [bold white]{workspace}[/bold white]\n"
    )
    res = onboard_ide(workspace=workspace)

    t = Table(
        title="Omni-IDE Developer Surface Status", border_style=theme.rich_border, expand=True
    )
    t.add_column("Developer Surface", style="bold white", width=28)
    t.add_column("Status", width=14)
    t.add_column("Configuration Details", style="white")

    t.add_row(
        "Cursor AI (.cursorrules)",
        f"[{theme.rich_success}]✔ CONFIGURED[/]" if res["cursor"] else "[dim]SKIPPED[/]",
        "8-Arm Swarm delegation rules & architecture heuristics",
    )
    t.add_row(
        "Claude Code CLI (~/.claude.json)",
        f"[{theme.rich_success}]✔ INJECTED[/]" if res["claude_code"] else "[dim]SKIPPED[/]",
        "Direct MCP connection for multi-file swarm execution",
    )
    t.add_row(
        "Claude Desktop App",
        f"[{theme.rich_success}]✔ INJECTED[/]" if res["claude_desktop"] else "[dim]NOT FOUND[/]",
        "Desktop UI connectome MCP tool integration",
    )
    t.add_row(
        "VS Code (.vscode/tasks.json)",
        f"[{theme.rich_success}]✔ CONFIGURED[/]" if res["vscode_tasks"] else "[dim]SKIPPED[/]",
        "4 Command Palette shortcut tasks (Cockpit, Guard, UI, Doctor)",
    )
    t.add_row(
        "Git Pre-Commit Hook",
        f"[{theme.rich_success}]✔ INSTALLED[/]" if res["git_hooks"] else "[dim]SKIPPED[/]",
        "Swarm Guard AST validation & secret leak protection",
    )

    console.print(t)
    console.print(
        f"[{theme.rich_success}]✔ Omni-IDE onboarding completed in <1s. Zero manual configuration required![/{theme.rich_success}]\n"
    )


def init_action_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace directory"),
):
    """Generate automated OctoFlow Swarm Guard GitHub Action (.github/workflows/octoflow-guard.yml)."""
    from octoflow.ci import generate_github_action_workflow

    theme = load_saved_theme()
    wf_path = generate_github_action_workflow(workspace)
    console.print(
        f"\n[{theme.rich_success}]✔ Generated GitHub Actions Workflow:[/{theme.rich_success}] [bold white]{wf_path}[/bold white]"
    )
    console.print(
        "[dim]Every Pull Request will now automatically trigger Arm 6 (Security), Arm 5 (QA/AST), and Arm 0 (Architect) audits.[/dim]\n"
    )


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register init commands with Typer apps."""
    app.command("init")(init_ide_cli_cmd)
    app.command("init-ide")(init_ide_cli_cmd)
    octos_app.command("init")(init_ide_cli_cmd)
    octos_app.command("init-ide")(init_ide_cli_cmd)

    app.command("init-action")(init_action_cli_cmd)
    octos_app.command("init-action")(init_action_cli_cmd)
