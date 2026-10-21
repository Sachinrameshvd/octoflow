"""Runner and Play CLI command for the Chrome Dino-style Benthic Dot Runner game."""

import typer
from rich.console import Console
from octoflow.themes import load_saved_theme

console = Console()


def cmd_app_runner():
    """Launch the Chrome Dino-style Benthic Dot Runner game."""
    from octoflow.runner import run_dino_game
    theme = load_saved_theme()
    run_dino_game(console, theme=theme)


def cmd_octos_runner():
    """Launch the Chrome Dino-style Benthic Dot Runner game."""
    from octoflow.runner import run_dino_game
    theme = load_saved_theme()
    run_dino_game(console, theme=theme)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register runner and play commands with Typer apps."""
    app.command(name="play")(cmd_app_runner)
    octos_app.command(name="play")(cmd_octos_runner)
    app.command(name="runner")(cmd_app_runner)
    octos_app.command(name="runner")(cmd_octos_runner)
