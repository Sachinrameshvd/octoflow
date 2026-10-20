"""OctoFlow Themes: Curated Developer Palettes & Theme Engine.

Provides 8 developer-favorite themes (Abyssal Cyber, Catppuccin Mocha,
Tokyo Night, Dracula, Cyberpunk 2077, Nord, Gruvbox, and Minimalist Obsidian),
persistent preference storage in ~/.octoflow/theme.json, and color tokens for
Rich terminal consoles and 3D WebGL visualizer synchronization.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import time
from typing import Dict, Optional, Tuple, List, Set

from rich.console import Console
from rich.live import Live
from rich.text import Text


@dataclass
class OctoTheme:
    """Color palette and visual tokens for terminal cockpit and visualizer."""
    id: str
    name: str
    description: str
    # Hex codes for WebGL & CSS
    primary_hex: str
    secondary_hex: str
    accent_hex: str
    success_hex: str
    warning_hex: str
    danger_hex: str
    bg_hex: str
    surface_hex: str
    text_hex: str
    muted_hex: str
    border_hex: str
    # Rich console color tag names
    rich_primary: str
    rich_secondary: str
    rich_accent: str
    rich_success: str
    rich_warning: str
    rich_danger: str
    rich_muted: str
    rich_border: str


THEMES: Dict[str, OctoTheme] = {
    "abyssal": OctoTheme(
        id="abyssal",
        name="Abyssal Cyber",
        description="Deep-sea bioluminescent cyan and neon magenta (Default)",
        primary_hex="#00F0FF",
        secondary_hex="#EC4899",
        accent_hex="#8B5CF6",
        success_hex="#10B981",
        warning_hex="#F59E0B",
        danger_hex="#EF4444",
        bg_hex="#0B0F19",
        surface_hex="#111827",
        text_hex="#F9FAFB",
        muted_hex="#6B7280",
        border_hex="#00F0FF",
        rich_primary="bold cyan",
        rich_secondary="bold magenta",
        rich_accent="bold blue",
        rich_success="bold green",
        rich_warning="bold yellow",
        rich_danger="bold red",
        rich_muted="dim white",
        rich_border="cyan",
    ),
    "catppuccin": OctoTheme(
        id="catppuccin",
        name="Catppuccin Mocha",
        description="Soothing pastel dark palette with mauve, sapphire & peach",
        primary_hex="#CBA6F7",
        secondary_hex="#89B4FA",
        accent_hex="#FAB387",
        success_hex="#A6E3A1",
        warning_hex="#F9E2AF",
        danger_hex="#F38BA8",
        bg_hex="#1E1E2E",
        surface_hex="#181825",
        text_hex="#CDD6F4",
        muted_hex="#7F849C",
        border_hex="#CBA6F7",
        rich_primary="bold magenta",
        rich_secondary="bold blue",
        rich_accent="bold yellow",
        rich_success="bold green",
        rich_warning="yellow",
        rich_danger="bold red",
        rich_muted="dim white",
        rich_border="magenta",
    ),
    "tokyo-night": OctoTheme(
        id="tokyo-night",
        name="Tokyo Night",
        description="Moody midnight cyberpunk with soft lavender and vibrant teal",
        primary_hex="#7DCFFF",
        secondary_hex="#BB9AF7",
        accent_hex="#7AA2F7",
        success_hex="#9ECE6A",
        warning_hex="#E0AF68",
        danger_hex="#F7768E",
        bg_hex="#1A1B26",
        surface_hex="#16161E",
        text_hex="#C0CAF5",
        muted_hex="#565F89",
        border_hex="#7DCFFF",
        rich_primary="bold cyan",
        rich_secondary="bold magenta",
        rich_accent="bold blue",
        rich_success="bold green",
        rich_warning="bold yellow",
        rich_danger="bold red",
        rich_muted="dim white",
        rich_border="cyan",
    ),
    "dracula": OctoTheme(
        id="dracula",
        name="Dracula Pro",
        description="High-contrast electric vampire purple, hot pink and mint",
        primary_hex="#BD93F9",
        secondary_hex="#FF79C6",
        accent_hex="#8BE9FD",
        success_hex="#50FA7B",
        warning_hex="#F1FA8C",
        danger_hex="#FF5555",
        bg_hex="#282A36",
        surface_hex="#21222C",
        text_hex="#F8F8F2",
        muted_hex="#6272A4",
        border_hex="#BD93F9",
        rich_primary="bold magenta",
        rich_secondary="bold red",
        rich_accent="bold cyan",
        rich_success="bold green",
        rich_warning="bold yellow",
        rich_danger="bold red",
        rich_muted="dim white",
        rich_border="magenta",
    ),
    "cyberpunk": OctoTheme(
        id="cyberpunk",
        name="Cyberpunk 2077",
        description="High-voltage neon yellow, hot magenta and laser cyan",
        primary_hex="#FFE600",
        secondary_hex="#FF007F",
        accent_hex="#00FFFF",
        success_hex="#00FF66",
        warning_hex="#FFAA00",
        danger_hex="#FF0033",
        bg_hex="#120A2A",
        surface_hex="#1A102F",
        text_hex="#FFFFFF",
        muted_hex="#7A68A6",
        border_hex="#FFE600",
        rich_primary="bold yellow",
        rich_secondary="bold magenta",
        rich_accent="bold cyan",
        rich_success="bold green",
        rich_warning="bold yellow",
        rich_danger="bold red",
        rich_muted="dim white",
        rich_border="yellow",
    ),
    "nord": OctoTheme(
        id="nord",
        name="Nord Arctic",
        description="Calm, distraction-free arctic polar night and frost blue",
        primary_hex="#88C0D0",
        secondary_hex="#81A1C1",
        accent_hex="#5E81AC",
        success_hex="#A3BE8C",
        warning_hex="#EBCB8B",
        danger_hex="#BF616A",
        bg_hex="#2E3440",
        surface_hex="#272C36",
        text_hex="#ECEFF4",
        muted_hex="#616E88",
        border_hex="#88C0D0",
        rich_primary="bold cyan",
        rich_secondary="bold blue",
        rich_accent="blue",
        rich_success="bold green",
        rich_warning="bold yellow",
        rich_danger="bold red",
        rich_muted="dim white",
        rich_border="cyan",
    ),
    "gruvbox": OctoTheme(
        id="gruvbox",
        name="Gruvbox Dark",
        description="Warm retro earthy analog palette with warm gold and terracotta",
        primary_hex="#FABD2F",
        secondary_hex="#FE8019",
        accent_hex="#8EC07C",
        success_hex="#B8BB26",
        warning_hex="#FABD2F",
        danger_hex="#FB4934",
        bg_hex="#282828",
        surface_hex="#1D2021",
        text_hex="#EBDBB2",
        muted_hex="#928374",
        border_hex="#FABD2F",
        rich_primary="bold yellow",
        rich_secondary="bold red",
        rich_accent="bold green",
        rich_success="bold green",
        rich_warning="bold yellow",
        rich_danger="bold red",
        rich_muted="dim white",
        rich_border="yellow",
    ),
    "minimalist": OctoTheme(
        id="minimalist",
        name="Minimalist Obsidian",
        description="Ultra-clean Vercel/Linear monochrome with stark emerald accents",
        primary_hex="#FFFFFF",
        secondary_hex="#22C55E",
        accent_hex="#A1A1AA",
        success_hex="#22C55E",
        warning_hex="#EAB308",
        danger_hex="#EF4444",
        bg_hex="#000000",
        surface_hex="#09090B",
        text_hex="#FAFAFA",
        muted_hex="#71717A",
        border_hex="#3F3F46",
        rich_primary="bold white",
        rich_secondary="bold green",
        rich_accent="bold white",
        rich_success="bold green",
        rich_warning="bold yellow",
        rich_danger="bold red",
        rich_muted="dim white",
        rich_border="white",
    ),
}


_CONFIG_DIR = Path.home() / ".octoflow"
_THEME_FILE = _CONFIG_DIR / "theme.json"


def get_theme(name_or_alias: Optional[str] = None) -> OctoTheme:
    """Retrieve an OctoTheme by id or alias, falling back to saved preference or 'abyssal'."""
    if not name_or_alias:
        return load_saved_theme()

    cleaned = name_or_alias.strip().lower().replace(" ", "-").replace("_", "-")
    # Aliases
    aliases = {
        "mocha": "catppuccin",
        "tokyo": "tokyo-night",
        "synthwave": "cyberpunk",
        "retro": "gruvbox",
        "mono": "minimalist",
        "obsidian": "minimalist",
        "linear": "minimalist",
        "default": "abyssal",
        "cyber": "abyssal",
    }
    resolved = aliases.get(cleaned, cleaned)
    return THEMES.get(resolved, THEMES["abyssal"])


def load_saved_theme() -> OctoTheme:
    """Load the user's saved theme from ~/.octoflow/theme.json, or default to 'abyssal'."""
    try:
        if _THEME_FILE.exists():
            data = json.loads(_THEME_FILE.read_text(encoding="utf-8"))
            theme_id = data.get("theme_id", "abyssal")
            if theme_id in THEMES:
                return THEMES[theme_id]
    except Exception:
        pass
    return THEMES["abyssal"]


