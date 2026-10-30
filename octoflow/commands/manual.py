"""Manual and Docs CLI command for the interactive Cephalopod Master Manual."""

import typer
from rich.console import Console

console = Console()


_notice_printed = False


def manual_cli_cmd(
    chapter: str | None = typer.Option(
        None,
        "--chapter",
        "-c",
        help="Specific chapter number or keyword (e.g. 1, 2, commands, playbooks)",
    ),
    web: bool = typer.Option(
        False, "--web", "-w", help="Open visual manual in default web browser"
    ),
):
    r"""Display interactive Cephalopod Master Manual and Developer Field Guide. \[experimental]"""
    global _notice_printed
    if not _notice_printed:
        console.print(
            "[yellow]Notice: 'manual/docs' is an experimental feature and may change or be removed in future releases.[/yellow]\n"
        )
        _notice_printed = True
    from octoflow.manual import display_manual

    display_manual(chapter=chapter, web=web, console=console)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register manual and docs commands with Typer apps."""
    app.command("docs")(manual_cli_cmd)
    octos_app.command("docs")(manual_cli_cmd)
    app.command("manual")(manual_cli_cmd)
    octos_app.command("manual")(manual_cli_cmd)
