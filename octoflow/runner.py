"""
OctoFlow Ultra-Short Playful Benthic Runner.
Features:
- 5-Line Kawaii Happy Smile Octopus (⌒   ⌒) with suction dots (○)
- Clean, obstacle-free ocean floor
- Smooth left-and-right swimming motion with buoyant leaping arcs
- Ambient floating bubbles and scrolling seabed
- Ultra-short compact profile (fits in any small terminal)
- Strict ZERO EMOJI rule: Pure bio-glyphs only (•, ·, ○, °, o, ⌒, ─).
"""

from dataclasses import dataclass
import math
import random
import select
import sys
import time
from typing import List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

from octoflow.themes import OctoTheme, load_saved_theme


# --- 5-LINE ULTRA MICRO-DOT SPRITES ---

OCTO_SPRITE_GROUND = [
    "      • • • •      ",
    "  • • • · · • • •  ",
    "  • • ⌒ • • ⌒ • •  ",
    "• • • • • • • • • •",
    " • •  ○     ○  • • ",
]

OCTO_SPRITE_RUN_B = [
    "      • • • •      ",
    "  • • • · · • • •  ",
    "  • • ⌒ • • ⌒ • •  ",
    "• • • • • • • • • •",
    "  • • ○     ○ • •  ",
]

OCTO_SPRITE_JUMP = [
    "      • • • •      ",
    "  • • • · · • • •  ",
    "  • • ⌒ • • ⌒ • •  ",
    "  • • • • • • • •  ",
    "   •  ○     ○  •   ",
]

OCTO_SPRITE_DEAD = [
    "      • • • •      ",
    "  • • • · · • • •  ",
    "  • • ✖ • • ✖ • •  ",
    "• • • • • • • • • •",
    " • •  ○     ○  • • ",
]

# Kept for backward compatibility in imports
FISH_SPRITE = [
    "    • • •    ",
    "• ⌒ • · • • •",
    "  • • · •   •",
    "      • •    ",
]


def render_runner_frame(
    theme: OctoTheme,
    octo_x: int = 0,
    octo_y: int = 0,
    fish_positions: Optional[List[int]] = None,
    fish_x: Optional[int] = None,
    is_jumping: bool = False,
    is_dead: bool = False,
    bubbles: Optional[List[tuple]] = None,
    score: int = 0,
    high_score: int = 0,
    game_over: bool = False,
    stride_alt: bool = False,
    seabed_offset: int = 0,
    auto_pilot: bool = True,
) -> Panel:
    """
    Renders an ultra-compact, extended-length (64 cols) retro dot-matrix frame inside a Rich Panel.
    Reduced height: canvas_h = 6 rows (no redundant interior header).
    Extended length: canvas_w = 64 columns (octopus travels all the way from end to end).
    Fish is completely removed as requested.
    """
    canvas_w = 64
    canvas_h = 6
    grid = [[" " for _ in range(canvas_w)] for _ in range(canvas_h)]
    styles = [["" for _ in range(canvas_w)] for _ in range(canvas_h)]

    # 1. Background bubbles
    if bubbles:
        for b in bubbles:
            bx, by, char = b[0], b[1], b[2]
            ibx, iby = int(bx) % canvas_w, int(by) % canvas_h
            if 0 <= iby < canvas_h and 0 <= ibx < canvas_w:
                grid[iby][ibx] = char
                styles[iby][ibx] = "dim cyan"

    # 2. Place Happy Octopus (Fish completely removed)
    if is_dead:
        octo_sprite = OCTO_SPRITE_DEAD
    elif is_jumping or octo_y > 0:
        octo_sprite = OCTO_SPRITE_JUMP
    elif stride_alt:
        octo_sprite = OCTO_SPRITE_RUN_B
    else:
        octo_sprite = OCTO_SPRITE_GROUND

    sprite_h = len(octo_sprite)
    octo_base_y = max(0, canvas_h - sprite_h - int(octo_y))
    ox = max(0, min(int(octo_x), canvas_w - len(octo_sprite[0])))

    for row_idx, line in enumerate(octo_sprite):
        gy = octo_base_y + row_idx
        for col_idx, char in enumerate(line):
            gx = ox + col_idx
            if 0 <= gy < canvas_h and 0 <= gx < canvas_w and char != " ":
                grid[gy][gx] = char
                if char == "⌒":
                    styles[gy][gx] = "bold bright_white"
                elif char == "✖":
                    styles[gy][gx] = "bold red"
                elif char == "○":
                    styles[gy][gx] = f"bold {theme.rich_secondary}"
                elif char == "·":
                    styles[gy][gx] = "bright_white"
                else:
                    styles[gy][gx] = theme.rich_primary

    # 3. Construct Rich Text with Seabed (reduced height, no wasted header)
    res_text = Text()

    for y in range(canvas_h):
        line_chars = "".join(grid[y]).rstrip()
        for x in range(len(line_chars)):
            ch = grid[y][x]
            st = styles[y][x]
            if st:
                res_text.append(ch, style=st)
            else:
                res_text.append(ch)
        res_text.append("\n")

    # Animated scrolling seabed spanning the full extended length
    base_pattern = "────── · ─────── ··· ─────────── · ─────" * 4
    s_start = seabed_offset % 25
    seabed_slice = base_pattern[s_start : s_start + canvas_w]
    res_text.append(seabed_slice, style=f"dim {theme.rich_border}")

    title = f"[{theme.rich_primary}]◈ Benthic Dot Runner[/{theme.rich_primary}]"
    subtitle = f"[{theme.rich_primary}]• Octo (⌒   ⌒)[/{theme.rich_primary}]  [dim]• Gliding left & right[/dim]"

    return Panel(
        res_text,
        title=title,
        subtitle=subtitle,
        border_style=theme.rich_border,
        padding=(0, 1),
        width=canvas_w + 4,
    )


