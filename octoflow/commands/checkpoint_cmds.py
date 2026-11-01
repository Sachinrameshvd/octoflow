"""CLI commands for undoing runs and inspecting run provenance history."""

import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from octoflow.checkpoint import list_runs, undo_run

console = Console()


def undo_cli_cmd(
    run_id: str | None = typer.Argument(
        None, help="Specific run ID to undo (default: most recent run)"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt and proceed immediately"
    ),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
):
    """Undo an OctoFlow run: checkout original branch, discard run branch, and restore stash."""
    ws = Path(workspace).resolve()

    def _cli_confirm(prompt_text: str, diff_stat: str) -> bool:
        if diff_stat:
            console.print(
                Panel(diff_stat, title="[cyan]Changes to be Discarded[/cyan]", border_style="cyan")
            )
        console.print(f"[bold yellow]▲ {prompt_text}[/bold yellow]")
        return Confirm.ask(
            "Are you sure you want to discard this run branch and return to original branch?"
        )

    try:
        res = undo_run(
            workspace_dir=ws,
            run_id=run_id,
            confirm=not yes,
            interactive_confirm=_cli_confirm if not yes else None,
        )

        if res.get("status") == "SUCCESS":
            console.print(
                f"\n[bold green]✔ Cleanly undone OctoFlow run '{res['run_id']}'.[/bold green]"
            )
            console.print(
                f"● Switched back to original branch: [bold cyan]{res['original_branch']}[/bold cyan]"
            )
            console.print(f"● Deleted run branch: [dim]{res['deleted_branch']}[/dim]")
            if res.get("restored_stash"):
                console.print(
                    "● [bold green]✔ Restored uncommitted changes from stash snapshot.[/bold green]\n"
                )
            else:
                console.print("")
        elif res.get("status") == "CANCELLED":
            console.print("[dim]Undo operation cancelled by user.[/dim]\n")
    except ValueError as ve:
        console.print(f"\n✖ [bold red][UNDO ERROR] {ve}[/bold red]\n")
        raise typer.Exit(code=1) from ve
    except Exception as e:
        console.print(f"\n✖ [bold red][FAILED] {e}[/bold red]\n")
        raise typer.Exit(code=2) from e


def runs_cli_cmd(
    workspace: str | None = typer.Option(
        None, "--dir", "-d", help="Filter runs by workspace folder"
    ),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of runs to display"),
):
    """List recent OctoFlow execution runs and their git provenance status."""
    ws = Path(workspace).resolve() if workspace else None
    runs = list_runs(workspace_dir=ws, limit=limit)

    if not runs:
        from octoflow.messages import format_empty_state

        console.print(f"\n{format_empty_state('no_runs')}\n")
        return

    table = Table(title="◈ OctoFlow Run Provenance Ledger", border_style="cyan")
    table.add_column("Run ID", style="bold cyan", no_wrap=True)
    table.add_column("Status", style="bold", no_wrap=True)
    table.add_column("Goal", style="white")
    table.add_column("Mode", style="dim", no_wrap=True)
    table.add_column("Branch", style="dim")
    table.add_column("Created", style="dim", no_wrap=True)

    for m in runs:
        dt = datetime.datetime.fromtimestamp(m.created_at).strftime("%Y-%m-%d %H:%M:%S")
        status_color = (
            "green"
            if m.status == "COMPLETED"
            else ("yellow" if m.status in ("WIP", "RUNNING") else "magenta")
        )
        status_str = f"[{status_color}]{m.status}[/{status_color}]"
        goal_snippet = m.goal.replace("\n", " ")[:45] + ("..." if len(m.goal) > 45 else "")
        table.add_row(
            m.run_id,
            status_str,
            goal_snippet,
            m.mode,
            m.run_branch or "(non-git)",
            dt,
        )

    console.print("\n", table, "\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register undo and runs commands with Typer CLIs."""
    app.command("undo")(undo_cli_cmd)
    app.command("runs")(runs_cli_cmd)
    octos_app.command("undo")(undo_cli_cmd)
    octos_app.command("runs")(runs_cli_cmd)
