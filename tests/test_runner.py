"""
Tests for OctoFlow Benthic Dot-Matrix Runner (Happy Octo & Winking Pixel Fish).
"""

from io import StringIO

from octoflow.runner import (
    FISH_SPRITE,
    OCTO_SPRITE_GROUND,
    OCTO_SPRITE_JUMP,
    get_animation_frames,
    play_runner_animation,
    render_runner_frame,
)
from octoflow.themes import THEMES, load_saved_theme
from rich.console import Console


def test_sprites_contain_happy_and_wink_eyes():
    """Verify that both sprites include the user's chosen eye styles."""
    octo_has_happy_smile = any("⌒" in line for line in OCTO_SPRITE_GROUND)
    assert octo_has_happy_smile, "Octopus ground sprite must feature the Kawaii Happy Smile (⌒   ⌒)"

    octo_jump_has_happy_smile = any("⌒" in line for line in OCTO_SPRITE_JUMP)
    assert octo_jump_has_happy_smile, (
        "Octopus jump sprite must feature the Kawaii Happy Smile (⌒   ⌒)"
    )

    fish_has_wink = any("⌒" in line for line in FISH_SPRITE)
    assert fish_has_wink, "Pixel fish must feature the cute wink eye (⌒)"


def test_render_runner_frame():
    """Verify frame rendering output and panel structure."""
    theme = load_saved_theme()
    panel = render_runner_frame(theme, octo_x=1, octo_y=0, fish_x=44, is_jumping=False)

    assert panel is not None
    console = Console(file=StringIO(), width=80)
    console.print(panel)
    output = console.file.getvalue()

    assert "Benthic Dot Runner" in output
    assert "Octo (⌒   ⌒)" in output
    assert "Gliding left & right" in output
    assert "───" in output


def test_animation_frames_sequence():
    """Verify all 6 animation frames are generated cleanly for a theme."""
    theme = THEMES["abyssal"]
    frames = get_animation_frames(theme)
    assert len(frames) == 6, "Expected 6 smooth leap animation frames"


def test_play_runner_animation_headless():
    """Verify play_runner_animation executes safely in headless / pipe environments."""
    theme = THEMES["cyberpunk"]
    buf = StringIO()
    console = Console(file=buf, width=80)
    play_runner_animation(console, theme=theme, cycles=1, delay=0.01)
    output = buf.getvalue()
    assert "Benthic Dot Runner" in output
