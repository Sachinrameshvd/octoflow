"""Comprehensive Unit Tests for OctoFlow Themes & Interactive CLI.

Verifies:
1. All 8 themes exist with valid hex colors and rich token mappings.
2. Theme resolution, alias handling ('mocha' -> 'catppuccin'), and fallback to 'abyssal'.
3. Theme persistence in ~/.octoflow/theme.json via save_theme_preference & load_saved_theme.
4. CLI theme switching commands and live rendering.
"""

from octoflow.cli import octos_app
from octoflow.themes import (
    THEMES,
    get_theme,
    list_themes,
    load_saved_theme,
    save_theme_preference,
)
from typer.testing import CliRunner

runner = CliRunner()


def test_theme_palette_integrity():
    """Verify that all 8 curated developer themes have complete color specs."""
    themes = list_themes()
    assert len(themes) == 8
    expected_ids = [
        "abyssal",
        "catppuccin",
        "tokyo-night",
        "dracula",
        "cyberpunk",
        "nord",
        "gruvbox",
        "minimalist",
    ]
    for theme_id in expected_ids:
        assert theme_id in themes
        t = themes[theme_id]
        assert t.primary_hex.startswith("#")
        assert t.secondary_hex.startswith("#")
        assert t.bg_hex.startswith("#")
        assert t.rich_primary != ""
        assert t.rich_secondary != ""
        assert t.rich_border != ""


def test_theme_resolution_and_aliases():
    """Verify alias mapping for developer ease."""
    assert get_theme("mocha").id == "catppuccin"
    assert get_theme("tokyo").id == "tokyo-night"
    assert get_theme("synthwave").id == "cyberpunk"
    assert get_theme("retro").id == "gruvbox"
    assert get_theme("linear").id == "minimalist"
    assert get_theme("obsidian").id == "minimalist"
    assert get_theme("nonexistent-theme-xyz").id == "abyssal"


def test_theme_persistence(monkeypatch, tmp_path):
    """Verify persistent saving and loading from ~/.octoflow/theme.json."""
    fake_config = tmp_path / ".octoflow"
    fake_theme_file = fake_config / "theme.json"
    monkeypatch.setattr("octoflow.themes._CONFIG_DIR", fake_config)
    monkeypatch.setattr("octoflow.themes._THEME_FILE", fake_theme_file)

    # Save catppuccin
    res = save_theme_preference("catppuccin")
    assert res is True
    assert fake_theme_file.exists()

    # Load saved
    loaded = load_saved_theme()
    assert loaded.id == "catppuccin"

    # Switch to dracula
    save_theme_preference("dracula")
    loaded2 = load_saved_theme()
    assert loaded2.id == "dracula"


def test_cli_theme_list_command():
    """Verify 'octos theme' lists all 8 available palettes."""
    result = runner.invoke(octos_app, ["theme"])
    assert result.exit_code == 0
    assert "Available Developer Palettes" in result.stdout
    assert "catppuccin" in result.stdout
    assert "dracula" in result.stdout
    assert "tokyo-night" in result.stdout


def test_cli_theme_switch_command(monkeypatch, tmp_path):
    """Verify 'octos theme <id>' switches theme."""
    fake_config = tmp_path / ".octoflow"
    fake_theme_file = fake_config / "theme.json"
    monkeypatch.setattr("octoflow.themes._CONFIG_DIR", fake_config)
    monkeypatch.setattr("octoflow.themes._THEME_FILE", fake_theme_file)

    result = runner.invoke(octos_app, ["theme", "nord"])
    assert result.exit_code == 0
    assert "Switched palette to: Nord Arctic" in result.stdout


def test_render_theme_selector_panel():
    """Verify render_theme_selector_panel renders all 8 developer palettes and preview bar without error."""
    from octoflow.theme_selector import render_theme_selector_panel

    themes_list = list(THEMES.items())

    for idx in range(len(themes_list)):
        panel = render_theme_selector_panel(idx, themes_list)
        assert panel is not None
        assert "Developer Themes" in str(panel.title)
        assert "ENTER" in str(panel.subtitle)
        assert "k" in str(panel.subtitle).lower()
        assert "j" in str(panel.subtitle).lower()


def test_interactive_theme_picker_non_tty():
    """Verify run_interactive_theme_picker falls back gracefully in non-interactive/CI environments."""
    from octoflow.theme_selector import run_interactive_theme_picker
    from rich.console import Console

    test_console = Console(record=True)
    initial = get_theme("catppuccin")
    # In pytest/runner, sys.stdin.isatty() is False
    chosen = run_interactive_theme_picker(test_console, initial_theme=initial)
    assert chosen.id == "catppuccin"
    output = test_console.export_text()
    assert "OctoFlow Developer Themes" in output
    assert "catppuccin" in output


def test_theme_dynamic_banner_colors():
    """Verify that every theme produces a unique 8-letter banner palette and shadow."""
    from octoflow.themes import get_theme_banner_colors

    palettes_seen = set()
    for theme_id, theme_obj in THEMES.items():
        colors, shadow = get_theme_banner_colors(theme_obj)
        assert len(colors) == 8, f"Theme {theme_id} must have 8 letter colors"
        assert all(c.startswith("#") for c in colors), f"All colors in {theme_id} must be hex"
        assert shadow.startswith("#"), f"Shadow in {theme_id} must be hex"
        palettes_seen.add(tuple(colors))

    # All 8 themes must have distinct letter palettes
    assert len(palettes_seen) == 8


