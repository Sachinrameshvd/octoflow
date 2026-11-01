"""Central glyph table, single-width text presentation, and terminal accessibility modes.

P6.3 Standards:
- Zero-Emoji: Every active glyph has wcwidth == 1 and no emoji presentation.
- ASCII Fallback: Every glyph provides a single-width ASCII fallback (ord < 128).
- NO_COLOR: Respects the https://no-color.org standard (NO_COLOR env and --no-color flag).
- Non-animated: Respects OCTOFLOW_ANIM=0 and --no-anim.
- Plain non-TTY: In pipes or redirects, disables animation, cursor codes, and cockpit chrome.
- Legacy Option: Retains legacy glyphs selectable via --legacy-glyphs for one release cycle.
"""

from __future__ import annotations

import io
import os
import sys
import unicodedata
from dataclasses import dataclass
from typing import Any

try:
    import wcwidth
except ImportError:
    wcwidth = None

# Global explicit override states (None = auto-detect from env/tty)
_ASCII_OVERRIDE: bool | None = None
_NO_COLOR_OVERRIDE: bool | None = None
_NO_ANIM_OVERRIDE: bool | None = None
_LEGACY_GLYPHS_OVERRIDE: bool | None = None
_PLAIN_MODE_OVERRIDE: bool | None = None


@dataclass(frozen=True)
class Glyph:
    """Individual terminal glyph with Unicode, ASCII fallback, and legacy mapping."""

    name: str
    unicode: str
    ascii: str
    legacy: str = ""

    def __post_init__(self) -> None:
        # Enforce P6.3 Selection Rules
        if wcwidth is not None:
            u_width = wcwidth.wcwidth(self.unicode)
            a_width = wcwidth.wcwidth(self.ascii)
            if u_width != 1:
                raise ValueError(
                    f"Glyph '{self.name}' unicode '{self.unicode}' (U+{ord(self.unicode):04X}) "
                    f"must have wcwidth == 1, got {u_width}"
                )
            if a_width != 1:
                raise ValueError(
                    f"Glyph '{self.name}' ascii '{self.ascii}' "
                    f"must have wcwidth == 1, got {a_width}"
                )
        if ord(self.ascii) >= 128:
            raise ValueError(
                f"Glyph '{self.name}' ascii '{self.ascii}' must be standard ASCII (< 128)"
            )

    @property
    def char(self) -> str:
        """Resolve character according to active terminal accessibility modes."""
        if is_ascii_mode():
            return self.ascii
        if is_legacy_glyphs() and self.legacy:
            return self.legacy
        return self.unicode


# -----------------------------------------------------------------------------
# 1. Central Glyph Table
# -----------------------------------------------------------------------------

GLYPH_TABLE: dict[str, Glyph] = {
    # Check / Success
    "OK": Glyph("OK", unicode="✓", ascii="+", legacy="✔"),
    "CHECK": Glyph("CHECK", unicode="✓", ascii="+", legacy="✔"),
    # Cross / Failure
    "FAIL": Glyph("FAIL", unicode="✗", ascii="x", legacy="✖"),
    "CROSS": Glyph("CROSS", unicode="✗", ascii="x", legacy="✖"),
    # Warning / Triangle
    "WARN": Glyph("WARN", unicode="▲", ascii="!", legacy="▲"),
    "TRIANGLE": Glyph("TRIANGLE", unicode="▲", ascii="!", legacy="▲"),
    # Lightning / Pulse / Action
    "BOLT": Glyph("BOLT", unicode="↯", ascii="!", legacy="⚡"),
    "FLASH": Glyph("FLASH", unicode="↯", ascii="!", legacy="⚡"),
    # Bullets and Dots
    "BULLET": Glyph("BULLET", unicode="•", ascii="*", legacy="•"),
    "DOT": Glyph("DOT", unicode="•", ascii="*", legacy="•"),
    "MIDDLE_DOT": Glyph("MIDDLE_DOT", unicode="·", ascii=".", legacy="·"),
    "POINT": Glyph("POINT", unicode="·", ascii=".", legacy="·"),
    # Circles
    "CIRCLE": Glyph("CIRCLE", unicode="○", ascii="o", legacy="○"),
    "HOLLOW_CIRCLE": Glyph("HOLLOW_CIRCLE", unicode="○", ascii="o", legacy="○"),
    "DISC": Glyph("DISC", unicode="●", ascii="*", legacy="●"),
    "FILLED_CIRCLE": Glyph("FILLED_CIRCLE", unicode="●", ascii="*", legacy="●"),
    # Diamonds
    "DIAMOND": Glyph("DIAMOND", unicode="◈", ascii="*", legacy="◈"),
    "WHITE_DIAMOND": Glyph("WHITE_DIAMOND", unicode="◇", ascii="*", legacy="◇"),
    # Arrows and Pointers
    "ARROW_RIGHT": Glyph("ARROW_RIGHT", unicode="→", ascii=">", legacy="→"),
    "ARROW_LEFT": Glyph("ARROW_LEFT", unicode="←", ascii="<", legacy="←"),
    # Box and UI Structure
    "BAR": Glyph("BAR", unicode="│", ascii="|", legacy="│"),
    "DASH": Glyph("DASH", unicode="─", ascii="-", legacy="─"),
    "BLOCK": Glyph("BLOCK", unicode="█", ascii="#", legacy="█"),
    "SHADE": Glyph("SHADE", unicode="░", ascii="-", legacy="░"),
    "HOURGLASS": Glyph("HOURGLASS", unicode="·", ascii="~", legacy="·"),
}


