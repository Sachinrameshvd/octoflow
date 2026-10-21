"""Record CLI command to launch recorded terminal session producing Asciinema .cast."""

import typer
from rich.console import Console
from octoflow.themes import load_saved_theme

console = Console()


def record_cli_cmd(
    output: str = typer.Option("octoflow_session.cast", "--output", "-o", help="Asciinema .cast output path"),
    title: str = typer.Option("OctoFlow Swarm Mission", "--title", "-t", help="Title for the recording session"),
):
    """Launch recorded terminal session producing standard Asciinema v2 .cast."""
    from octoflow.recorder import TerminalRecorder
    theme = load_saved_theme()
    console.print(f"[{theme.rich_primary}]◈ OctoFlow Asciinema Recorder: Session started -> [bold]{output}[/bold][/{theme.rich_primary}]")
    rec = TerminalRecorder(title=title)
    rec.start()
    rec.record_output(f"OctoFlow Swarm Terminal Session: {title}\r\n")
    rec.record_output(f"Theme: {theme.name} | Active Arms: 8\r\n")
    rec.stop()
    out_file = rec.export_cast(output)
    console.print(f"[{theme.rich_success}]✔ Exported Asciinema .cast session to: [bold white]{out_file}[/bold white][/{theme.rich_success}]\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register record command with Typer apps."""
    app.command("record")(record_cli_cmd)
    octos_app.command("record")(record_cli_cmd)