def get_animation_frames(theme: OctoTheme) -> List[Panel]:
    """Generates the left-and-right swimming and jumping frames across the extended platform."""
    frames = [
        # Frame 0: Touching far left edge, seabed
        render_runner_frame(
            theme, octo_x=0, octo_y=0, is_jumping=False,
            bubbles=[(10, 1, "°"), (35, 2, "·"), (50, 0, "o")],
            stride_alt=False
        ),
        # Frame 1: Ascending jump gliding rightward
        render_runner_frame(
            theme, octo_x=12, octo_y=1, is_jumping=True,
            bubbles=[(15, 0, "°"), (40, 2, "o"), (55, 1, "·")],
            stride_alt=True
        ),
        # Frame 2: Mid-water free floating rightward
        render_runner_frame(
            theme, octo_x=28, octo_y=1, is_jumping=True,
            bubbles=[(8, 1, "o"), (25, 0, "°"), (48, 2, "°")],
            stride_alt=False
        ),
        # Frame 3: Touching far right edge!
        render_runner_frame(
            theme, octo_x=45, octo_y=0, is_jumping=False,
            bubbles=[(5, 2, "°"), (20, 1, "·"), (58, 0, "o")],
            stride_alt=True
        ),
        # Frame 4: Ascending jump gliding leftward
        render_runner_frame(
            theme, octo_x=30, octo_y=1, is_jumping=True,
            bubbles=[(18, 0, "°"), (38, 2, "o"), (52, 1, "·")],
            stride_alt=False
        ),
        # Frame 5: Gliding back towards far left start
        render_runner_frame(
            theme, octo_x=12, octo_y=1, is_jumping=True,
            bubbles=[(14, 2, "·"), (32, 1, "°"), (46, 0, "o")],
            stride_alt=True
        ),
    ]
    return frames