# -----------------------------------------------------------------------------
# 2. Environment & Mode Queries
# -----------------------------------------------------------------------------


def is_ascii_mode() -> bool:
    """Return True if output must be strictly ASCII (< 128)."""
    if _ASCII_OVERRIDE is not None:
        return _ASCII_OVERRIDE
    if os.getenv("OCTOFLOW_ASCII") == "1":
        if _orig_stdout is None:
            install_ascii_filter()
        return True
    return False


def is_no_color() -> bool:
    """Return True if ANSI color formatting must be omitted (NO_COLOR standard)."""
    if _NO_COLOR_OVERRIDE is not None:
        return _NO_COLOR_OVERRIDE
    if os.getenv("NO_COLOR", "") != "":
        return True
    if os.getenv("OCTOFLOW_NO_COLOR") == "1":
        return True
    if os.getenv("TERM") == "dumb":
        return True
    return False


def is_no_anim() -> bool:
    """Return True if terminal animations and frame refresh loops must be disabled."""
    if _NO_ANIM_OVERRIDE is not None:
        return _NO_ANIM_OVERRIDE
    if os.getenv("OCTOFLOW_ANIM") == "0":
        return True
    if os.getenv("TERM") == "dumb":
        return True
    if not (sys.stdout.isatty() and sys.stdin.isatty()):
        return True
    return False


def is_legacy_glyphs() -> bool:
    """Return True if legacy glyphs (U+2714, U+2716, U+26A1) are requested."""
    if _LEGACY_GLYPHS_OVERRIDE is not None:
        return _LEGACY_GLYPHS_OVERRIDE
    return os.getenv("OCTOFLOW_LEGACY_GLYPHS") == "1"


def is_plain_mode() -> bool:
    """Return True if plain line-oriented output is requested (no cockpit, no Live)."""
    if _PLAIN_MODE_OVERRIDE is not None:
        return _PLAIN_MODE_OVERRIDE
    if os.getenv("OCTOFLOW_PLAIN") == "1":
        return True
    if not sys.stdout.isatty():
        return True
    return False


# -----------------------------------------------------------------------------
# 3. Mode Override Controls (for CLI Flags & Tests)
# -----------------------------------------------------------------------------

_orig_stdout: Any = None
_orig_stderr: Any = None


class AsciiStreamWrapper:
    """Stream wrapper filtering and transliterating writes to standard ASCII (< 128)."""

    def __init__(self, target: Any) -> None:
        self._target = target

    def write(self, s: str) -> int:
        if not s:
            return 0
        cleaned = sanitize_text(s)
        return self._target.write(cleaned)

    def writelines(self, lines: Any) -> None:
        for line in lines:
            self.write(line)

    def flush(self) -> None:
        if hasattr(self._target, "flush"):
            self._target.flush()

    def isatty(self) -> bool:
        if hasattr(self._target, "isatty"):
            return self._target.isatty()
        return False

    def fileno(self) -> int:
        if hasattr(self._target, "fileno"):
            return self._target.fileno()
        raise io.UnsupportedOperation("fileno")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


def install_ascii_filter() -> None:
    """Install ASCII filtering wrapper onto sys.stdout and sys.stderr."""
    global _orig_stdout, _orig_stderr
    if _orig_stdout is None:
        _orig_stdout = sys.stdout
        sys.stdout = AsciiStreamWrapper(_orig_stdout)
    if _orig_stderr is None:
        _orig_stderr = sys.stderr
        sys.stderr = AsciiStreamWrapper(_orig_stderr)


def uninstall_ascii_filter() -> None:
    """Restore original sys.stdout and sys.stderr streams."""
    global _orig_stdout, _orig_stderr
    if _orig_stdout is not None:
        sys.stdout = _orig_stdout
        _orig_stdout = None
    if _orig_stderr is not None:
        sys.stderr = _orig_stderr
        _orig_stderr = None


def set_ascii_mode(enabled: bool | None = None) -> None:
    """Explicitly override ASCII mode."""
    global _ASCII_OVERRIDE
    _ASCII_OVERRIDE = enabled
    if enabled:
        os.environ["OCTOFLOW_ASCII"] = "1"
        install_ascii_filter()
    elif enabled is False:
        os.environ.pop("OCTOFLOW_ASCII", None)
        uninstall_ascii_filter()


