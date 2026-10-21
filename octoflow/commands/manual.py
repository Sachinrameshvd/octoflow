"""Manual and Docs CLI command for the interactive Cephalopod Master Manual."""

from typing import Optional
import typer
from rich.console import Console

console = Console()


def manual_cli_cmd(
    chapter: Optional[str] = typer.Option(None, "--chapter", "-c", help="Specific chapter number or keyword (e.g. 1, 2, commands, playbooks)"),
    web: bool = typer.Option(False, "--web", "-w", help="Open visual manual in default web browser"),
):
    """Display interactive Cephalopod Master Manual and Developer Field Guide."""
    from octoflow.manual import display_manual
    display_manual(chapter=chapter, web=web, console=console)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register manual and docs commands with Typer apps."""
    app.command("docs")(manual_cli_cmd)
    octos_app.command("docs")(manual_cli_cmd)
    app.command("manual")(manual_cli_cmd)
    octos_app.command("manual")(manual_cli_cmd)
