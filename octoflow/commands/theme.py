"""Theme, Banner, and Screensaver CLI commands."""

import sys

import typer
from rich.console import Console
from rich.table import Table

from octoflow.themes import (
    get_theme,
    list_themes,
    load_saved_theme,
    save_theme_preference,
)

console = Console()


def _execute_theme_cmd(name: str | None):
    """Execute theme display or switch."""
    cur_theme = load_saved_theme()
    if not name:
        if sys.stdin.isatty() and sys.stdout.isatty():
            from octoflow.theme_selector import run_interactive_theme_picker

            chosen = run_interactive_theme_picker(console, initial_theme=cur_theme)
            console.print(
                f"[{chosen.rich_success}]✔ Theme locked in: [bold]{chosen.name}[/bold] ({chosen.description})[/{chosen.rich_success}]"
            )
            console.print(
                "[dim]Saved to ~/.octoflow/theme.json and synchronized with 3D Visualizer.[/dim]\n"
            )
            return

        themes_all = list_themes()
        theme_table = Table(
            title="◈ Available Developer Palettes", border_style=cur_theme.rich_border, expand=True
        )
        theme_table.add_column("#", width=4, style=cur_theme.rich_primary)
        theme_table.add_column("Theme ID", style="bold white", width=16)
        theme_table.add_column("Name", style="white", width=22)
        theme_table.add_column("Palette Swatch", width=14)
        theme_table.add_column("Description", style="dim")

        for idx, (t_id, t_obj) in enumerate(themes_all.items(), 1):
            is_active = " [bold green]✔ ACTIVE[/]" if t_id == cur_theme.id else ""
            swatch = f"[{t_obj.rich_primary}]●[/{t_obj.rich_primary}] [{t_obj.rich_secondary}]●[/{t_obj.rich_secondary}] [{t_obj.rich_success}]●[/{t_obj.rich_success}] [{t_obj.rich_warning}]●[/{t_obj.rich_warning}]"
            theme_table.add_row(str(idx), t_id + is_active, t_obj.name, swatch, t_obj.description)

        console.print(theme_table)
        console.print(
            "[dim]Tip: Switch theme by typing [bold]octos theme <id>[/bold] (e.g. [cyan]octos theme catppuccin[/cyan])[/dim]\n"
        )
    else:
        new_theme = get_theme(name)
        save_theme_preference(new_theme.id)
        console.print(
            f"[{new_theme.rich_success}]✔ Switched palette to: [bold]{new_theme.name}[/bold] ({new_theme.description})[/{new_theme.rich_success}]"
        )
        console.print(
            "[dim]Saved to ~/.octoflow/theme.json and synchronized with 3D Visualizer.[/dim]\n"
        )


def _run_banner(loop: bool, theme_name: str | None):
    t = get_theme(theme_name) if theme_name else load_saved_theme()
    if loop:
        from octoflow.themes import play_banner_continuous

        play_banner_continuous(console, t, prompt_message="Press [Enter] or any key to exit")
    else:
        from octoflow.themes import play_banner_animation

        play_banner_animation(console, t)


def app_theme_cmd(
    name: str | None = typer.Argument(
        None,
        help="Theme palette ('abyssal', 'catppuccin', 'tokyo-night', 'dracula', 'cyberpunk', 'nord', 'gruvbox', 'minimalist')",
    ),
):
    """View or switch the OctoFlow terminal & visualizer theme."""
    _execute_theme_cmd(name)


def octos_theme_cmd(
    name: str | None = typer.Argument(
        None,
        help="Theme palette ('abyssal', 'catppuccin', 'tokyo-night', 'dracula', 'cyberpunk', 'nord', 'gruvbox', 'minimalist')",
    ),
):
    """View or switch the OctoFlow terminal & visualizer theme."""
    _execute_theme_cmd(name)


def app_banner_cmd(
    loop: bool = typer.Option(False, "--loop", "-l", help="Run continuous ambient animation loop"),
    theme: str | None = typer.Option(None, "--theme", "-t", help="Theme palette"),
):
    """Play the 3D animated OCTOFLOW banner (single replay or continuous loop)."""
    _run_banner(loop, theme)


def octos_banner_cmd(
    loop: bool = typer.Option(False, "--loop", "-l", help="Run continuous ambient animation loop"),
    theme: str | None = typer.Option(None, "--theme", "-t", help="Theme palette"),
):
    """Play the 3D animated OCTOFLOW banner (single replay or continuous loop)."""
    _run_banner(loop, theme)


def app_screensaver_cmd(
    theme: str | None = typer.Option(None, "--theme", "-t", help="Theme palette"),
):
    """Launch continuous ambient 3D banner screensaver until keypress."""
    _run_banner(True, theme)


def octos_screensaver_cmd(
    theme: str | None = typer.Option(None, "--theme", "-t", help="Theme palette"),
):
    """Launch continuous ambient 3D banner screensaver until keypress."""
    _run_banner(True, theme)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register theme, banner, and screensaver commands with Typer apps."""
    app.command("theme")(app_theme_cmd)
    octos_app.command("theme")(octos_theme_cmd)

    app.command("banner")(app_banner_cmd)
    octos_app.command("banner")(octos_banner_cmd)

    app.command("screensaver")(app_screensaver_cmd)
    octos_app.command("screensaver")(octos_screensaver_cmd)
