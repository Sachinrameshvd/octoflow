"""Unit and integration tests for OctoFlow Claude Code Bridge & SPARC integration."""

from pathlib import Path
from unittest.mock import patch

import pytest
from octoflow.claude_bridge import (
    compile_sparc_prompt,
    execute_claude_cli,
    generate_claude_md,
    get_claude_status,
)
from octoflow.cli import app, octos_app
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


def test_generate_claude_md_creates_new(tmp_path: Path):
    target, created = generate_claude_md(workspace=tmp_path, force=False)
    assert created is True
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "OctoFlow Cephalopod Intelligence Protocol for Claude Code" in content
    assert "Arm 0: System Architect" in content
    assert "Active Inference Sensory Gating Directives" in content
    assert "The 4-Phase SPARC Execution Lifecycle" in content


def test_generate_claude_md_idempotent(tmp_path: Path):
    target, created1 = generate_claude_md(workspace=tmp_path, force=False)
    assert created1 is True

    # Running again should not duplicate content
    target2, created2 = generate_claude_md(workspace=tmp_path, force=False)
    assert created2 is False
    content = target2.read_text(encoding="utf-8")
    assert content.count("OctoFlow Cephalopod Intelligence Protocol") == 1


def test_generate_claude_md_appends_existing(tmp_path: Path):
    existing_file = tmp_path / "CLAUDE.md"
    existing_file.write_text("# Existing Project Instructions\n- Do not delete\n")

    target, modified = generate_claude_md(workspace=tmp_path, force=False)
    assert modified is True
    content = target.read_text(encoding="utf-8")
    assert "# Existing Project Instructions" in content
    assert "OctoFlow Cephalopod Intelligence Protocol" in content


def test_compile_sparc_prompt_structure(tmp_path: Path):
    # Create fake pyproject.toml to test stack detection
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")

    prompt = compile_sparc_prompt("Build user registration with JWT", workspace=tmp_path)
    assert "OCTOFLOW 8-ARM SPARC DIRECTIVE FOR CLAUDE CODE" in prompt
    assert "Goal: Build user registration with JWT" in prompt
    assert "Python" in prompt
    assert "Docker" in prompt
    assert "Phase 1: Specification & Architecture Blueprint [Arms 0, 1, 2]" in prompt
    assert "Phase 2: Core Construction & TDD Implementation [Arms 3, 4, 5]" in prompt
    assert "Phase 3: QA, AST Verification & Security Audit [Arms 5, 6]" in prompt
    assert "Phase 4: Delivery & Ignition Readiness [Arm 7]" in prompt


def test_get_claude_status(tmp_path: Path):
    status = get_claude_status(workspace=tmp_path)
    assert "claude_installed" in status
    assert "claude_path" in status
    assert "claude_md_exists" in status
    assert "mcp_configured" in status
    assert status["claude_md_exists"] is False

    # Create CLAUDE.md and check again
    generate_claude_md(workspace=tmp_path)
    status2 = get_claude_status(workspace=tmp_path)
    assert status2["claude_md_exists"] is True
    assert status2["claude_md_path"] == str(tmp_path / "CLAUDE.md")


def test_execute_claude_cli_dry_run(tmp_path: Path):
    ret = execute_claude_cli(
        goal="Test feature",
        print_mode=True,
        dangerously_skip_permissions=True,
        dry_run=True,
        workspace=tmp_path,
    )
    assert ret == 0


def test_execute_claude_cli_missing_binary(tmp_path: Path):
    with patch("shutil.which", return_value=None):
        ret = execute_claude_cli(goal="Test feature", workspace=tmp_path)
        assert ret == 127


def test_cli_claude_help(runner: CliRunner):
    res = runner.invoke(app, ["claude", "--help"])
    assert res.exit_code == 0
    assert "Direct Claude Code CLI integration" in res.output
    assert "init" in res.output
    assert "run" in res.output
    assert "prompt" in res.output
    assert "status" in res.output


def test_cli_claude_init(runner: CliRunner, tmp_path: Path):
    res = runner.invoke(app, ["claude", "init", "--dir", str(tmp_path)])
    assert res.exit_code == 0
    assert (tmp_path / "CLAUDE.md").exists()
    assert "Claude Code Integration Status" in res.output


def test_cli_claude_prompt_raw(runner: CliRunner, tmp_path: Path):
    res = runner.invoke(app, ["claude", "prompt", "Add Redis Cache", "--dir", str(tmp_path), "--raw"])
    assert res.exit_code == 0
    assert "OCTOFLOW 8-ARM SPARC DIRECTIVE FOR CLAUDE CODE" in res.output
    assert "Goal: Add Redis Cache" in res.output


def test_cli_claude_run_dry_run(runner: CliRunner, tmp_path: Path):
    res = runner.invoke(app, ["claude", "run", "Implement OAuth2", "--dir", str(tmp_path), "--dry-run"])
    assert res.exit_code == 0
    assert "[DRY-RUN]" in res.output
    assert "Implement OAuth2" in res.output


def test_cli_claude_status(runner: CliRunner, tmp_path: Path):
    res = runner.invoke(app, ["claude", "status", "--dir", str(tmp_path)])
    assert res.exit_code == 0
    assert "OctoFlow ◈ Claude Code Integration Diagnostics" in res.output


def test_cli_init_with_claude_flag(runner: CliRunner, tmp_path: Path):
    res = runner.invoke(app, ["init", "--claude", "--dir", str(tmp_path)])
    assert res.exit_code == 0
    assert (tmp_path / "CLAUDE.md").exists()


def test_octos_cli_claude_status(runner: CliRunner, tmp_path: Path):
    res = runner.invoke(octos_app, ["claude", "status", "--dir", str(tmp_path)])
    assert res.exit_code == 0
    assert "Diagnostics" in res.output
