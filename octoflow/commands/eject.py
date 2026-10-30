"""Eject CLI command to export autonomous standalone agent harness."""

import typer
from rich.console import Console

console = Console()


_notice_printed = False


def eject_cli_cmd(
    output_dir: str = typer.Option(
        "./octo-harness", "--output", "-o", help="Target output directory for standalone harness"
    ),
):
    r"""Eject autonomous standalone cephalopod agent harness into any repository. \[experimental]"""
    global _notice_printed
    if not _notice_printed:
        console.print(
            "[yellow]Notice: 'eject' is an experimental feature and may change or be removed in future releases.[/yellow]\n"
        )
        _notice_printed = True
    from octoflow.eject import eject_harness

    eject_harness(output_dir=output_dir, console=console)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register eject command with Typer apps."""
    app.command("eject")(eject_cli_cmd)
    octos_app.command("eject")(eject_cli_cmd)