def save_theme_preference(theme_id: str) -> bool:
    """Persist the user's theme preference globally to ~/.octoflow/theme.json."""
    try:
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        theme = get_theme(theme_id)
        payload = {
            "theme_id": theme.id,
            "theme_name": theme.name,
            "tokens": asdict(theme),
        }
        _THEME_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def list_themes() -> Dict[str, OctoTheme]:
    """Return all available registered themes."""
    return THEMES


def get_theme_banner_colors(theme: OctoTheme) -> Tuple[List[str], str]:
    """Return the tailored 8-letter color palette and 3D shadow color for a given theme."""
    THEME_PALETTES: Dict[str, Tuple[List[str], str]] = {
        "abyssal": (
            ['#00f0ff', '#22d3ee', '#38bdf8', '#60a5fa', '#818cf8', '#a855f7', '#c084fc', '#ff007f'],
            '#78350f',
        ),
        "catppuccin": (
            ['#cba6f7', '#b4befe', '#89b4fa', '#74c7ec', '#89dceb', '#a6e3a1', '#f9e2af', '#fab387'],
            '#78350f',
        ),
        "tokyo-night": (
            ['#7dcfff', '#7aa2f7', '#2ac3de', '#bb9af7', '#9d7cd8', '#f7768e', '#ff9e64', '#e0af68'],
            '#78350f',
        ),
        "dracula": (
            ['#bd93f9', '#8be9fd', '#50fa7b', '#f1fa8c', '#ffb86c', '#ff5555', '#ff79c6', '#bd93f9'],
            '#78350f',
        ),
        "cyberpunk": (
            ['#ffe600', '#fbbf24', '#ff5500', '#ff0055', '#ff007f', '#c026d3', '#8b5cf6', '#00ffff'],
            '#78350f',
        ),
        "nord": (
            ['#88c0d0', '#81a1c1', '#5e81ac', '#8fbcbb', '#a3be8c', '#ebcb8b', '#d08770', '#b48ead'],
            '#78350f',
        ),
        "gruvbox": (
            ['#fb4934', '#fe8019', '#fabd2f', '#b8bb26', '#8ec07c', '#83a598', '#d3869b', '#fabd2f'],
            '#78350f',
        ),
        "minimalist": (
            ['#ffffff', '#f4f4f5', '#e4e4e7', '#d4d4d8', '#a1a1aa', '#50fa7b', '#34d399', '#ffffff'],
            '#78350f',
        ),
    }

    if theme.id in THEME_PALETTES:
        return THEME_PALETTES[theme.id]

    # Dynamic fallback for any custom theme
    colors = [
        theme.primary_hex,
        theme.secondary_hex,
        theme.accent_hex,
        theme.success_hex,
        theme.warning_hex,
        theme.danger_hex,
        theme.primary_hex,
        theme.secondary_hex,
    ]
    return colors, theme.surface_hex