def test_render_octoflow_3d_banner_all_themes():
    """Verify 3D banner renders cleanly with theme name for every theme."""
    from octoflow.themes import render_octoflow_3d_banner
    from rich.console import Console

    test_console = Console(record=True)
    for theme_id, theme_obj in THEMES.items():
        banner = render_octoflow_3d_banner(theme_obj)
        test_console.print(banner)
        output = test_console.export_text()
        assert "OCTOFLOW" in output
        assert f"Theme: {theme_obj.name}" in output


def test_get_banner_animation_frames_all_themes():
    """Verify that every theme generates valid 3D animation frames."""
    from octoflow.themes import get_banner_animation_frames

    for theme_id, theme_obj in THEMES.items():
        frames = get_banner_animation_frames(theme_obj)
        assert len(frames) >= 4, f"Theme {theme_id} must have at least 4 animation frames"
        for frame in frames:
            assert frame is not None


def test_play_banner_animation_headless():
    """Verify play_banner_animation completes safely in headless mode."""
    from octoflow.themes import play_banner_animation
    from rich.console import Console

    test_console = Console(record=True)
    # Headless execution
    play_banner_animation(test_console, delay=0.001)
    output = test_console.export_text()
    assert "OCTOFLOW" in output


def test_prompt_prefix_stripping():
    """Verify that copy-pasted prompts like 'octos ❯ /theme' or './octos theme' are properly stripped to '/theme' or 'theme'."""
    raw_inputs = [
        "octos ❯ octos ❯ /theme",
        "octos ❯ /banner",
        "octos > /help",
        "❯ /theme catppuccin",
        "> /clear",
        "octo ❯ /exit",
        "./octos theme",
        "./octo theme",
        "octos theme",
        "./octos /banner",
    ]
    expected = [
        "/theme",
        "/banner",
        "/help",
        "/theme catppuccin",
        "/clear",
        "/exit",
        "theme",
        "theme",
        "theme",
        "/banner",
    ]
    for inp, exp in zip(raw_inputs, expected):
        user_input = inp.strip()
        while True:
            prev_len = len(user_input)
            for prefix in [
                "octos ❯",
                "octos >",
                "octos:",
                "octo ❯",
                "octo >",
                "❯",
                ">",
                "$",
                "#",
                "./octos ",
                "./octo ",
                "octos ",
                "octo ",
            ]:
                if user_input.startswith(prefix):
                    user_input = user_input[len(prefix) :].strip()
            if len(user_input) == prev_len:
                break
        assert user_input == exp


def test_cli_run_sandbox_mode_default_direct_call(monkeypatch, tmp_path):
    """Verify that calling cli.run directly as a Python function doesn't fail Pydantic validation on sandbox_mode."""
    from octoflow.cli import run

    mock_executed = False

    def mock_run_swarm(self, objective, **kwargs):
        nonlocal mock_executed
        mock_executed = True
        return {"objective": objective, "status": "completed"}

    from octoflow.conductor import SupraesophagealConductor

    monkeypatch.setattr(SupraesophagealConductor, "run_swarm", mock_run_swarm)

    # Calling run without sandbox argument should normalize OptionInfo to 'local'
    run(
        objective="test goal",
        mode="software_dev",
        guild=None,
        octos=1,
        model="mock",
        budget=1.0,
        workspace=str(tmp_path),
        port=8099,
        open_ui=False,
        theme="abyssal",
        no_checkpoint=True,
    )
    assert mock_executed is True


def test_get_banner_loop_frame_all_themes():
    """Verify that every theme produces valid continuous loop frames across a full cycle."""
    from octoflow.themes import get_banner_loop_frame

    for theme_id, theme_obj in THEMES.items():
        for tick in range(24):
            frame = get_banner_loop_frame(theme_obj, tick=tick, subtitle="TEST SUBTITLE")
            assert frame is not None
            text_content = frame.plain
            assert "OCTOFLOW" in text_content
            assert "TEST SUBTITLE" in text_content


def test_play_banner_continuous_headless():
    """Verify that play_banner_continuous runs safely and renders in headless/test environments."""
    from octoflow.themes import play_banner_continuous
    from rich.console import Console

    test_console = Console(record=True)
    # Headless execution
    play_banner_continuous(test_console, max_ticks=2)
    output = test_console.export_text()
    assert "OCTOFLOW" in output


def test_cli_banner_and_screensaver_commands(monkeypatch):
    """Verify the CLI top-level banner and screensaver commands execute without error."""
    from octoflow.cli import app_banner_cmd, app_screensaver_cmd

    banner_called = False
    continuous_called = False

    def mock_anim(console, theme=None, delay=0.05):
        nonlocal banner_called
        banner_called = True

    def mock_cont(console, theme=None, delay=0.045, max_ticks=None, prompt_message=""):
        nonlocal continuous_called
        continuous_called = True

    monkeypatch.setattr("octoflow.themes.play_banner_animation", mock_anim)
    monkeypatch.setattr("octoflow.themes.play_banner_continuous", mock_cont)

    app_banner_cmd(loop=False, theme="catppuccin")
    assert banner_called is True

    app_banner_cmd(loop=True, theme="dracula")
    assert continuous_called is True

    continuous_called = False
    app_screensaver_cmd(theme="cyberpunk")
    assert continuous_called is True
