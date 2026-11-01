"""Test Glyph Policy, Single-Width Presentation, and Central Glyph Table.

P6.3 Standards:
- Zero-Emoji: Every active glyph has wcwidth == 1 and no emoji presentation.
- ASCII Fallback: Every glyph provides a single-width ASCII fallback (< 128).
- Central Table: All glyphs defined in octoflow/glyphs.py.
- Codebase Cleanliness: Zero wide characters (wcwidth > 1) in octoflow/ sources.
"""

import os
from pathlib import Path

import pytest
import wcwidth

from octoflow.glyphs import (
    GLYPH_TABLE,
    Glyph,
    glyph,
    is_ascii_mode,
    is_legacy_glyphs,
    is_no_anim,
    is_no_color,
    is_plain_mode,
    reset_glyph_modes,
    sanitize_text,
    set_ascii_mode,
    set_legacy_glyphs_mode,
    set_no_anim_mode,
    set_no_color_mode,
    set_plain_mode,
)


@pytest.fixture(autouse=True)
def clean_glyph_modes():
    """Ensure clean mode state before and after each test."""
    reset_glyph_modes()
    yield
    reset_glyph_modes()


def test_glyph_table_widths():
    """All glyphs in GLYPH_TABLE must have wcwidth == 1 and ASCII < 128."""
    assert len(GLYPH_TABLE) >= 20
    for name, g in GLYPH_TABLE.items():
        assert isinstance(g, Glyph)
        assert g.name == name
        u_w = wcwidth.wcwidth(g.unicode)
        assert u_w == 1, f"Glyph '{name}' unicode '{g.unicode}' (U+{ord(g.unicode):04X}) has width {u_w} != 1"
        a_w = wcwidth.wcwidth(g.ascii)
        assert a_w == 1, f"Glyph '{name}' ascii '{g.ascii}' has width {a_w} != 1"
        assert ord(g.ascii) < 128, f"Glyph '{name}' ascii '{g.ascii}' ord >= 128"


def test_glyph_lookup_defaults():
    """Default mode produces single-width Unicode symbols."""
    assert glyph("OK") == "✓"
    assert glyph("FAIL") == "✗"
    assert glyph("BOLT") == "↯"
    assert glyph("WARN") == "▲"
    assert glyph("DIAMOND") == "◈"
    assert glyph("BULLET") == "•"
    assert glyph("MIDDLE_DOT") == "·"
    assert glyph("HOURGLASS") == "·"


def test_glyph_ascii_mode():
    """ASCII mode produces strictly ASCII characters < 128 with width 1."""
    set_ascii_mode(True)
    assert is_ascii_mode() is True

    for name, g in GLYPH_TABLE.items():
        char = glyph(name)
        assert ord(char) < 128
        assert wcwidth.wcwidth(char) == 1

    assert glyph("OK") == "+"
    assert glyph("FAIL") == "x"
    assert glyph("BOLT") == "!"
    assert glyph("WARN") == "!"
    assert glyph("DIAMOND") == "*"
    assert glyph("HOURGLASS") == "~"


def test_glyph_legacy_mode():
    """Legacy mode retains original symbols for transition compatibility."""
    set_legacy_glyphs_mode(True)
    assert is_legacy_glyphs() is True

    assert glyph("OK") == "✔"
    assert glyph("FAIL") == "✖"
    assert glyph("BOLT") == "⚡"


def test_dynamic_module_attribute_access():
    """Direct import from octoflow.glyphs resolves glyphs cleanly."""
    import octoflow.glyphs as g

    assert g.OK == "✓"
    assert g.FAIL == "✗"
    assert g.BOLT == "↯"
    assert g.DIAMOND == "◈"

    with pytest.raises(AttributeError):
        _ = g.NONEXISTENT_GLYPH_XYZ


def test_unknown_glyph_name_raises():
    """Querying an unknown glyph name raises KeyError with available list."""
    with pytest.raises(KeyError) as exc_info:
        glyph("UNKNOWN_NAME")
    assert "Unknown glyph name" in str(exc_info.value)


def test_sanitize_text():
    """Sanitize converts wide/legacy emojis to compliant single-width symbols."""
    text = "Status: ⚡ Active, ✔ Completed, ✖ Failed, ⏳ Waiting"
    sanitized = sanitize_text(text)
    assert "⚡" not in sanitized
    assert "✔" not in sanitized
    assert "✖" not in sanitized
    assert "⏳" not in sanitized
    assert "↯" in sanitized
    assert "✓" in sanitized
    assert "✗" in sanitized

    # In ASCII mode
    set_ascii_mode(True)
    ascii_sanitized = sanitize_text("◈ OctoFlow [✓] ↯ Complete! — Done")
    assert all(ord(c) < 128 for c in ascii_sanitized)
    assert "*" in ascii_sanitized
    assert "+" in ascii_sanitized
    assert "!" in ascii_sanitized


def test_no_wide_characters_in_octoflow_source():
    """Zero-Emoji Policy Audit: No python source file in octoflow/ may contain wcwidth > 1."""
    octoflow_dir = Path(__file__).resolve().parent.parent / "octoflow"
    violations = []

    for py_file in octoflow_dir.rglob("*.py"):
        if py_file.name == "glyphs.py":
            continue  # glyphs.py defines the legacy fallback table
        content = py_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            for ch in line:
                if ord(ch) >= 128 and wcwidth.wcwidth(ch) > 1:
                    violations.append(f"{py_file.relative_to(octoflow_dir.parent)}:{line_no} U+{ord(ch):04X} '{ch}'")

    assert not violations, f"Found wide characters (wcwidth > 1) violating Zero-Emoji policy:\n" + "\n".join(violations)


def test_modes_environment_detection(monkeypatch):
    """Test environment variable auto-detection for accessibility modes."""
    monkeypatch.setenv("NO_COLOR", "1")
    assert is_no_color() is True

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "dumb")
    assert is_no_color() is True
    assert is_no_anim() is True

    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.setenv("OCTOFLOW_ANIM", "0")
    assert is_no_anim() is True

    monkeypatch.delenv("OCTOFLOW_ANIM", raising=False)
    monkeypatch.setenv("OCTOFLOW_ASCII", "1")
    assert is_ascii_mode() is True

    monkeypatch.delenv("OCTOFLOW_ASCII", raising=False)
    monkeypatch.setenv("OCTOFLOW_PLAIN", "1")
    assert is_plain_mode() is True