OCTOFLOW_3D_LETTERS = {
    'O': [' ▄██▄  ', '██  ██▌', '██  ██▌', ' ▀██▀ ▌', '  ▀▀▀  '],
    'C': [' ▄███  ', '██    ▌', '██    ▌', ' ▀███ ▌', '  ▀▀▀  '],
    'T': ['█████  ', '  █   ▌', '  █   ▌', '  █   ▌', '  ▀    '],
    'O2':[' ▄██▄  ', '██  ██▌', '██  ██▌', ' ▀██▀ ▌', '  ▀▀▀  '],
    'F': ['█████  ', '██▀▀  ▌', '██    ▌', '██    ▌', '▀      '],
    'L': ['██     ', '██    ▌', '██    ▌', '█████ ▌', ' ▀▀▀▀  '],
    'O3':[' ▄██▄  ', '██  ██▌', '██  ██▌', ' ▀██▀ ▌', '  ▀▀▀  '],
    'W': ['█   █  ', '█ █ █ ▌', '██ ██ ▌', ' █ █  ▌', '  ▀ ▀  '],
}
WORD_LETTERS = ['O', 'C', 'T', 'O2', 'F', 'L', 'O3', 'W']


def render_octoflow_3d_banner(
    theme: OctoTheme,
    active_indices: Optional[Set[int]] = None,
    spark_idx: int = -1,
    subtitle: Optional[str] = None,
) -> Text:
    """Render the volumetric 3D extruded OCTOFLOW banner styled dynamically in the theme's palette."""
    banner_text = Text()
    colors, _ = get_theme_banner_colors(theme)
    banner_text.append("  ◈ OCTOFLOW // CEPHALOPOD NEURAL SWARM CONSOLE\n\n", style=f"dim {colors[0]}")

    for y in range(5):
        banner_text.append("  ")
        for i, ch in enumerate(WORD_LETTERS):
            s = OCTOFLOW_3D_LETTERS[ch][y]
            is_spark = (i == spark_idx)
            is_active = (active_indices is None) or (i in active_indices)

            for char in s:
                if char in ['█', '▄', '▀'] and y < 4:
                    if is_spark:
                        banner_text.append(char, style="bold white")
                    elif is_active:
                        banner_text.append(char, style=f"bold {colors[i]}")
                    else:
                        banner_text.append(char, style=f"dim {colors[i]}")
                elif char in ['▌', '▀']:
                    if is_spark:
                        banner_text.append(char, style="white")
                    elif is_active:
                        banner_text.append(char, style=f"dim {colors[i]}")
                    else:
                        banner_text.append(char, style="dim #1e293b")
                else:
                    banner_text.append(char)
            banner_text.append(" ")
        banner_text.append("\n")

    if subtitle is not None:
        banner_text.append(Text.from_markup(f"\n  {subtitle}\n"))
    else:
        banner_text.append(f"\n  ● v1.0.0 • 8-64 Ganglia • Active Inference • Theme: {theme.name}\n", style="dim white")
    return banner_text


