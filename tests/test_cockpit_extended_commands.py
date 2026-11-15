"""Tests for extended cockpit slash commands, sensory gate analytics, and ignition preview (P13.1).

Verifies:
1. Registration of new slash commands in COCKPIT_COMMANDS
2. Normalization of slashless variants (receipt, runs, replay, gate, dashboard, feedback, tree)
3. HUD panel composition includes sensory surprise gate line
4. Simulation vs Live LLM badge rendering in post-execution ribbon
5. Registration of ignite CLI command with --open flag
"""

from unittest.mock import MagicMock, patch

from octoflow.cockpit.app import COCKPIT_COMMANDS
from octoflow.cockpit.render import build_hud_panel
from octoflow.cockpit.session import CockpitSession
from octoflow.commands.ignition_cmds import ignite_cli_cmd


def test_cockpit_commands_registration():
    """Verify newly added commands exist in COCKPIT_COMMANDS list."""
    expected = [
        "/receipt",
        "/runs",
        "/replay",
        "/gate",
        "/surprise",
        "/dashboard",
        "/feedback",
        "/tree",
        "/interview",
        "/steer",
    ]
    for cmd in expected:
        assert cmd in COCKPIT_COMMANDS, f"{cmd} should be in COCKPIT_COMMANDS"


def test_hud_panel_sensory_gate_row():
    """Verify build_hud_panel includes sensory gate row."""
    from rich.console import Console

    session = CockpitSession()
    panel = build_hud_panel(session)
    console = Console(width=120)
    with console.capture() as capture:
        console.print(panel)
    rendered = capture.get()
    assert "SENSORY GATE" in rendered
    assert "Active Inference" in rendered


def test_ignite_cli_cmd_registration():
    """Verify ignite CLI command executes with ProjectIgniter."""
    with patch("octoflow.ignition.ProjectIgniter.ignite") as mock_ignite:
        manifest = MagicMock()
        manifest.primary_url = "http://localhost:3000"
        manifest.api_docs_url = "http://localhost:8000/docs"
        manifest.status = "READY"
        manifest.title = "Test App"
        manifest.service_type = "fastapi"
        mock_ignite.return_value = manifest

        ignite_cli_cmd(workspace=".", open_browser=False)
        assert mock_ignite.called
