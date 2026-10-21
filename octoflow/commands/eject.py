"""Eject CLI command to export autonomous standalone agent harness."""

import typer
from rich.console import Console

console = Console()


def eject_cli_cmd(
    output_dir: str = typer.Option("./octo-harness", "--output", "-o", help="Target output directory for standalone harness"),
):
    """Eject autonomous standalone cephalopod agent harness into any repository."""
    from octoflow.eject import eject_harness
    eject_harness(output_dir=output_dir, console=console)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register eject command with Typer apps."""
    app.command("eject")(eject_cli_cmd)
    octos_app.command("eject")(eject_cli_cmd)