def get_banner_animation_frames(theme: OctoTheme) -> List[Text]:
    """Generate signature theme-specific animation frames for the 3D banner."""
    frames: List[Text] = []
    tid = theme.id

    if tid == "cyberpunk":
        # Night City high-voltage neon overdrive boot sequence
        frames.append(render_octoflow_3d_banner(theme, active_indices=set()))
        frames.append(render_octoflow_3d_banner(theme, active_indices={1, 3, 5, 7}, spark_idx=1))
        frames.append(render_octoflow_3d_banner(theme, active_indices=set()))
        frames.append(render_octoflow_3d_banner(theme, active_indices={0, 2, 4, 6}, spark_idx=4))
        for step in range(8):
            frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(step + 1)), spark_idx=step))
        frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(8)), spark_idx=-1))

    elif tid == "dracula":
        # Vampire voltage lightning arc
        frames.append(render_octoflow_3d_banner(theme, active_indices=set()))
        frames.append(render_octoflow_3d_banner(theme, active_indices={0, 7}, spark_idx=0))
        frames.append(render_octoflow_3d_banner(theme, active_indices={0, 1, 6, 7}, spark_idx=7))
        frames.append(render_octoflow_3d_banner(theme, active_indices={0, 1, 2, 5, 6, 7}, spark_idx=2))
        frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(8)), spark_idx=3))
        frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(8)), spark_idx=-1))

    elif tid == "tokyo-night":
        # Dual-beam converge wipe from edges to center
        for i in range(4):
            active = set()
            for k in range(i + 1):
                active.add(k)
                active.add(7 - k)
            frames.append(render_octoflow_3d_banner(theme, active_indices=active, spark_idx=i))
        frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(8)), spark_idx=3))
        frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(8)), spark_idx=-1))

    else:
        # Abyssal / Catppuccin / Nord / Gruvbox / Minimalist:
        # Bioluminescent wave pulse flowing smoothly left-to-right
        for step in range(8):
            frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(step + 1)), spark_idx=step))
        # Radiant glow lock-in
        frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(8)), spark_idx=4))
        frames.append(render_octoflow_3d_banner(theme, active_indices=set(range(8)), spark_idx=-1))

    return frames


