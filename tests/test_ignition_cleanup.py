"""Comprehensive integration and cleanup tests for OctoFlow Ignition runtime.

Tests cover:
- Process isolation (start_new_session, process groups, killpg).
- Guaranteed cleanup on normal exit, termination, and SIGTERM/SIGINT.
- TCP and HTTP readiness detection with 30s timeout and log tail on failure.
- --open flag behavior (mocked webbrowser.open, TTY/SSH detection).
- Port collision handling (bind-and-hold / retry on EADDRINUSE).
- 127.0.0.1 bind guarantee.
- CLI commands: octoflow ps and octoflow stop.
"""

import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import httpx
import pytest
from typer.testing import CliRunner

pytestmark = pytest.mark.integration_local

from octoflow.cli import app
from octoflow.ignition import (
    ProjectIgniter,
    find_free_port,
    is_port_listening,
    kill_process_group,
    wait_for_service_readiness,
    open_url_in_browser,
    list_active_ignitions,
    stop_ignition,
    get_log_tail,
)

runner = CliRunner()


def test_ignition_http_server_lifecycle_and_127_bind():
    """Verify that a service binds to 127.0.0.1, writes logs to disk, and cleans up cleanly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        html_file = ws / "index.html"
        html_file.write_text("<!DOCTYPE html><html><body><h1>OctoFlow Cleanup Test</h1></body></html>")

        igniter = ProjectIgniter(workspace_dir=tmpdir)
        manifest = igniter.ignite(objective="Test cleanup lifecycle", timeout=5.0)

        try:
            assert manifest.status in ("READY", "RUNNING")
            assert manifest.primary_url is not None
            assert "127.0.0.1" in manifest.primary_url
            port = manifest.frontend_port
            assert port is not None
            assert len(manifest.pids) > 0
            assert len(manifest.pgids) > 0

            # Verify log file is captured in <workspace>/.octoflow/ignition/<service>.log
            log_dir = ws / ".octoflow" / "ignition"
            assert log_dir.exists()
            log_file = log_dir / "frontend.log"
            assert log_file.exists()

            # Verify service is reachable on 127.0.0.1
            resp = httpx.get(f"http://127.0.0.1:{port}", timeout=3.0)
            assert resp.status_code == 200
            assert "OctoFlow Cleanup Test" in resp.text

            # Verify PID is running
            for pid in manifest.pids:
                # Signal 0 checks if process exists without killing it
                os.kill(pid, 0)
        finally:
            igniter.terminate_all()

        # After termination, status should be STOPPED
        assert manifest.status == "STOPPED"
        time.sleep(0.5)

        # Port should be released
        assert is_port_listening(port) is False

        # All PIDs should be terminated (os.kill raises ProcessLookupError)
        for pid in manifest.pids:
            with pytest.raises(ProcessLookupError):
                os.kill(pid, 0)


def test_ignition_open_flag_mocked_webbrowser():
    """Verify --open calls webbrowser.open exactly once after readiness only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        (ws / "index.html").write_text("<html><body>Open Test</body></html>")

        igniter = ProjectIgniter(workspace_dir=tmpdir)

        # 1. When open_browser=False: webbrowser.open should NOT be called
        with patch("webbrowser.open") as mock_open:
            manifest_no_open = igniter.ignite(objective="No open", open_browser=False, timeout=5.0)
            igniter.terminate_all()
            assert not mock_open.called

        # 2. When open_browser=True in interactive local TTY: webbrowser.open called exactly once
        igniter_open = ProjectIgniter(workspace_dir=tmpdir)
        with patch("webbrowser.open", return_value=True) as mock_open, \
             patch("sys.stdout.isatty", return_value=True), \
             patch.dict(os.environ, {}, clear=False):
            # Ensure SSH env vars are unset
            for key in ["SSH_CLIENT", "SSH_TTY", "SSH_CONNECTION"]:
                os.environ.pop(key, None)

            manifest_open = igniter_open.ignite(objective="With open", open_browser=True, timeout=5.0)
            try:
                assert manifest_open.status in ("READY", "RUNNING")
                assert mock_open.call_count == 1
                mock_open.assert_called_once_with(manifest_open.primary_url)
            finally:
                igniter_open.terminate_all()

        # 3. When open_browser=True but in SSH or non-TTY: print URL, do NOT call webbrowser.open
        igniter_ssh = ProjectIgniter(workspace_dir=tmpdir)
        with patch("webbrowser.open") as mock_open, \
             patch.dict(os.environ, {"SSH_CONNECTION": "192.168.1.1 12345 192.168.1.2 22"}):
            manifest_ssh = igniter_ssh.ignite(objective="SSH session", open_browser=True, timeout=5.0)
            try:
                assert manifest_ssh.status in ("READY", "RUNNING")
                assert not mock_open.called
            finally:
                igniter_ssh.terminate_all()


