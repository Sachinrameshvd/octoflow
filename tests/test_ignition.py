"""Tests for Phase Gate 4: ProjectIgniter & Live Service Provisioning."""

import asyncio
import tempfile
import time
from pathlib import Path
import pytest
import requests

from octoflow.ignition import ProjectIgniter, find_free_port, is_port_listening, LiveServiceManifest
from octoflow.consortium import OctosConsortium
from octoflow.config import OctoFlowConfig, SwarmMorphology


def test_find_free_port():
    """Verify find_free_port finds an open port."""
    port = find_free_port(start_port=9100)
    assert 9100 <= port < 9200


def test_inspect_deliverables_empty():
    """Verify inspection on an empty workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        igniter = ProjectIgniter(workspace_dir=tmpdir)
        d = igniter.inspect_deliverables()
        assert d["has_node_frontend"] is False
        assert d["has_python_backend"] is False
        assert d["has_aiml_train"] is False


def test_inspect_deliverables_detection():
    """Verify inspection correctly detects deliverables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        (ws / "package.json").write_text('{"name": "test-app"}')
        (ws / "backend").mkdir()
        (ws / "backend" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        (ws / "train.py").write_text("import torch\nprint('training')")

        igniter = ProjectIgniter(workspace_dir=tmpdir)
        d = igniter.inspect_deliverables()
        assert d["has_node_frontend"] is True
        assert d["has_python_backend"] is True
        assert d["has_fastapi"] is True
        assert d["has_aiml_train"] is True


def test_ignite_static_web_server():
    """Verify ProjectIgniter launches a live static web server and can serve traffic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        html_file = ws / "index.html"
        html_file.write_text("<!DOCTYPE html><html><body><h1>OctoFlow Live Test</h1></body></html>")

        igniter = ProjectIgniter(workspace_dir=tmpdir)
        manifest = igniter.ignite(objective="Test static web launch")

        try:
            assert manifest.status == "RUNNING"
            assert manifest.primary_url is not None
            assert manifest.frontend_port is not None
            assert len(manifest.pids) > 0

            # Brief pause for server to bind
            time.sleep(0.5)

            # Probe the server
            resp = requests.get(manifest.primary_url, timeout=3.0)
            assert resp.status_code == 200
            assert "OctoFlow Live Test" in resp.text
        finally:
            igniter.terminate_all()
            assert manifest.status == "STOPPED"
            time.sleep(0.3)
            # Port should be free again
            assert is_port_listening(manifest.frontend_port) is False


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_consortium_live_ignition_phase_gate(anyio_backend):
    """Verify consortium completes Phase Gate 4: Live Ignition."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = OctoFlowConfig(
            morphology=SwarmMorphology.SOFTWARE_DEV,
            model_provider="mock",
            workspace_dir=tmpdir,
        )
        consortium = OctosConsortium(config=cfg, octopus_count=3)
        res = await consortium.arun_consortium(objective="Build a live web dashboard", cycles_per_octopus=2)

        assert res["status"] == "COMPLETED"
        assert "ignition" in res
        # Clean up any spawned igniter processes
        consortium.igniter.terminate_all()