def set_no_color_mode(enabled: bool | None = None) -> None:
    """Explicitly override NO_COLOR mode."""
    global _NO_COLOR_OVERRIDE
    _NO_COLOR_OVERRIDE = enabled
    if enabled:
        os.environ["NO_COLOR"] = "1"
        os.environ["OCTOFLOW_NO_COLOR"] = "1"
    elif enabled is False:
        os.environ.pop("NO_COLOR", None)
        os.environ.pop("OCTOFLOW_NO_COLOR", None)


def set_no_anim_mode(enabled: bool | None = None) -> None:
    """Explicitly override animation mode."""
    global _NO_ANIM_OVERRIDE
    _NO_ANIM_OVERRIDE = enabled
    if enabled:
        os.environ["OCTOFLOW_ANIM"] = "0"
    elif enabled is False:
        os.environ.pop("OCTOFLOW_ANIM", None)


def set_legacy_glyphs_mode(enabled: bool | None = None) -> None:
    """Explicitly override legacy glyphs mode."""
    global _LEGACY_GLYPHS_OVERRIDE
    _LEGACY_GLYPHS_OVERRIDE = enabled
    if enabled:
        os.environ["OCTOFLOW_LEGACY_GLYPHS"] = "1"
    elif enabled is False:
        os.environ.pop("OCTOFLOW_LEGACY_GLYPHS", None)


def set_plain_mode(enabled: bool | None = None) -> None:
    """Explicitly override plain line mode."""
    global _PLAIN_MODE_OVERRIDE
    _PLAIN_MODE_OVERRIDE = enabled
    if enabled:
        os.environ["OCTOFLOW_PLAIN"] = "1"
    elif enabled is False:
        os.environ.pop("OCTOFLOW_PLAIN", None)


def reset_glyph_modes() -> None:
    """Reset all mode overrides back to environment detection defaults."""
    global _ASCII_OVERRIDE, _NO_COLOR_OVERRIDE, _NO_ANIM_OVERRIDE, _LEGACY_GLYPHS_OVERRIDE, _PLAIN_MODE_OVERRIDE
    _ASCII_OVERRIDE = None
    _NO_COLOR_OVERRIDE = None
    _NO_ANIM_OVERRIDE = None
    _LEGACY_GLYPHS_OVERRIDE = None
    _PLAIN_MODE_OVERRIDE = None
    os.environ.pop("OCTOFLOW_ASCII", None)
    os.environ.pop("NO_COLOR", None)
    os.environ.pop("OCTOFLOW_NO_COLOR", None)
    os.environ.pop("OCTOFLOW_ANIM", None)
    os.environ.pop("OCTOFLOW_LEGACY_GLYPHS", None)
    os.environ.pop("OCTOFLOW_PLAIN", None)
    uninstall_ascii_filter()


# -----------------------------------------------------------------------------
# 4. Glyph Lookup & Dynamic Module Attributes
# -----------------------------------------------------------------------------


def glyph(name: str) -> str:
    """Resolve a glyph character by name based on active terminal modes."""
    key = name.upper().strip()
    if key in GLYPH_TABLE:
        return GLYPH_TABLE[key].char
    raise KeyError(f"Unknown glyph name '{name}'. Available: {list(GLYPH_TABLE.keys())}")


def sanitize_text(text: str) -> str:
    """Convert any legacy or wide emoji in text to compliant single-width glyphs."""
    if not text:
        return ""
    out = text
    if is_ascii_mode():
        replacements = {
            "✔": "+",
            "✓": "+",
            "✖": "x",
            "✗": "x",
            "▲": "!",
            "▼": "v",
            "⚡": "!",
            "↯": "!",
            "◈": "*",
            "◇": "*",
            "•": "*",
            "●": "*",
            "○": "o",
            "·": ".",
            "⏳": "~",
            "─": "-",
            "│": "|",
            "█": "#",
            "░": "-",
            "→": ">",
            "←": "<",
            "╭": "+",
            "╮": "+",
            "╰": "+",
            "╯": "+",
            "┌": "+",
            "┐": "+",
            "└": "+",
            "┘": "+",
            "├": "+",
            "┤": "+",
            "┬": "+",
            "┴": "+",
            "┼": "+",
            "═": "=",
            "║": "|",
            "’": "'",
            "‘": "'",
            "“": '"',
            "”": '"',
            "—": "--",
            "–": "-",
            "…": "...",
        }
        for k, v in replacements.items():
            out = out.replace(k, v)
        normalized = unicodedata.normalize("NFKD", out)
        out = normalized.encode("ascii", "replace").decode("ascii")
    elif not is_legacy_glyphs():
        replacements = {
            "✔": "✓",
            "✖": "✗",
            "⚡": "↯",
            "⏳": "·",
        }
        for k, v in replacements.items():
            out = out.replace(k, v)
    return out


def __getattr__(name: str) -> str:
    """Allow importing glyphs directly: e.g. from octoflow.glyphs import OK, FAIL."""
    if name in GLYPH_TABLE:
        return GLYPH_TABLE[name].char
    if name.startswith("GLYPH_") and name[6:] in GLYPH_TABLE:
        return GLYPH_TABLE[name[6:]].char
    raise AttributeError(f"module 'octoflow.glyphs' has no attribute '{name}'")
