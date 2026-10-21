"""Heal and Fix CLI command for autonomous closed-loop test repair."""

import typer
from rich.console import Console
from rich.table import Table
from octoflow.themes import load_saved_theme

console = Console()


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


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register heal and fix commands with Typer apps."""
    app.command("fix")(heal_cli_cmd)
    octos_app.command("fix")(heal_cli_cmd)
    app.command("heal")(heal_cli_cmd)
    octos_app.command("heal")(heal_cli_cmd)
