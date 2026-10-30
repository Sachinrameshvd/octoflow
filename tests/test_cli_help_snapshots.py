import os
from pathlib import Path

import pytest
from octoflow.cli import app, octos_app
from typer.testing import CliRunner

SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots" / "help"


@pytest.fixture
def runner():
    return CliRunner(env={"COLUMNS": "100"})


def test_root_help_snapshot(runner):
    snapshot_file = SNAPSHOT_DIR / "_root.txt"
    result = runner.invoke(app, ["--help"], prog_name="octoflow")
    assert result.exit_code == 0
    if os.getenv("UPDATE_SNAPSHOTS") == "1":
        snapshot_file.write_text(result.output, encoding="utf-8")
    assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"
    expected = snapshot_file.read_text(encoding="utf-8")
    assert result.output == expected


@pytest.mark.parametrize(
    "cmd_name",
    [cmd.name or cmd.callback.__name__ for cmd in app.registered_commands],
)
def test_app_command_help_snapshots(runner, cmd_name):
    snapshot_file = SNAPSHOT_DIR / f"{cmd_name}.txt"
    result = runner.invoke(app, [cmd_name, "--help"], prog_name="octoflow")
    assert result.exit_code == 0
    if os.getenv("UPDATE_SNAPSHOTS") == "1":
        snapshot_file.write_text(result.output, encoding="utf-8")
    assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"
    expected = snapshot_file.read_text(encoding="utf-8")
    assert result.output == expected


def test_octos_root_help_snapshot(runner):
    snapshot_file = SNAPSHOT_DIR / "octos__root.txt"
    result = runner.invoke(octos_app, ["--help"], prog_name="octos")
    assert result.exit_code == 0
    if os.getenv("UPDATE_SNAPSHOTS") == "1":
        snapshot_file.write_text(result.output, encoding="utf-8")
    assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"
    expected = snapshot_file.read_text(encoding="utf-8")
    assert result.output == expected


@pytest.mark.parametrize(
    "cmd_name",
    [cmd.name or cmd.callback.__name__ for cmd in octos_app.registered_commands],
)
def test_octos_command_help_snapshots(runner, cmd_name):
    snapshot_file = SNAPSHOT_DIR / f"octos__{cmd_name}.txt"
    result = runner.invoke(octos_app, [cmd_name, "--help"], prog_name="octos")
    assert result.exit_code == 0
    if os.getenv("UPDATE_SNAPSHOTS") == "1":
        snapshot_file.write_text(result.output, encoding="utf-8")
    assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"
    expected = snapshot_file.read_text(encoding="utf-8")
    assert result.output == expected


def test_config_group_help_snapshot(runner):
    snapshot_file = SNAPSHOT_DIR / "config.txt"
    result = runner.invoke(app, ["config", "--help"], prog_name="octoflow")
    assert result.exit_code == 0
    if os.getenv("UPDATE_SNAPSHOTS") == "1":
        snapshot_file.write_text(result.output, encoding="utf-8")
    assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"
    expected = snapshot_file.read_text(encoding="utf-8")
    assert result.output == expected


@pytest.mark.parametrize(
    "sub_cmd",
    ["path", "show", "set", "validate", "migrate"],
)
def test_config_subcommand_help_snapshots(runner, sub_cmd):
    snapshot_file = SNAPSHOT_DIR / f"config_{sub_cmd}.txt"
    result = runner.invoke(app, ["config", sub_cmd, "--help"], prog_name="octoflow")
    assert result.exit_code == 0
    if os.getenv("UPDATE_SNAPSHOTS") == "1":
        snapshot_file.write_text(result.output, encoding="utf-8")
    assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"
    expected = snapshot_file.read_text(encoding="utf-8")
    assert result.output == expected
