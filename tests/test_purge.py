"""Tests for octoflow purge CLI command (P5.4)."""

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from octoflow.cli import app

runner = CliRunner()


def test_purge_dry_run_lists_without_deleting(tmp_path):
    """Purge in --dry-run mode reports candidate targets and does not delete anything."""
    fake_home = tmp_path / "home"
    fake_octo_dir = fake_home / ".octoflow"
    fake_octo_dir.mkdir(parents=True, exist_ok=True)
    config_file = fake_octo_dir / "config.json"
    config_file.write_text(json.dumps({"theme": "catppuccin"}), encoding="utf-8")

    ws_dir = tmp_path / "ws"
    ws_dir.mkdir(parents=True, exist_ok=True)
    (ws_dir / ".octoflow").mkdir(parents=True, exist_ok=True)
    (ws_dir / "octoflow-audit-sample.html").write_text("<html></html>", encoding="utf-8")

    with patch("octoflow.commands.purge.get_octoflow_dir", return_value=fake_octo_dir):
        res = runner.invoke(app, ["purge", "--dry-run", "--dir", str(ws_dir)])

    assert res.exit_code == 0
    assert "DRY-RUN" in res.output
    assert "OctoFlow Data Purge Candidates" in res.output
    # Verify nothing was deleted
    assert config_file.exists()
    assert (ws_dir / ".octoflow").exists()
    assert (ws_dir / "octoflow-audit-sample.html").exists()


def test_purge_with_yes_deletes_targets(tmp_path):
    """Purge with --yes flag executes deletion and reclaims storage space."""
    fake_home = tmp_path / "home"
    fake_octo_dir = fake_home / ".octoflow"
    fake_octo_dir.mkdir(parents=True, exist_ok=True)
    (fake_octo_dir / "test.log").write_text("sample log", encoding="utf-8")

    ws_dir = tmp_path / "ws"
    ws_dir.mkdir(parents=True, exist_ok=True)
    ws_cache = ws_dir / ".octoflow"
    ws_cache.mkdir(parents=True, exist_ok=True)
    report_file = ws_dir / "octoflow-report-test.html"
    report_file.write_text("report", encoding="utf-8")

    with patch("octoflow.commands.purge.get_octoflow_dir", return_value=fake_octo_dir):
        res = runner.invoke(app, ["purge", "--yes", "--dir", str(ws_dir)])

    assert res.exit_code == 0
    assert "Successfully purged" in res.output
    # Global ~/.octoflow and workspace targets should now be deleted
    assert not fake_octo_dir.exists()
    assert not ws_cache.exists()
    assert not report_file.exists()


def test_purge_workspace_only_leaves_global_intact(tmp_path):
    """--workspace-only flag must leave ~/.octoflow completely untouched."""
    fake_home = tmp_path / "home"
    fake_octo_dir = fake_home / ".octoflow"
    fake_octo_dir.mkdir(parents=True, exist_ok=True)
    config_file = fake_octo_dir / "config.json"
    config_file.write_text("{}", encoding="utf-8")

    ws_dir = tmp_path / "ws"
    ws_dir.mkdir(parents=True, exist_ok=True)
    ws_cache = ws_dir / ".octoflow"
    ws_cache.mkdir(parents=True, exist_ok=True)

    with patch("octoflow.commands.purge.get_octoflow_dir", return_value=fake_octo_dir):
        res = runner.invoke(app, ["purge", "--yes", "--workspace-only", "--dir", str(ws_dir)])

    assert res.exit_code == 0
    # Global config file preserved
    assert config_file.exists()
    # Workspace cache deleted
    assert not ws_cache.exists()
