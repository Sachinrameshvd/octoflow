"""Tests for network egress isolation and zero phoning home (P5.4).

Ensures that OctoFlow runs completely offline / local-only:
- No telemetry phoned home
- No analytics sent to remote hosts
- Sockets strictly restricted to loopback (127.0.0.1 / localhost)
"""

import socket
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from octoflow.cli import app
from octoflow.commands.doctor import run_doctor
from octoflow.conductor import SupraesophagealConductor
from octoflow.config import OctoFlowConfig

runner = CliRunner()


def is_loopback(host: str) -> bool:
    """Check if a host string resolves to a local loopback interface."""
    host_lower = str(host).lower().strip()
    return (
        host_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1")
        or host_lower.startswith("127.")
    )


@pytest.fixture
def strict_loopback_egress_guard():
    """Pytest fixture that blocks all sockets except local loopback."""
    non_loopback_attempts = []
    orig_create_connection = socket.create_connection
    orig_connect = socket.socket.connect

    def guarded_create_connection(address, *args, **kwargs):
        host = address[0] if isinstance(address, (tuple, list)) else address
        port = address[1] if isinstance(address, (tuple, list)) and len(address) > 1 else ""
        if not is_loopback(host):
            non_loopback_attempts.append((host, port))
            raise RuntimeError(f"Egress Blocked: Non-loopback network connection attempt to {host}:{port}")
        return orig_create_connection(address, *args, **kwargs)

    def guarded_connect(self, address):
        host = address[0] if isinstance(address, (tuple, list)) else address
        port = address[1] if isinstance(address, (tuple, list)) and len(address) > 1 else ""
        if not is_loopback(host):
            non_loopback_attempts.append((host, port))
            raise RuntimeError(f"Egress Blocked: Non-loopback network connection attempt to {host}:{port}")
        return orig_connect(self, address)

    with patch("socket.create_connection", side_effect=guarded_create_connection), \
         patch.object(socket.socket, "connect", guarded_connect):
        yield non_loopback_attempts


@pytest.mark.integration_local
def test_full_mission_and_commands_have_zero_egress(strict_loopback_egress_guard, tmp_path):
    """Execute full fake-provider mission with telemetry, doctor, report, bench, and assert zero egress."""
    attempts = strict_loopback_egress_guard

    # 1. Full fake-provider mission with local telemetry enabled
    ws_dir = tmp_path / "egress_test_ws"
    ws_dir.mkdir(parents=True, exist_ok=True)
    cfg = OctoFlowConfig(
        model_provider="fake",
        workspace_dir=str(ws_dir),
        enable_3d_telemetry=True,
        allow_mock=True,
        is_bench=True,
    )
    conductor = SupraesophagealConductor(config=cfg)
    run_result = conductor.run_swarm("Build an egress validation script", max_cycles=1)
    assert run_result is not None
    assert len(attempts) == 0, f"Expected 0 non-loopback egress attempts, got: {attempts}"

    # 2. Run OctoFlow Doctor
    res_doc = runner.invoke(app, ["doctor"])
    assert res_doc.exit_code == 0
    assert len(attempts) == 0, f"Doctor caused non-loopback egress attempts: {attempts}"

    # 3. Run OctoFlow Report export
    report_file = tmp_path / "audit_report.html"
    res_report = runner.invoke(app, ["report", "--out", str(report_file)])
    assert res_report.exit_code == 0
    assert len(attempts) == 0, f"Report caused non-loopback egress attempts: {attempts}"

    # 4. Run Benchmark in fake mode
    bench_dir = tmp_path / "bench_artifacts"
    bench_dir.mkdir(parents=True, exist_ok=True)
    res_bench = runner.invoke(app, ["bench", "--fake", "--task", "rate_limiter", "--runs", "1", "--mode", "gated", "--out", str(bench_dir)])
    assert res_bench.exit_code == 0
    assert len(attempts) == 0, f"Benchmark caused non-loopback egress attempts: {attempts}"

    # 5. Verify intentional non-loopback socket fails and triggers the egress guard
    with pytest.raises(RuntimeError) as exc_info:
        socket.create_connection(("telemetry.evilcorp.com", 443), timeout=1)
    assert "Egress Blocked" in str(exc_info.value)
    assert len(attempts) == 1
    assert attempts[0] == ("telemetry.evilcorp.com", 443)
