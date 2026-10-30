"""Triage and Diff-Review CLI command for file patch inspection and AST validation."""

import typer
from rich.console import Console

from octoflow.themes import load_saved_theme

console = Console()


_notice_printed = False


def triage_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
    auto_approve: bool = typer.Option(
        False, "--yes", "-y", help="Auto-approve all AST-valid changes"
    ),
):
    r"""Interactive file-by-file patch inspector and diff triage with AST validation. \[experimental]"""
    global _notice_printed
    if not _notice_printed:
        console.print(
            "[yellow]Notice: 'triage' is an experimental feature and may change or be removed in future releases.[/yellow]\n"
        )
        _notice_printed = True
    from octoflow.triage import triage_workspace_diffs

    theme = load_saved_theme()
    console.print(
        f"\n[{theme.rich_primary}]◈ OctoFlow Patch Triage: Reviewing uncommitted changes...[/{theme.rich_primary}]"
    )
    res = triage_workspace_diffs(
        workspace_dir=workspace,
        interactive=not auto_approve,
        auto_approve=auto_approve,
        console=console,
    )
    console.print(f"\n[{theme.rich_success}]✔ {res['message']}[/{theme.rich_success}]\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register triage and diff-review commands with Typer apps."""
    app.command("diff-review")(triage_cli_cmd)
    octos_app.command("diff-review")(triage_cli_cmd)
    app.command("triage")(triage_cli_cmd)
    octos_app.command("triage")(triage_cli_cmd)
