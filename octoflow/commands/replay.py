"""Replay CLI command to replay recorded trace.jsonl into terminal and 3D visualizer."""

from __future__ import annotations

import typer
from rich.console import Console

from octoflow.themes import load_saved_theme
from octoflow.trace import replay_trace

console = Console()


def replay_cli_cmd(
    run_id: str | None = typer.Argument(
        None, help="Run ID to replay (e.g. 'run-1731000000'), or omit to replay latest run"
    ),
    speed: float = typer.Option(
        1.0, "--speed", "-s", help="Replay playback speed multiplier (0 = instantaneous playback)"
    ),
    no_visualizer: bool = typer.Option(
        False, "--no-visualizer", help="Disable broadcasting replayed telemetry to 3D visualizer"
    ),
    port: int = typer.Option(
        8088, "--port", "-p", help="Visualizer telemetry port to broadcast on"
    ),
):
    """Replay an execution trace into the 3D connectome visualizer and terminal as plain lines."""
    theme = load_saved_theme()

    def _print_fn(line: str) -> None:
        console.print(line, markup=False)

    try:
        resolved_id, events = replay_trace(
            run_id=run_id,
            speed=speed,
            no_visualizer=no_visualizer,
            port=port,
            output_fn=_print_fn,
        )
    except FileNotFoundError as e:
        console.print(f"\n[{theme.rich_danger}]✖ Replay failed: {e}[/{theme.rich_danger}]\n")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"\n[{theme.rich_danger}]✖ Error during replay: {e}[/{theme.rich_danger}]\n")
        raise typer.Exit(code=2) from e


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register replay command with Typer apps."""
    app.command("replay")(replay_cli_cmd)
    octos_app.command("replay")(replay_cli_cmd)