def get_banner_loop_frame(
    theme: OctoTheme,
    tick: int,
    subtitle: Optional[str] = None,
) -> Text:
    """Generate fluid continuous looping animation frame for the 3D banner."""
    tid = theme.id
    phase = tick % 24

    if tid == "cyberpunk":
        if phase < 8:
            active = set(range(phase + 1))
            spark = phase
        elif phase < 12:
            active = {0, 2, 4, 6} if (phase % 2 == 0) else {1, 3, 5, 7}
            spark = (phase * 3) % 8
        elif phase < 20:
            active = set(range(8))
            spark = 7 - (phase - 12)
        else:
            active = set(range(8))
            spark = -1

    elif tid == "dracula":
        if phase < 4:
            active = {phase, 7 - phase}
            spark = phase
        elif phase < 12:
            active = set(range(8))
            spark = (phase * 2) % 8
        elif phase < 20:
            active = set(range(8))
            spark = 7 - (phase - 12)
        else:
            active = set(range(8))
            spark = -1

    elif tid == "tokyo-night":
        if phase < 4:
            active = {i for i in range(phase + 1)} | {7 - i for i in range(phase + 1)}
            spark = phase
        elif phase < 8:
            active = set(range(8))
            spark = 3 if phase % 2 == 0 else 4
        elif phase < 16:
            active = set(range(8))
            spark = phase % 8
        else:
            active = set(range(8))
            spark = -1

    else:
        # Abyssal / Catppuccin / Nord / Gruvbox / Minimalist
        if phase < 8:
            active = set(range(phase + 1))
            spark = phase
        elif phase < 16:
            active = set(range(8))
            spark = 7 - (phase - 8)
        elif phase < 20:
            active = set(range(8))
            spark = 3 if (phase % 2 == 0) else 4
        else:
            active = set(range(8))
            spark = -1

    return render_octoflow_3d_banner(theme, active_indices=active, spark_idx=spark, subtitle=subtitle)


def play_banner_animation(console: Console, theme: Optional[OctoTheme] = None, delay: float = 0.05):
    """Play the animated 3D banner in the terminal (with automatic headless fallback)."""
    if theme is None:
        theme = load_saved_theme()

    if not sys.stdout.isatty():
        console.print(render_octoflow_3d_banner(theme))
        return

    frames = get_banner_animation_frames(theme)
    try:
        with Live(frames[0], console=console, refresh_per_second=24, transient=True) as live:
            for frame in frames:
                live.update(frame)
                time.sleep(delay)
    except (KeyboardInterrupt, Exception):
        pass

    console.print(render_octoflow_3d_banner(theme))


def play_banner_continuous(
    console: Console,
    theme: Optional[OctoTheme] = None,
    delay: float = 0.045,
    max_ticks: Optional[int] = None,
    prompt_message: str = "Press [Enter] or any key to enter Cockpit • [Ctrl+C to exit]",
) -> None:
    """Continuously play the ambient animated 3D banner until a key is pressed or max_ticks reached."""
    if theme is None:
        theme = load_saved_theme()

    if not (sys.stdout.isatty() and sys.stdin.isatty()):
        console.print(render_octoflow_3d_banner(theme))
        return

    import termios
    import tty
    import select

    fd = sys.stdin.fileno()
    old_settings = None
    try:
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    except Exception:
        play_banner_animation(console, theme, delay=delay)
        return

    tick = 0
    sub = f"[{theme.rich_primary}]● LIVE AMBIENT HUD[/{theme.rich_primary}] [dim]• {prompt_message}[/dim]"
    try:
        with Live(get_banner_loop_frame(theme, 0, subtitle=sub), console=console, refresh_per_second=24, transient=True) as live:
            while True:
                rlist, _, _ = select.select([sys.stdin], [], [], delay)
                if rlist:
                    # Key was pressed, drain input
                    try:
                        sys.stdin.read(1)
                        # Flush any remaining bytes in multi-byte escape sequences
                        while select.select([sys.stdin], [], [], 0.01)[0]:
                            sys.stdin.read(1)
                    except Exception:
                        pass
                    break

                tick += 1
                if max_ticks is not None and tick >= max_ticks:
                    break

                frame = get_banner_loop_frame(theme, tick, subtitle=sub)
                live.update(frame)
    except (KeyboardInterrupt, Exception):
        pass
    finally:
        if old_settings is not None:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                pass

    console.print(render_octoflow_3d_banner(theme))


