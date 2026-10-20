"""
Interactive Theme Selector for OctoFlow with Live Preview.
Navigate through all 8 developer palettes using Up/Down arrow keys or Vim keys (k / j).
Theme colors update live in real-time as you navigate.
Press [ENTER] to confirm and persist, or [ESC]/[Q] to cancel.
"""

from dataclasses import asdict
import select
import sys
import time
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

from octoflow.themes import (
    THEMES,
    OctoTheme,
    load_saved_theme,
    save_theme_preference,
    render_octoflow_3d_banner,
)


def render_theme_selector_panel(selected_idx: int, themes_list: list) -> Panel:
    """Renders the interactive theme selector panel styled in the currently highlighted theme."""
    active_theme: OctoTheme = themes_list[selected_idx][1]

    table = Table(
        title=f"[{active_theme.rich_primary}]◈ Interactive Theme Selector (Live Preview)[/{active_theme.rich_primary}]",
        border_style=active_theme.rich_border,
        expand=True,
        padding=(0, 1),
    )
    table.add_column("Sel", width=3, justify="center")
    table.add_column("#", width=3, style="dim")
    table.add_column("Theme ID", width=14)
    table.add_column("Name", width=22)
    table.add_column("Palette Swatch", width=14)
    table.add_column("Description", style="dim")

    for idx, (t_id, t_obj) in enumerate(themes_list):
        is_selected = (idx == selected_idx)
        if is_selected:
            cursor = f"[{t_obj.rich_primary}]❯[/]"
            theme_id_str = f"[bold {t_obj.rich_primary}]{t_id}[/]"
            name_str = f"[bold white]{t_obj.name}[/]"
        else:
            cursor = " "
            theme_id_str = f"[dim]{t_id}[/dim]"
            name_str = f"[white]{t_obj.name}[/white]"

        swatch = (
            f"[{t_obj.rich_primary}]●[/{t_obj.rich_primary}] "
            f"[{t_obj.rich_secondary}]●[/{t_obj.rich_secondary}] "
            f"[{t_obj.rich_success}]●[/{t_obj.rich_success}] "
            f"[{t_obj.rich_warning}]●[/{t_obj.rich_warning}]"
        )
        table.add_row(cursor, str(idx + 1), theme_id_str, name_str, swatch, t_obj.description)

    # Live Navigation Controls and Color Palette Bar at bottom of panel
    preview_bar = (
        f"\n  [dim]Navigation:[/dim] "
        f"[bold {active_theme.rich_primary}]k / ▲[/] Up  •  "
        f"[bold {active_theme.rich_primary}]j / ▼[/] Down  •  "
        f"[bold white]ENTER[/] Confirm & Save  •  "
        f"[bold]ESC / q[/] Cancel\n"
        f"  [dim]Live Palette:[/dim] [bold {active_theme.rich_primary}]{active_theme.name}[/]  •  "
        f"[{active_theme.rich_primary}]● Primary[/]  •  "
        f"[{active_theme.rich_secondary}]● Secondary[/]  •  "
        f"[{active_theme.rich_success}]● Success[/]  •  "
        f"[{active_theme.rich_warning}]● Warning[/]"
    )

    banner = render_octoflow_3d_banner(active_theme)
    content = Text.from_markup(preview_bar)
    grid = Table.grid(expand=True)
    grid.add_row(banner)
    grid.add_row(table)
    grid.add_row(content)

    return Panel(
        grid,
        title=f"[{active_theme.rich_primary}]◈ OctoFlow Developer Themes[/{active_theme.rich_primary}]",
        subtitle=(
            f"[dim]Navigate: [bold {active_theme.rich_primary}]k / ▲[/] (Up) • "
            f"[bold {active_theme.rich_primary}]j / ▼[/] (Down) • "
            f"[bold white]ENTER[/] Select • [bold]ESC / q[/] Cancel[/dim]"
        ),
        border_style=active_theme.rich_border,
        padding=(0, 0),
    )


def run_interactive_theme_picker(
    console: Console,
    initial_theme: Optional[OctoTheme] = None,
    broadcaster=None,
) -> OctoTheme:
    """
    Launches the live interactive arrow-key theme selector.
    Updates in real time as user presses Up / Down.
    Returns the selected OctoTheme.
    """
    if initial_theme is None:
        initial_theme = load_saved_theme()

    themes_list = list(THEMES.items())
    # Start on current active theme
    selected_idx = 0
    for idx, (t_id, _) in enumerate(themes_list):
        if t_id == initial_theme.id:
            selected_idx = idx
            break

    # If not a TTY (pipe, tests, CI), print static table and return current theme
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        console.print(render_theme_selector_panel(selected_idx, themes_list))
        return initial_theme

    import termios
    import tty

    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    def read_char() -> str:
        return sys.stdin.read(1)

    console.clear()

    try:
        initial_panel = render_theme_selector_panel(selected_idx, themes_list)
        with Live(initial_panel, console=console, refresh_per_second=24, screen=False) as live:
            while True:
                ch = read_char()

                # ESC sequences (Arrow keys)
                if ch == "\x1b":
                    # Check if arrow key follows: \x1b[A or \x1b[B
                    r, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if r:
                        ch2 = read_char()
                        if ch2 == "[":
                            ch3 = read_char()
                            if ch3 == "A":  # UP ARROW
                                selected_idx = (selected_idx - 1) % len(themes_list)
                            elif ch3 == "B":  # DOWN ARROW
                                selected_idx = (selected_idx + 1) % len(themes_list)
                    else:
                        # Standalone ESC -> Cancel and revert
                        return initial_theme

                elif ch in ["k", "K"]:  # Vim Up
                    selected_idx = (selected_idx - 1) % len(themes_list)

                elif ch in ["j", "J"]:  # Vim Down
                    selected_idx = (selected_idx + 1) % len(themes_list)

                elif ch in ["\r", "\n"]:  # ENTER -> Confirm selection
                    selected_theme = themes_list[selected_idx][1]
                    save_theme_preference(selected_theme.id)
                    if broadcaster:
                        broadcaster.broadcast_raw({
                            "type": "THEME_CHANGE",
                            "theme_id": selected_theme.id,
                            "tokens": asdict(selected_theme),
                        })
                    return selected_theme

                elif ch in ["q", "Q", "\x03"]:  # Q or Ctrl+C -> Cancel
                    return initial_theme

                # Broadcast live preview to 3D visualizer while navigating!
                preview_theme = themes_list[selected_idx][1]
                if broadcaster:
                    broadcaster.broadcast_raw({
                        "type": "THEME_CHANGE",
                        "theme_id": preview_theme.id,
                        "tokens": asdict(preview_theme),
                    })

                # Update live terminal UI
                live.update(render_theme_selector_panel(selected_idx, themes_list))

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        console.clear()


if __name__ == "__main__":
    c = Console()
    chosen = run_interactive_theme_picker(c)
    c.print(f"[{chosen.rich_success}]✔ Theme locked in: {chosen.name}[/{chosen.rich_success}]")
