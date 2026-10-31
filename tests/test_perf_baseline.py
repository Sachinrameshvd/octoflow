"""Smoke tests for scripts/perf_baseline.py benchmark collector (P4.3).

Verifies that the performance baseline script runs in --quick mode,
produces valid JSON conforming to the schema, and evaluates soft thresholds.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.unit
def test_perf_baseline_quick_execution(tmp_path: Path):
    """Verify that perf_baseline.py executes in --quick mode and emits valid JSON."""
    repo_root = Path(__file__).resolve().parent.parent
    script_path = repo_root / "scripts" / "perf_baseline.py"
    output_file = tmp_path / "baseline_test.json"
    thresholds_file = repo_root / "benchmarks" / "perf" / "thresholds.json"

    cmd = [
        sys.executable,
        str(script_path),
        "--quick",
        "--output",
        str(output_file),
    ]
    if thresholds_file.exists():
        cmd.extend(["--check-thresholds", str(thresholds_file)])

    res = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
    assert res.returncode == 0, (
        f"perf_baseline.py failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    )

    assert output_file.exists(), "Output baseline JSON file was not generated"

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["version"] == "1.0"
    assert data["phase"] == "P4.3"
    assert data["mode"] == "quick"

    # Validate machine metadata
    machine = data["machine"]
    assert "system" in machine
    assert "python_version" in machine
    assert "cpu_count_logical" in machine

    # Validate core metric categories
    metrics = data["metrics"]
    assert "help_startup" in metrics
    assert "import_times" in metrics
    assert "cockpit_idle" in metrics
    assert "frame_render" in metrics
    assert "visualizer_dist" in metrics
    assert "install_size" in metrics

    # Validate numeric ranges
    assert metrics["help_startup"]["median_seconds"] > 0
    assert metrics["frame_render"]["p95_ms"] > 0
    assert metrics["frame_render"]["p95_ms"] < 100.0  # Sanity bound
    assert metrics["cockpit_idle"]["cpu_percent_median"] >= 0.0
