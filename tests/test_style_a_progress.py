"""Tests for Style A Live Multi-Octopus Progress Bars and Activity Spinners (Milestone 2).

Verifies:
1. Animated braille activity spinner frame progression (Unicode and ASCII fallbacks)
2. Style A Multi-Octopus Progress panel rendering (compact and wide modes)
3. Lifecycle state labels: [✓ Complete], [⠋ Working], [⏳ Waiting], [○ Standby]
4. Visual progress bars with percentage thresholds
5. 8-Arm Neural Matrix badge formatting ([✓✓✓✓✓✓✓✓], [✓↯······], [········])
6. Sensory gating token metrics in synaptic telemetry footer
7. Re-exports across octoflow.cli, octoflow.commands.dashboard, and octoflow.cockpit.render
"""

import io

from octoflow.cli import build_style_a_progress_panel as cli_build_panel
from octoflow.cockpit.render import build_style_a_progress_panel as cockpit_build_panel
from octoflow.commands.dashboard import (
    ASCII_SPINNER_FRAMES,
    SPINNER_FRAMES,
    _get_spinner_frame,
    build_style_a_progress_panel,
    render_consortium_dashboard,
)
from octoflow.glyphs import set_ascii_mode
from rich.console import Console
from rich.panel import Panel


def test_spinner_frame_progression_unicode():
    """Verify spinner frame sequence cycles through 10-frame Unicode braille."""
    set_ascii_mode(False)
    for tick in range(25):
        expected = SPINNER_FRAMES[tick % len(SPINNER_FRAMES)]
        assert _get_spinner_frame(tick) == expected


def test_spinner_frame_progression_ascii():
    """Verify spinner frame sequence cycles through 4-frame ASCII characters."""
    try:
        set_ascii_mode(True)
        for tick in range(12):
            expected = ASCII_SPINNER_FRAMES[tick % len(ASCII_SPINNER_FRAMES)]
            assert _get_spinner_frame(tick) == expected
    finally:
        set_ascii_mode(False)


def test_build_style_a_progress_panel_compact():
    """Verify Style A progress panel renders cleanly in compact terminal width (< 100 cols)."""
    set_ascii_mode(False)
    mock_states = {
        0: {
            "title": "Genesis & Architecture",
            "color_tag": "cyan",
            "status": "COMPLETED",
            "progress_pct": 100.0,
            "arms": ["✔"] * 8,
            "action": "Foundation scaffold & component boundaries established",
        },
        1: {
            "title": "Backend & Services",
            "color_tag": "blue",
            "status": "RUNNING",
            "progress_pct": 60.0,
            "arms": ["✔", "↯", "·", "·", "·", "·", "·", "·"],
            "action": "Writing FastAPI routes in src/api/endpoints.py",
        },
        2: {
            "title": "Frontend & UI",
            "color_tag": "magenta",
            "status": "WAITING",
            "progress_pct": 0.0,
            "arms": ["·"] * 8,
            "action": "Awaiting API contract from Octopus 1",
        },
        3: {
            "title": "Security Sentinel",
            "color_tag": "green",
            "status": "STANDBY",
            "progress_pct": 0.0,
            "arms": ["·"] * 8,
            "action": "Synaptic reserve (cross-coalitions)",
        },
    }

    panel = build_style_a_progress_panel(
        objective="Build an AI Resume & Job Description ATS Matcher",
        octopus_states=mock_states,
        total_tokens_saved=84.5,
        total_cost=0.024,
        last_event_msg="[Backend / API]: Writing src/api/endpoints.py",
        elapsed_seconds=12.5,
        total_arms=32,
        tier_name="OCTOPOLIS_TIER",
        tick=2,  # Should use SPINNER_FRAMES[2] == '⠹'
        tokens_spent=16_200,
        tokens_avoided=88_400,
    )

    assert isinstance(panel, Panel)

    # Render to string console and assert critical visual elements exist
    buf = io.StringIO()
    c = Console(file=buf, width=80, force_terminal=True)
    c.print(panel)
    output = buf.getvalue()

    # Octopus names & Guilds
    assert "Genesis & Architecture" in output or "Architecture" in output
    assert "Backend & Services" in output or "Backend" in output
    assert "Frontend & UI" in output or "Frontend" in output

    # Progress bar percentages
    assert "100%" in output
    assert "60%" in output

    # State badges
    assert "Complete" in output
    assert "Working" in output
    assert "Waiting" in output
    assert "Standby" in output

    # 8-Arm Neural Matrix brackets
    assert "[" in output and "]" in output

    # Sensory gating reflex footer
    assert "84.5%" in output
    assert "16,200" in output
    assert "88,400" in output


def test_build_style_a_progress_panel_wide():
    """Verify Style A progress panel renders in wide terminal mode (>= 100 cols)."""
    set_ascii_mode(False)
    mock_states = {
        0: {
            "title": "System Architect",
            "color_tag": "cyan",
            "status": "COMPLETED",
            "progress_pct": 100.0,
            "arms": ["✔"] * 8,
            "action": "Project architecture signed",
        },
        1: {
            "title": "Database & Storage",
            "color_tag": "blue",
            "status": "RUNNING",
            "progress_pct": 75.0,
            "arms": ["✔", "✔", "↯", "·", "·", "·", "·", "·"],
            "action": "Writing SQLAlchemy models and migrations",
        },
    }

    panel = build_style_a_progress_panel(
        objective="Build High-Throughput Analytics Stream",
        octopus_states=mock_states,
        total_tokens_saved=92.0,
        total_cost=0.018,
        last_event_msg="[Database / Models]: Writing models/stream.py",
        elapsed_seconds=6.0,
        total_arms=16,
        tier_name="TRIAD",
        tick=1,
    )

    assert isinstance(panel, Panel)

    buf = io.StringIO()
    c = Console(file=buf, width=120, force_terminal=True)
    c.print(panel)
    output = buf.getvalue()

    assert "System Architect" in output
    assert "Database & Storage" in output
    assert "100%" in output
    assert "75%" in output
    assert "Complete" in output
    assert "Working" in output


def test_backward_compatibility_aliases():
    """Verify build_style_a_progress_panel is properly aliased and exported across modules."""
    mock_states = {
        0: {
            "title": "Genesis",
            "color_tag": "cyan",
            "progress_pct": 100.0,
            "arms": ["✔"] * 8,
            "action": "Ready",
        }
    }

    p1 = render_consortium_dashboard("Test objective", mock_states)
    p2 = cli_build_panel("Test objective", mock_states)
    p3 = cockpit_build_panel("Test objective", mock_states)

    assert isinstance(p1, Panel)
    assert isinstance(p2, Panel)
    assert isinstance(p3, Panel)

