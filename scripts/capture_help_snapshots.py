"""Script to capture CLI help snapshots for all octoflow commands with COLUMNS=100."""
import os
from pathlib import Path
from typer.testing import CliRunner
from octoflow.cli import app, octos_app

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "tests" / "snapshots" / "help"


def capture_all():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    runner = CliRunner(env={"COLUMNS": "100"})

    # Capture main app help
    root_help = runner.invoke(app, ["--help"], prog_name="octoflow")
    assert root_help.exit_code == 0, f"Root help failed: {root_help.exit_code}"
    (SNAPSHOT_DIR / "_root.txt").write_text(root_help.output, encoding="utf-8")
    print(f"Captured _root.txt ({len(root_help.output)} bytes)")

    # Capture each command on main app
    for cmd in app.registered_commands:
        cmd_name = cmd.name or cmd.callback.__name__
        cmd_help = runner.invoke(app, [cmd_name, "--help"], prog_name="octoflow")
        assert cmd_help.exit_code == 0, f"Command help failed for {cmd_name}: {cmd_help.exit_code}"
        filename = f"{cmd_name}.txt"
        (SNAPSHOT_DIR / filename).write_text(cmd_help.output, encoding="utf-8")
        print(f"Captured {filename} ({len(cmd_help.output)} bytes)")

    # Capture octos app help
    octos_root = runner.invoke(octos_app, ["--help"], prog_name="octos")
    assert octos_root.exit_code == 0, f"Octos root help failed: {octos_root.exit_code}"
    (SNAPSHOT_DIR / "octos__root.txt").write_text(octos_root.output, encoding="utf-8")
    print(f"Captured octos__root.txt ({len(octos_root.output)} bytes)")

    # Capture each command on octos app
    for cmd in octos_app.registered_commands:
        cmd_name = cmd.name or cmd.callback.__name__
        cmd_help = runner.invoke(octos_app, [cmd_name, "--help"], prog_name="octos")
        assert cmd_help.exit_code == 0, f"Octos command help failed for {cmd_name}: {cmd_help.exit_code}"
        filename = f"octos__{cmd_name}.txt"
        (SNAPSHOT_DIR / filename).write_text(cmd_help.output, encoding="utf-8")
        print(f"Captured {filename} ({len(cmd_help.output)} bytes)")

    print(f"\nSuccessfully captured all help snapshots to {SNAPSHOT_DIR}")


if __name__ == "__main__":
    capture_all()
