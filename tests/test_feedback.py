"""Tests for privacy-preserving feedback command and post-run hint (P12.3)."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from unittest.mock import patch

import pytest
from octoflow.cli import app
from octoflow.commands.feedback import (
    build_feedback_issue_url,
    maybe_show_post_run_feedback_hint,
)
from octoflow.settings import Settings, save_settings
from rich.console import Console
from typer.testing import CliRunner

runner = CliRunner()


def is_loopback(host: str) -> bool:
    """Check if host is local loopback."""
    h = str(host).lower().strip()
    return h in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or h.startswith("127.")


@pytest.fixture
def loopback_egress_guard():
    """Verify zero non-loopback egress attempts during execution."""
    attempts: list[tuple[str, str]] = []
    orig_connect = socket.socket.connect

    def guarded_connect(self, address):
        host = address[0] if isinstance(address, (tuple, list)) else address
        port = address[1] if isinstance(address, (tuple, list)) and len(address) > 1 else ""
        if not is_loopback(host):
            attempts.append((host, port))
            raise RuntimeError(f"Egress Blocked: Non-loopback attempt to {host}:{port}")
        return orig_connect(self, address)

    with patch.object(socket.socket, "connect", guarded_connect):
        yield attempts


def test_build_feedback_issue_url_formatting() -> None:
    """Test URL generation, query encoding, and length constraints."""
    url = build_feedback_issue_url(
        title="[Feedback]: Great experience",
        body="OctoFlow planned smoothly with zero telemetry.",
        labels=["feedback"],
        repo="octoflow/octoflow",
    )
    assert url.startswith("https://github.com/octoflow/octoflow/issues/new?")
    assert "title=%5BFeedback%5D%3A+Great+experience" in url
    assert "labels=feedback" in url

    # Discussion URL
    disc_url = build_feedback_issue_url(
        title="[Show and Tell]: My custom guild",
        body="Built a custom 8-arm guild.",
        repo="octoflow/octoflow",
        is_discussion=True,
        discussion_category="show-and-tell",
    )
    assert disc_url.startswith("https://github.com/octoflow/octoflow/discussions/new?")
    assert "category=show-and-tell" in disc_url


def test_build_feedback_issue_url_truncation_on_overflow() -> None:
    """Verify that excessively long bodies are gracefully truncated to protect URL length."""
    huge_body = "A" * 8000
    url = build_feedback_issue_url(
        title="[Bug]: Truncate test",
        body=huge_body,
        repo="octoflow/octoflow",
    )
    assert len(url) <= 4100
    assert "truncated" in url


def test_feedback_cli_dry_run_modes() -> None:
    """Test CLI execution across categories in dry-run/no-browser mode."""
    # 1. Feedback
    r1 = runner.invoke(app, ["feedback", "--category", "feedback", "--no-browser", "--dry-run"])
    assert r1.exit_code == 0
    assert "OctoFlow Voluntary Feedback" in r1.output
    assert "github.com" in r1.output

    # 2. Bug with diagnostics
    r2 = runner.invoke(
        app,
        ["feedback", "--category", "bug", "--diagnostics", "--no-browser", "--dry-run"],
    )
    assert r2.exit_code == 0
    assert "github.com" in r2.output
    assert "%5BBug%5D" in r2.output

    # 3. Idea
    r3 = runner.invoke(app, ["feedback", "--category", "idea", "--no-browser", "--dry-run"])
    assert r3.exit_code == 0
    assert "%5BIdea%5D" in r3.output

    # 4. Show and tell
    r4 = runner.invoke(
        app,
        ["feedback", "--category", "show-and-tell", "--no-browser", "--dry-run"],
    )
    assert r4.exit_code == 0
    assert "discussions%2Fnew" in r4.output or "discussions/new" in r4.output


def test_feedback_egress_isolation(loopback_egress_guard) -> None:
    """CRITICAL: Assert octoflow feedback command makes ZERO non-loopback network connections."""
    attempts = loopback_egress_guard

    # Invoke feedback command with diagnostics attached
    result = runner.invoke(
        app,
        ["feedback", "--category", "feedback", "--diagnostics", "--no-browser", "--dry-run"],
    )
    assert result.exit_code == 0
    # Must have 0 network egress calls
    assert len(attempts) == 0, f"Expected 0 egress calls, found: {attempts}"


def test_maybe_show_post_run_feedback_hint_lifecycle(tmp_path: Path) -> None:
    """Verify the post-run feedback hint displays once and updates settings."""
    cfg_file = tmp_path / "config.json"
    settings = Settings()
    settings.ui.show_feedback_prompt = True
    settings.feedback_prompted = False
    save_settings(settings, cfg_path=cfg_file)

    test_console = Console(record=True)

    with patch("sys.stdout.isatty", return_value=True), patch.dict(os.environ, {}, clear=True):
        # 1. First run: should display hint and return True
        shown = maybe_show_post_run_feedback_hint(console_out=test_console, cfg_path=cfg_file)
        assert shown is True
        output = test_console.export_text()
        assert "octoflow feedback" in output

        # 2. Second run: already prompted, should return False
        shown_second = maybe_show_post_run_feedback_hint(
            console_out=test_console, cfg_path=cfg_file
        )
        assert shown_second is False


def test_maybe_show_post_run_feedback_hint_suppressed_by_setting(tmp_path: Path) -> None:
    """Verify feedback hint is suppressed when ui.show_feedback_prompt is False."""
    cfg_file = tmp_path / "config.json"
    settings = Settings()
    settings.ui.show_feedback_prompt = False
    settings.feedback_prompted = False
    save_settings(settings, cfg_path=cfg_file)

    test_console = Console()

    with patch("sys.stdout.isatty", return_value=True):
        shown = maybe_show_post_run_feedback_hint(console_out=test_console, cfg_path=cfg_file)
        assert shown is False


def test_maybe_show_post_run_feedback_hint_suppressed_by_env(tmp_path: Path) -> None:
    """Verify feedback hint is suppressed when OCTOFLOW_NO_FEEDBACK_PROMPT is set."""
    cfg_file = tmp_path / "config.json"
    settings = Settings()
    settings.ui.show_feedback_prompt = True
    settings.feedback_prompted = False
    save_settings(settings, cfg_path=cfg_file)

    test_console = Console()

    with (
        patch.dict(os.environ, {"OCTOFLOW_NO_FEEDBACK_PROMPT": "1"}),
        patch("sys.stdout.isatty", return_value=True),
    ):
        shown = maybe_show_post_run_feedback_hint(console_out=test_console, cfg_path=cfg_file)
        assert shown is False


def test_maybe_show_post_run_feedback_hint_suppressed_in_noninteractive(tmp_path: Path) -> None:
    """Verify feedback hint is suppressed in non-interactive environments."""
    cfg_file = tmp_path / "config.json"
    settings = Settings()
    save_settings(settings, cfg_path=cfg_file)

    test_console = Console()

    with (
        patch.dict(os.environ, {"OCTOFLOW_NONINTERACTIVE": "1"}),
        patch("sys.stdout.isatty", return_value=True),
    ):
        shown = maybe_show_post_run_feedback_hint(console_out=test_console, cfg_path=cfg_file)
        assert shown is False
