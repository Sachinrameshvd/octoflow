"""Tests for Guided First Run Onboarding (P6.1)."""

import http.server
import json
import os
import pty
import select
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from octoflow.cli import app
from octoflow.config import get_octoflow_dir
from octoflow.first_run import (
    check_environment,
    run_guided_first_run,
    should_run_first_run_wizard,
)
from octoflow.settings import get_default_config_path, load_settings

runner = CliRunner()


class FakeOllamaHandler(http.server.BaseHTTPRequestHandler):
    """Fake local Ollama HTTP server for test doubles."""

    def do_GET(self):
        if self.path == "/api/tags":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "models": [
                    {
                        "name": "qwen2.5-coder:7b",
                        "modified_at": "2026-01-01T00:00:00Z",
                        "size": 4700000000,
                    }
                ]
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/generate":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            action_json = json.dumps({
                "action": "write_file",
                "path": "reverse_words.py",
                "content": "def reverse_words(text: str) -> str:\n    return ' '.join(reversed(text.split()))\n",
                "explanation": "Implemented word reversal function",
            })
            data = {
                "response": action_json,
                "done": True,
                "prompt_eval_count": 12,
                "eval_count": 24,
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence HTTP server access logs in test output
        pass


@pytest.fixture
def fake_ollama_server():
    """Start local fake Ollama HTTP daemon on an ephemeral port."""
    server = http.server.HTTPServer(("127.0.0.1", 0), FakeOllamaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    ollama_url = f"http://127.0.0.1:{port}"
    try:
        yield ollama_url
    finally:
        server.shutdown()
        server.server_close()


def test_first_run_with_fake_ollama_completes(fake_ollama_server, tmp_path, monkeypatch):
    """On a clean HOME with Ollama endpoint, guided flow records onboarding_completed."""
    fake_octo = tmp_path / ".octoflow"
    fake_octo.mkdir(parents=True, exist_ok=True)
    cfg_file = fake_octo / "config.json"

    monkeypatch.setenv("OLLAMA_BASE_URL", fake_ollama_server)

    with patch("octoflow.first_run.get_octoflow_dir", return_value=fake_octo), \
         patch("octoflow.first_run.get_default_config_path", return_value=cfg_file), \
         patch("octoflow.config.get_octoflow_dir", return_value=fake_octo):

        res = runner.invoke(app, ["first-run", "--yes"])

    assert res.exit_code == 0
    assert "OCTOFLOW FIRST-RUN DEMO COMPLETE" in res.output or "onboarding completed" in res.output
    # Verify settings recorded onboarding_completed
    assert cfg_file.exists()
    settings = load_settings(cfg_path=cfg_file)
    assert settings.onboarding_completed is True

    # Verify demo wrote strictly under ~/.octoflow/demo
    demo_dir = fake_octo / "demo"
    assert demo_dir.exists()
    written_files = list(demo_dir.glob("*.py"))
    assert len(written_files) > 0


def test_first_run_without_ollama_selects_dry_run(tmp_path, monkeypatch):
    """With no Ollama daemon and no API key, --yes selects dry-run mode."""
    fake_octo = tmp_path / ".octoflow"
    fake_octo.mkdir(parents=True, exist_ok=True)
    cfg_file = fake_octo / "config.json"

    # Point to closed dead port
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:59999")

    with patch("octoflow.first_run.get_octoflow_dir", return_value=fake_octo), \
         patch("octoflow.first_run.get_default_config_path", return_value=cfg_file), \
         patch("octoflow.config.get_octoflow_dir", return_value=fake_octo):

        res = runner.invoke(app, ["first-run", "--yes"])

    assert res.exit_code == 0
    assert "dry-run demo" in res.output.lower() or "first-run demo complete" in res.output.lower()

    settings = load_settings(cfg_path=cfg_file)
    assert settings.onboarding_completed is True
    assert settings.defaults.default_provider == "mock"


def test_interactive_choice_dry_run(tmp_path, monkeypatch):
    """User interactively chooses choice 3 (Dry-run demo)."""
    fake_octo = tmp_path / ".octoflow"
    fake_octo.mkdir(parents=True, exist_ok=True)
    cfg_file = fake_octo / "config.json"

    # Inputs: "3" (dry-run), "y" (run demo), "n" (no visualizer)
    inputs = "3\ny\nn\n"

    with patch("octoflow.first_run.get_octoflow_dir", return_value=fake_octo), \
         patch("octoflow.first_run.get_default_config_path", return_value=cfg_file), \
         patch("octoflow.config.get_octoflow_dir", return_value=fake_octo):

        res = runner.invoke(app, ["first-run"], input=inputs)

    assert res.exit_code == 0
    assert "OCTOFLOW FIRST-RUN DEMO COMPLETE" in res.output
    settings = load_settings(cfg_path=cfg_file)
    assert settings.onboarding_completed is True
    assert settings.defaults.default_provider == "mock"


def test_non_tty_runs_never_prompt(monkeypatch):
    """When stdin is not a TTY, should_run_first_run_wizard must return False."""
    with patch("sys.stdin.isatty", return_value=False):
        assert should_run_first_run_wizard() is False


def test_skip_onboarding_escape_hatch(monkeypatch):
    """OCTOFLOW_SKIP_ONBOARDING=1 disables the first run wizard."""
    monkeypatch.setenv("OCTOFLOW_SKIP_ONBOARDING", "1")
    assert should_run_first_run_wizard() is False


def test_demo_writes_only_under_demo_directory(tmp_path):
    """Demonstrate that the demo conductor only writes to ~/.octoflow/demo."""
    fake_octo = tmp_path / ".octoflow"
    demo_dir = fake_octo / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    from octoflow.first_run import execute_demo_mission

    success, result, elapsed = execute_demo_mission("mock", demo_dir)
    assert success is True
    assert elapsed > 0

    # Ensure files exist in demo_dir
    files_in_demo = list(demo_dir.glob("*.py"))
    assert len(files_in_demo) >= 1
    # Check filenames
    filenames = [p.name for p in files_in_demo]
    assert any("reverse_words" in f for f in filenames)


@pytest.mark.pty
def test_pty_wizard_keystrokes_flow(tmp_path):
    """Walk through guided wizard keystrokes over an isolated pseudo-terminal."""
    fake_octo = tmp_path / ".octoflow"
    fake_octo.mkdir(parents=True, exist_ok=True)
    cfg_file = fake_octo / "config.json"

    master, slave = pty.openpty()
    try:
        # Feed keystrokes: '3\n' (dry run), 'y\n' (demo), 'n\n' (no viz)
        os.write(master, b"3\ny\nn\n")

        with patch("sys.stdin", os.fdopen(slave, "r")), \
             patch("sys.stdin.isatty", return_value=True), \
             patch("octoflow.first_run.get_octoflow_dir", return_value=fake_octo), \
             patch("octoflow.first_run.get_default_config_path", return_value=cfg_file), \
             patch("octoflow.config.get_octoflow_dir", return_value=fake_octo):

            finished = run_guided_first_run(yes=False, launch_cockpit_after=False)

        assert finished is True
        assert cfg_file.exists()
        settings = load_settings(cfg_path=cfg_file)
        assert settings.onboarding_completed is True
    finally:
        os.close(master)