def test_ignition_readiness_failure_reports_failed_with_log_tail():
    """Verify that a failing service reports FAILED with the last 20 log lines within timeout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        # Create a broken python file that crashes immediately with distinct log output
        crash_script = ws / "broken_app.py"
        crash_script.write_text(
            "import sys\n"
            "for i in range(25):\n"
            "    print(f'CRASH_LOG_LINE_{i}', file=sys.stderr)\n"
            "sys.exit(1)\n"
        )

        igniter = ProjectIgniter(workspace_dir=tmpdir)

        # Force inspection to use this broken app as backend
        start_time = time.time()
        deliverables = {
            "has_python_backend": True,
            "backend_entrypoint": crash_script,
            "has_fastapi": False,
            "has_node_frontend": False,
            "has_static_html": False,
            "has_aiml_train": False,
            "has_aiml_infer": False,
        }
        with patch.object(igniter, "inspect_deliverables", return_value=deliverables):
            manifest = igniter.ignite(objective="Test crash log tail", timeout=4.0)

        elapsed = time.time() - start_time
        try:
            assert manifest.status == "FAILED"
            assert elapsed < 5.0
            assert manifest.error_message is not None
            # Verify log tail contains the last crash lines (e.g. CRASH_LOG_LINE_24)
            assert "CRASH_LOG_LINE_24" in manifest.error_message or "CRASH_LOG_LINE_24" in (manifest.log_tail or "")
        finally:
            igniter.terminate_all()


def test_ignition_readiness_timeout_silent_service():
    """Verify a service that hangs without listening reports FAILED within the timeout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        # Create a python script that sleeps indefinitely without opening a socket
        hang_script = ws / "silent_app.py"
        hang_script.write_text(
            "import time\n"
            "print('Starting silent app...')\n"
            "time.sleep(60)\n"
        )

        igniter = ProjectIgniter(workspace_dir=tmpdir)
        deliverables = {
            "has_python_backend": True,
            "backend_entrypoint": hang_script,
            "has_fastapi": False,
            "has_node_frontend": False,
            "has_static_html": False,
            "has_aiml_train": False,
            "has_aiml_infer": False,
        }

        start_time = time.time()
        with patch.object(igniter, "inspect_deliverables", return_value=deliverables):
            manifest = igniter.ignite(objective="Test readiness timeout", timeout=1.5)
        elapsed = time.time() - start_time

        try:
            assert manifest.status == "FAILED"
            assert elapsed >= 1.2
            assert elapsed < 4.0
            assert "readiness failed" in (manifest.error_message or "").lower()
        finally:
            igniter.terminate_all()


def test_ignition_port_collision_and_retry():
    """Verify ignition handles port race / collision and retries on a new free port."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        (ws / "index.html").write_text("<html><body>Port Collision Test</body></html>")

        # Pick a target base port and hold it open with a raw socket
        collision_port = 5173
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", collision_port))
            sock.listen(1)

            igniter = ProjectIgniter(workspace_dir=tmpdir)
            manifest = igniter.ignite(objective="Test port collision", timeout=5.0)
            try:
                assert manifest.status in ("READY", "RUNNING")
                assert manifest.frontend_port != collision_port
                assert manifest.frontend_port > collision_port

                # Probe newly bound port
                resp = httpx.get(manifest.primary_url, timeout=3.0)
                assert resp.status_code == 200
                assert "Port Collision Test" in resp.text
            finally:
                igniter.terminate_all()
        finally:
            sock.close()


def test_process_group_isolation_and_no_orphans():
    """Verify kill_process_group kills parent and child worker processes without orphans."""
    # Spawn a process group where parent spawns a child worker
    child_code = (
        "import subprocess, sys, time\n"
        "sub = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "time.sleep(60)\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", child_code],
        start_new_session=True,
    )
    time.sleep(0.5)

    pgid = os.getpgid(proc.pid)
    assert pgid is not None

    # Kill process group
    kill_process_group(pgid, grace_seconds=0.5)

    time.sleep(0.3)
    # Process must have exited (terminated by SIGTERM or SIGKILL)
    assert proc.poll() is not None
    assert proc.returncode in (-signal.SIGTERM, -signal.SIGKILL, 0, 1)

    # Verify no orphan processes in pgid
    try:
        os.killpg(pgid, 0)
        orphan_found = True
    except (ProcessLookupError, PermissionError):
        orphan_found = False
    assert orphan_found is False


def test_ignition_registry_and_cli_ps_and_stop():
    """Verify ~/.octoflow/runs/<id>/ignition.json persistence and octoflow ps/stop commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        (ws / "index.html").write_text("<html><body>Registry Test</body></html>")

        igniter = ProjectIgniter(workspace_dir=tmpdir)
        manifest = igniter.ignite(objective="Test CLI ps and stop", timeout=5.0)

        run_id = igniter.run_id
        try:
            # 1. Verify registry list includes this run_id
            active = list_active_ignitions()
            active_ids = [a["run_id"] for a in active]
            assert run_id in active_ids

            # 2. Run `octoflow ps` CLI
            res_ps = runner.invoke(app, ["ps"])
            assert res_ps.exit_code == 0
            assert run_id in res_ps.output or "ACTIVE" in res_ps.output or "READY" in res_ps.output

            # 3. Run `octoflow stop <run_id>` CLI
            res_stop = runner.invoke(app, ["stop", run_id])
            assert res_stop.exit_code == 0
            assert "successfully stopped" in res_stop.output.lower()

            # Verify manifest status updated to STOPPED
            active_after = list_active_ignitions()
            active_after_ids = [a["run_id"] for a in active_after]
            assert run_id not in active_after_ids
        finally:
            igniter.terminate_all()
