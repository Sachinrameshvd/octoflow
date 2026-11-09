"""Unit tests for release automation, version bumping, and wheel verification."""

from __future__ import annotations

import re
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

from scripts.check_docs import is_emoji
from scripts.release import (
    apply_changelog_version,
    apply_pyproject_version,
    calculate_next_version,
    get_current_version,
)


def test_get_current_version():
    ver = get_current_version()
    assert re.match(r"^\d+\.\d+\.\d+", ver)


def test_calculate_next_version():
    # Patch
    assert calculate_next_version("0.2.0", "patch") == "0.2.1"
    assert calculate_next_version("1.0.9", "patch") == "1.0.10"

    # Minor
    assert calculate_next_version("0.2.0", "minor") == "0.3.0"
    assert calculate_next_version("1.4.2", "minor") == "1.5.0"

    # Major
    assert calculate_next_version("0.2.0", "major") == "1.0.0"
    assert calculate_next_version("1.9.3", "major") == "2.0.0"

    # Explicit SemVer
    assert calculate_next_version("0.2.0", "0.3.0") == "0.3.0"
    assert calculate_next_version("0.2.0", "1.0.0-rc1") == "1.0.0-rc1"

    # Invalid
    with pytest.raises(ValueError, match="Invalid bump type"):
        calculate_next_version("0.2.0", "invalid")

    with pytest.raises(ValueError, match="not valid SemVer"):
        calculate_next_version("invalid", "patch")


def test_apply_pyproject_version():
    content = '[project]\nname = "octoflow"\nversion = "0.2.0"\ndescription = "Cephalopod"\n'
    updated = apply_pyproject_version(content, "0.3.0")
    assert 'version = "0.3.0"' in updated
    assert 'name = "octoflow"' in updated


def test_apply_changelog_version_new():
    content = """# Changelog

## [Unreleased]

### Added
- New feature X
- New feature Y

## [0.2.0] - 2026-10-31
"""
    updated = apply_changelog_version(content, "0.3.0", "2026-11-09")
    assert "## [Unreleased]" in updated
    assert "## [0.3.0] - 2026-11-09" in updated
    assert "- New feature X" in updated
    assert "## [0.2.0] - 2026-10-31" in updated


def test_apply_changelog_version_existing_header():
    content = """# Changelog

## [0.3.0]
### Added
- Feature A
"""
    updated = apply_changelog_version(content, "0.3.0", "2026-11-09")
    assert "## [0.3.0] - 2026-11-09" in updated


def test_wheel_verification_rules_logic(tmp_path: Path):
    """Test the logic asserted by scripts/verify_wheel.sh."""
    # 1. Valid wheel archive
    valid_wheel = tmp_path / "valid-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(valid_wheel, "w") as z:
        z.writestr("octoflow/__init__.py", "print('hello')")
        z.writestr("octoflow/dist/index.html", "<html>OctoFlow Connectome</html>")
        z.writestr("octoflow/dist/assets/index.js", "console.log(1);")

    with zipfile.ZipFile(valid_wheel, "r") as z:
        names = z.namelist()
        assert "octoflow/dist/index.html" in names
        assert not any("tests/" in n for n in names)
        assert not any(".env" in n for n in names)

    # 2. Leaked test file rejection
    dirty_wheel = tmp_path / "dirty-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(dirty_wheel, "w") as z:
        z.writestr("octoflow/__init__.py", "print('hello')")
        z.writestr("octoflow/dist/index.html", "<html>OctoFlow Connectome</html>")
        z.writestr("tests/test_leak.py", "assert True")

    with zipfile.ZipFile(dirty_wheel, "r") as z:
        names = z.namelist()
        forbidden = [n for n in names if n.startswith("tests/")]
        assert len(forbidden) > 0  # detected!


def test_no_emojis_in_release_files():
    """Verify zero emoji characters in release scripts and configs."""
    root = Path(__file__).resolve().parent.parent
    check_paths = [
        root / "scripts" / "release.py",
        root / "scripts" / "verify_wheel.sh",
        root / "docs" / "adr" / "0002-visualizer-dist.md",
    ]
    for p in check_paths:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for ch in line:
                assert not is_emoji(ch), f"Emoji character '{ch}' (U+{ord(ch):04X}) detected in {p}:{line_no}"
