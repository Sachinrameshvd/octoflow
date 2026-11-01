"""Tests for OctoFlow message catalog, empty states, help UX, and command suggestions (P6.2)."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from rich.console import Console
from typer.testing import CliRunner

from octoflow.cli import app, octos_app
from octoflow.cockpit.app import COCKPIT_COMMANDS
from octoflow.errors import OctoFlowError
from octoflow.messages import (
    EMPTY_STATES,
    ERROR_CATALOG,
    GLOSSARY,
    PLAIN_LANGUAGE_SUMMARY,
    CatalogEntry,
    EmptyState,
    format_empty_state,
    format_unknown_command,
    get_catalog_entry,
    get_catalog_entry_for_class,
    get_empty_state,
    render_glossary_table,
    suggest_command,
)

SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots" / "messages"


def _get_all_subclasses(cls: type[OctoFlowError]) -> set[type[OctoFlowError]]:
    """Recursively collect all subclasses of OctoFlowError."""
    subclasses = set(cls.__subclasses__())
    for sub in list(subclasses):
        subclasses.update(_get_all_subclasses(sub))
    return subclasses


# =============================================================================
# 1. Catalog Coverage
# =============================================================================


def test_every_octoflow_error_subclass_has_catalog_entry():
    """Verify that every OctoFlowError subclass has an associated catalog entry."""
    subclasses = _get_all_subclasses(OctoFlowError)
    assert len(subclasses) >= 10, f"Expected at least 10 subclasses, got {len(subclasses)}"

    for sub in subclasses:
        entry = get_catalog_entry_for_class(sub)
        assert isinstance(
            entry, CatalogEntry
        ), f"Class {sub.__name__} did not resolve to a CatalogEntry"
        assert entry.code.startswith("E-"), f"Entry for {sub.__name__} has invalid code: {entry.code}"
        assert entry.title, f"Entry for {sub.__name__} missing title"
        assert entry.cause, f"Entry for {sub.__name__} missing cause"
        assert entry.consequence, f"Entry for {sub.__name__} missing consequence"
        assert entry.next_step, f"Entry for {sub.__name__} missing next_step"
        assert entry.hint, f"Entry for {sub.__name__} missing hint"
        assert entry.docs_anchor.startswith("docs/TROUBLESHOOTING.md#")


def test_troubleshooting_has_anchor_for_every_error_code():
    """Verify docs/TROUBLESHOOTING.md has an explicit anchor for every catalog code."""
    troubleshooting_path = (
        Path(__file__).resolve().parent.parent / "docs" / "TROUBLESHOOTING.md"
    )
    assert troubleshooting_path.exists(), f"Missing {troubleshooting_path}"
    content = troubleshooting_path.read_text(encoding="utf-8")

    for code, entry in ERROR_CATALOG.items():
        anchor_slug = code.lower()
        # Accept either <a id="e-xxxx"> or header anchor #e-xxxx
        has_tag = f'id="{anchor_slug}"' in content or f'name="{anchor_slug}"' in content
        has_anchor_link = f"#{anchor_slug}" in content
        assert (
            has_tag and has_anchor_link
        ), f"docs/TROUBLESHOOTING.md is missing anchor for {code} ({anchor_slug})"


# =============================================================================
# 2. Command Suggestions
# =============================================================================


def test_unknown_command_suggestions():
    """Verify difflib command suggestions for mistyped cockpit commands."""
    commands = COCKPIT_COMMANDS

    # /modle -> /model
    matches = suggest_command("/modle", commands)
    assert "/model" in matches
    suggestion_msg = format_unknown_command("/modle", commands)
    assert "Did you mean '/model'?" in suggestion_msg

    # /heal typos
    assert "/heal" in suggest_command("/hela", commands)
    assert "/export" in suggest_command("/exprot", commands)
    assert "/doctor" in suggest_command("/doctr", commands)
    assert "/rollback" in suggest_command("/rolback", commands)

    # Completely alien command
    alien_msg = format_unknown_command("/totallyboguscommandxyz", commands)
    assert "Unknown command '/totallyboguscommandxyz'" in alien_msg
    assert "Type '/help'" in alien_msg


# =============================================================================
# 3. Empty States
# =============================================================================


def test_empty_states_exist_for_all_listed_situations():
    """Verify empty states exist for all 7 listed situations."""
    expected_situations = [
        "no_runs",
        "no_memory",
        "no_reports",
        "no_providers",
        "no_ollama",
        "not_git_repo",
        "no_tests_found",
    ]

    for sit in expected_situations:
        assert sit in EMPTY_STATES, f"Missing empty state for '{sit}'"
        es = get_empty_state(sit)
        assert isinstance(es, EmptyState)
        assert es.friendly_line, f"Empty state '{sit}' missing friendly_line"
        assert es.command_to_try, f"Empty state '{sit}' missing command_to_try"
        formatted = format_empty_state(sit)
        assert es.friendly_line in formatted
        assert es.command_to_try in formatted
        assert "Try:" in formatted


# =============================================================================
# 4. Help and Glossary
# =============================================================================


def test_plain_language_help_and_glossary():
    """Verify plain-language help summary and 5-concept metaphor glossary."""
    # Summary
    assert "autonomous multi-agent coding framework" in PLAIN_LANGUAGE_SUMMARY
    assert "checkpoint safety" in PLAIN_LANGUAGE_SUMMARY

    # Glossary terms
    required_terms = ["Conductor", "Arm", "Gate", "Bus", "Vertical Lobe"]
    for term in required_terms:
        assert term in GLOSSARY
        assert GLOSSARY[term], f"Missing definition for {term}"

    # Verify CLI command 'octoflow glossary'
    runner = CliRunner()
    result = runner.invoke(app, ["glossary"])
    assert result.exit_code == 0
    for term in required_terms:
        assert term in result.output


# =============================================================================
# 5. Snapshot Tests
# =============================================================================


def test_message_snapshots():
    """Snapshot test error messages, empty states, and suggestions."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    update = os.getenv("UPDATE_SNAPSHOTS") == "1"

    # 1. Catalog errors
    for code, entry in ERROR_CATALOG.items():
        c = Console(record=True, width=100, color_system=None)
        c.print(f"[bold red]{entry.code}[/bold red] {entry.cause}")
        c.print(f"[dim]Consequence:[/dim] {entry.consequence}")
        c.print(f"[bold cyan]Next Step:[/bold cyan] {entry.next_step}")
        c.print(f"[yellow]Hint:[/yellow] {entry.hint}")
        rendered = c.export_text()

        filename = SNAPSHOT_DIR / f"{code.lower().replace('-', '_')}.txt"
        if update:
            filename.write_text(rendered, encoding="utf-8")
        assert filename.exists(), f"Snapshot {filename} missing"
        expected = filename.read_text(encoding="utf-8")
        assert rendered == expected, f"Snapshot mismatch for {code}"

    # 2. Empty states
    for key, es in EMPTY_STATES.items():
        c = Console(record=True, width=100, color_system=None)
        c.print(f"[dim]{es.friendly_line}[/dim]")
        c.print(f"Try: [bold cyan]{es.command_to_try}[/bold cyan]")
        rendered = c.export_text()

        filename = SNAPSHOT_DIR / f"empty_{key}.txt"
        if update:
            filename.write_text(rendered, encoding="utf-8")
        assert filename.exists(), f"Snapshot {filename} missing"
        expected = filename.read_text(encoding="utf-8")
        assert rendered == expected, f"Snapshot mismatch for empty_{key}"

    # 3. Suggestion /modle -> /model
    c = Console(record=True, width=100, color_system=None)
    c.print(format_unknown_command("/modle", COCKPIT_COMMANDS))
    rendered = c.export_text()
    filename = SNAPSHOT_DIR / "suggest_modle.txt"
    if update:
        filename.write_text(rendered, encoding="utf-8")
    assert filename.exists(), f"Snapshot {filename} missing"
    assert rendered == filename.read_text(encoding="utf-8")

    # 4. Glossary table
    c = Console(record=True, width=100, color_system=None)
    c.print(render_glossary_table(c))
    rendered = c.export_text()
    filename = SNAPSHOT_DIR / "glossary.txt"
    if update:
        filename.write_text(rendered, encoding="utf-8")
    assert filename.exists(), f"Snapshot {filename} missing"
    assert rendered == filename.read_text(encoding="utf-8")
