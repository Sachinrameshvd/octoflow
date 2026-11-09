"""Tests for the automated documentation checker (scripts/check_docs.py)."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from scripts.check_docs import check_docs, extract_anchors, heading_to_slug, is_emoji, main


def test_docs_checker_passes_on_repo() -> None:
    """Verifies that the entire OctoFlow documentation tree passes all checks with 0 errors."""
    errors = check_docs()
    assert not errors, f"Documentation checks failed with {len(errors)} error(s):\n" + "\n".join(errors)


def test_heading_slug_generation() -> None:
    """Verifies GitHub-compatible anchor slug transformation."""
    assert heading_to_slug("1. Getting Started") == "1-getting-started"
    assert heading_to_slug("Execution Modes & Truthful Outcomes") == "execution-modes-truthful-outcomes"
    assert heading_to_slug("E-PROV-AUTH: Invalid API Key") == "e-prov-auth-invalid-api-key"
    assert heading_to_slug("Step 2: Run `octoflow doctor`") == "step-2-run-octoflow-doctor"


def test_emoji_detection() -> None:
    """Verifies zero-emoji policy: true emojis fail, approved semantic glyphs pass."""
    # Approved glyphs from P6.3 policy
    assert not is_emoji("✔")
    assert not is_emoji("✖")
    assert not is_emoji("•")
    assert not is_emoji("·")
    assert not is_emoji("○")
    assert not is_emoji("◈")
    assert not is_emoji("●")
    assert not is_emoji("a")
    assert not is_emoji("-")

    # Forbidden wide emojis
    assert is_emoji("🐙")
    assert is_emoji("⚡")
    assert is_emoji("🚀")
    assert is_emoji("🔥")
    assert is_emoji("⏳")


def test_detects_broken_relative_link(tmp_path: Path) -> None:
    """Verifies broken relative file links are detected."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("[Read more](non_existent_file.md)", encoding="utf-8")

    errors = check_docs(tmp_path)
    assert any("[Broken Link]" in err and "non_existent_file.md" in err for err in errors)


def test_detects_broken_anchor(tmp_path: Path) -> None:
    """Verifies broken markdown anchor targets are detected."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "target.md").write_text("# Target Section\nContent", encoding="utf-8")
    (docs / "caller.md").write_text("[Target](target.md#missing-section)", encoding="utf-8")

    errors = check_docs(tmp_path)
    assert any("[Broken Anchor]" in err and "#missing-section" in err for err in errors)


def test_detects_broken_in_file_anchor(tmp_path: Path) -> None:
    """Verifies broken in-file anchors (#section) are detected."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "page.md").write_text(
        "# Real Heading\n[Jump](#phantom-heading)",
        encoding="utf-8",
    )

    errors = check_docs(tmp_path)
    assert any("[Broken In-File Anchor]" in err and "#phantom-heading" in err for err in errors)


def test_detects_unknown_cli_command(tmp_path: Path) -> None:
    """Verifies unregistered octoflow subcommands are flagged."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "run_example.md").write_text(
        "Run `octoflow bogus_nonexistent_command_xyz` to test.",
        encoding="utf-8",
    )

    errors = check_docs(tmp_path)
    assert any("[Unknown Subcommand]" in err and "bogus_nonexistent_command_xyz" in err for err in errors)


def test_detects_forbidden_emoji(tmp_path: Path) -> None:
    """Verifies emojis are caught by docs checker."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "emoji.md").write_text("Great job! 🚀", encoding="utf-8")

    errors = check_docs(tmp_path)
    assert any("[Emoji]" in err and "🚀" in err for err in errors)


def test_detects_absolute_user_paths(tmp_path: Path) -> None:
    """Verifies absolute user paths (/Users/... or /home/...) are flagged."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "paths.md").write_text(
        "Logs saved to /Users/johndoe/project/logs.txt",
        encoding="utf-8",
    )

    errors = check_docs(tmp_path)
    assert any("[Absolute Path]" in err and "/Users/johndoe/" in err for err in errors)


def test_docs_checker_main_exit_code() -> None:
    """Verifies main() returns 0 on clean repository."""
    exit_code = main()
    assert exit_code == 0