def play_runner_animation(
    console: Console,
    theme: Optional[OctoTheme] = None,
    cycles: int = 1,
    delay: float = 0.12,
    interactive: bool = False,
):
    """
    Plays the animated dot runner or launches the interactive game.
    """
    if theme is None:
        theme = load_saved_theme()

    if interactive and sys.stdin.isatty():
        run_dino_game(console, theme)
        return

    frames = get_animation_frames(theme)

    if not sys.stdout.isatty():
        console.print(frames[0])
        return

    try:
        with Live(frames[0], console=console, refresh_per_second=20, transient=False) as live:
            for _ in range(cycles):
                for frame in frames:
                    live.update(frame)
                    time.sleep(delay)
            live.update(frames[0])
    except KeyboardInterrupt:
        pass


def run_dino_game(console: Console, theme: Optional[OctoTheme] = None, auto_pilot: bool = True):
    """
    Ultra-short, obstacle-free playful octopus moving left and right while jumping freely!
    - Travels smoothly across the extended platform (0 <-> 45)
    - Jumps freely with fluid buoyant leaps
    - Controls: [Space]/[Up] to jump, [A]/[D] or [Left]/[Right] to steer, [Q]/[ESC] to exit
    """
    if theme is None:
        theme = load_saved_theme()

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        play_runner_animation(console, theme=theme, cycles=1)
        return

    import termios
    import tty

    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    def check_key() -> str:
        r, _, _ = select.select([sys.stdin], [], [], 0)
        if r:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r2, _, _ = select.select([sys.stdin], [], [], 0.02)
                if r2:
                    seq = sys.stdin.read(2)
                    if seq in ["[A", "OA"]:
                        return "up"
                    elif seq in ["[C", "OC"]:
                        return "right"
                    elif seq in ["[D", "OD"]:
                        return "left"
                return "esc"
            return ch
        return ""

    octo_x = 0.0
    octo_dx = 1.2
    octo_y = 0
    jump_timer = 0.0
    seabed_offset = 0

    bubbles = [
        [random.randint(0, 63), random.randint(0, 5), random.choice(["°", "·", "o"])]
        for _ in range(6)
    ]

    console.clear()

    try:
        frame = render_runner_frame(
            theme, octo_x=int(octo_x), octo_y=0, is_jumping=False,
            bubbles=bubbles
        )
        with Live(frame, console=console, refresh_per_second=24, screen=False) as live:
            while True:
                key = check_key()
                if key in ["q", "Q", "\x03", "esc"]:  # Q, Ctrl+C, or Esc
                    break
                elif key in [" ", "w", "W", "up"]:  # Space, W, or Up arrow triggers an extra high leap
                    jump_timer = 0.8
                elif key in ["a", "A", "h", "H", "left"]:  # Steer left
                    octo_dx = -1.5
                elif key in ["d", "D", "l", "L", "right"]:  # Steer right
                    octo_dx = 1.5

                # 1. Update horizontal movement across the full platform length (0 to 45)
                octo_x += octo_dx
                if octo_x >= 45.0:
                    octo_x = 45.0
                    octo_dx = -1.2  # Reach far right end and turn left
                elif octo_x <= 0.0:
                    octo_x = 0.0
                    octo_dx = 1.2   # Reach far left end and turn right

                # 2. Update playful jumping & floating motion
                jump_timer += 0.16
                jump_val = math.sin(jump_timer)
                if jump_val > 0.25:
                    octo_y = 1
                    is_jumping = True
                else:
                    octo_y = 0
                    is_jumping = False

                # 3. Update ambient bubbles
                for b in bubbles:
                    b[0] = (b[0] - 0.4 * octo_dx) % 64

                # 4. Seabed scroll & stride
                seabed_offset = (seabed_offset + int(octo_dx)) % 40
                stride_alt = int(octo_x // 3) % 2 == 1

                # 5. Render current frame
                frame = render_runner_frame(
                    theme,
                    octo_x=int(octo_x),
                    octo_y=octo_y,
                    is_jumping=is_jumping,
                    bubbles=bubbles,
                    stride_alt=stride_alt,
                    seabed_offset=seabed_offset,
                )
                live.update(frame)
                time.sleep(0.045)  # ~22 FPS silky smooth loop

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        console.clear()


if __name__ == "__main__":
    c = Console()
    run_dino_game(c)
