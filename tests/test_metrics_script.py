"""Tests for privacy-preserving repository metrics collection script (P12.3)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.metrics import MetricsCollector


@pytest.fixture
def sample_fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "metrics_sample.json"


@pytest.fixture
def sample_fixture_data(sample_fixture_path: Path) -> dict:
    return json.loads(sample_fixture_path.read_text(encoding="utf-8"))


def test_metrics_collector_with_fixture(sample_fixture_data: dict) -> None:
    """Validate calculation of all 10 core metrics from standard fixtures."""
    collector = MetricsCollector(
        repo="octoflow/octoflow",
        package="octoflow",
        fixture_data=sample_fixture_data,
    )

    metrics = collector.compute_all_metrics()

    # 1. PyPI metrics
    pypi = metrics["pypi"]
    assert pypi["last_30_days"] == 1842
    assert pypi["last_7_days"] == 486
    assert pypi["last_day"] == 74
    assert pypi["without_mirrors_30d"] == 1290
    assert pypi["organic_ratio"] == 0.7

    # 2. GitHub community & responsiveness
    gh = metrics["github"]
    assert gh["stars"] == 312
    assert gh["forks"] == 28
    assert gh["open_issues"] == 1
    assert gh["closed_issues"] == 3
    assert gh["median_first_response_hours"] == 9.0  # median of [6.0, 12.0, 24.0, 6.0] -> 9.0
    assert gh["median_bug_close_days"] == 4.0  # median of [3.0, 5.0] -> 4.0
    assert gh["median_pr_merge_hours"] == 24.0

    # 3. Contributor retention
    assert gh["repeat_contributors_count"] == 2  # userA (2 PRs) and userB (2 PRs)
    assert gh["first_time_contributors_90d"] == 3

    # 4. Release cadence & CI
    assert gh["total_releases"] == 3
    assert gh["median_release_cadence_days"] == 29.5  # median of [30.0, 29.0]
    assert gh["ci_pass_rate_pct"] == 95.0  # 19/20 = 95.0%

    # 5. Maintainer targets
    targets = metrics["targets"]
    assert targets["first_response_sla_met"] is True
    assert targets["contributor_retention_met"] is True
    assert targets["release_cadence_met"] is True
    assert targets["ci_pass_rate_met"] is True


def test_metrics_markdown_rendering(sample_fixture_data: dict) -> None:
    """Verify that Markdown rendering adheres to structure, moats, and alerts."""
    collector = MetricsCollector(
        repo="octoflow/octoflow",
        package="octoflow",
        fixture_data=sample_fixture_data,
    )

    data = collector.compute_all_metrics()
    md_output = collector.render_markdown(data)

    assert "Zero Telemetry Commitment" in md_output
    assert "The Download Trap" in md_output
    assert "The GitHub Stars Trap" in md_output
    assert "| **Responsiveness** | Median First Response | `9.0 hours`" in md_output
    assert "| **Retention** | Contributors with 2+ PRs | `2`" in md_output
    assert "Target Met" in md_output


def test_metrics_script_cli_execution(sample_fixture_path: Path, tmp_path: Path) -> None:
    """Verify end-to-end command line execution with fixture inputs."""
    out_md = tmp_path / "METRICS.md"
    out_json = tmp_path / "metrics.json"

    cmd = [
        sys.executable,
        "scripts/metrics.py",
        "--fixture",
        str(sample_fixture_path),
        "--output-md",
        str(out_md),
        "--output-json",
        str(out_json),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    assert res.returncode == 0
    assert out_md.exists()
    assert out_json.exists()

    saved_json = json.loads(out_json.read_text(encoding="utf-8"))
    assert saved_json["pypi"]["last_30_days"] == 1842
    assert saved_json["github"]["repeat_contributors_count"] == 2

    saved_md = out_md.read_text(encoding="utf-8")
    assert "Zero Telemetry Commitment" in saved_md


def test_metrics_collector_empty_fallback() -> None:
    """Verify graceful handling when no issues, PRs, or releases exist."""
    collector = MetricsCollector(
        repo="empty/repo",
        package="empty-pkg",
        fixture_data={
            "pypi_recent": {},
            "pypi_overall": {},
            "repo": {},
            "issues": [],
            "comments": {},
            "pulls": [],
            "releases": [],
            "workflow_runs": [],
        },
    )

    metrics = collector.compute_all_metrics()
    gh = metrics["github"]
    assert gh["open_issues"] == 0
    assert gh["median_first_response_hours"] is None
    assert gh["median_bug_close_days"] is None
    assert gh["repeat_contributors_count"] == 0
    assert gh["ci_pass_rate_pct"] == 100.0
