"""Comprehensive tests for Doctor JSON diagnostics and Bugreport command (P8.4).

Verifies:
1. 'octoflow doctor --json' produces valid machine-readable JSON.
2. 'octoflow bugreport' formats a complete environment summary for issue reports.
3. Canary keys and sensitive credentials in environment/config are strictly masked in bugreport.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from octoflow.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_doctor_json_output():
    """Verify 'octoflow doctor --json' outputs structured JSON with required fields."""
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0, f"Doctor --json failed: {result.stdout}"

    data = json.loads(result.stdout)
    assert "overall_status" in data
    assert "all_passed" in data
    assert isinstance(data["subsystems"], list)
    assert len(data["subsystems"]) >= 5

    subsystem_names = [sub["subsystem"] for sub in data["subsystems"]]
    assert "Python Runtime" in subsystem_names
    assert "Git Repository" in subsystem_names
    assert "3D Visualizer Dist" in subsystem_names


def test_bugreport_structure():
    """Verify 'octoflow bugreport' prints structured markdown suitable for issue submission."""
    result = runner.invoke(app, ["bugreport"])
    assert result.exit_code == 0, f"Bugreport failed: {result.stdout}"

    out = result.stdout
    assert "### OctoFlow Bug Report Environment Summary" in out
    assert "#### System & Environment" in out
    assert "#### Diagnostics Findings" in out
    assert "#### Config Settings (Masked)" in out
    assert "#### Environment Variables (Masked)" in out
    assert "#### Recent Log Excerpt" in out


def test_bugreport_canary_key_redaction(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Verify bugreport output contains zero raw secrets when canary credentials are set."""
    # 1. Set distinctive canary keys across env
    canary_anthropic = "sk-ant-api03-canary-secret-12345678901234567890"
    canary_openai = "sk-canaryopenaisecretkey123456789012345678"
    canary_github = "ghp_canarygithubtoken12345678901234567890"
    canary_custom_pwd = "super_secret_canary_db_password"

    monkeypatch.setenv("ANTHROPIC_API_KEY", canary_anthropic)
    monkeypatch.setenv("OPENAI_API_KEY", canary_openai)
    monkeypatch.setenv("CANARY_TOKEN", canary_github)
    monkeypatch.setenv("OCTOFLOW_CANARY_PASSWORD", canary_custom_pwd)

    result = runner.invoke(app, ["bugreport"])
    assert result.exit_code == 0

    out = result.stdout

    # Assert CANARY SECRETS are NEVER present in plain text
    assert canary_anthropic not in out, "Canary Anthropic API key leaked into bugreport output"
    assert canary_openai not in out, "Canary OpenAI API key leaked into bugreport output"
    assert canary_github not in out, "Canary GitHub token leaked into bugreport output"
    assert canary_custom_pwd not in out, "Canary custom password leaked into bugreport output"

    # Assert masked placeholders are present
    assert "[REDACTED_CREDENTIAL]" in out or "[REDACTED" in out
