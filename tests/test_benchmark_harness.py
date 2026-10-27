"""Unit tests for OctoFlow benchmark harness, usage accounting, and gate mode baselines."""

import json
import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from octoflow.bench import (
    BENCHMARK_SUITE,
    FakeBenchmarkProvider,
    run_single_benchmark_run,
    generate_summary_markdown,
    run_benchmark_harness,
)
from octoflow.cli import app
from octoflow.gate import SurpriseGate
from octoflow.provider import LLMResponse
from octoflow.tools import ToolResult
from octoflow.usage import UsageLedger, estimate_tokens_from_chars


runner = CliRunner()


def test_usage_ledger_accounting():
    ledger = UsageLedger()
    assert ledger.total_calls == 0
    assert ledger.total_tokens == 0
    assert not ledger.is_estimated

    # Record measured API call
    ledger.record(prompt_tokens=100, completion_tokens=50, estimated=False, provider="anthropic", model="claude-3-5-sonnet")
    assert ledger.total_calls == 1
    assert ledger.prompt_tokens == 100
    assert ledger.completion_tokens == 50
    assert ledger.total_tokens == 150
    assert not ledger.is_estimated
    assert ledger.measured_calls == 1
    assert ledger.estimated_calls == 0

    # Record estimated call
    ledger.record(prompt_tokens=40, completion_tokens=20, estimated=True, provider="mock", model="mock")
    assert ledger.total_calls == 2
    assert ledger.total_tokens == 210
    assert ledger.is_estimated  # Any estimated call marks ledger as estimated
    assert ledger.measured_calls == 1
    assert ledger.estimated_calls == 1

    summary = ledger.summary()
    assert summary["total_calls"] == 2
    assert summary["total_tokens"] == 210
    assert summary["is_estimated"] is True
    assert summary["measured_prompt_tokens"] == 100
    assert summary["estimated_prompt_tokens"] == 40


def test_estimate_tokens_from_chars():
    assert estimate_tokens_from_chars("") == 0
    assert estimate_tokens_from_chars("abcd") == 1
    assert estimate_tokens_from_chars("abcdefgh") == 2
    assert estimate_tokens_from_chars("abcde") == 2  # ceil(5/4) = 2


def test_gate_mode_always_escalate_vs_gated():
    gated_gate = SurpriseGate(arm_id=0, initial_threshold=0.50, gate_mode="gated")
    assert gated_gate.gate_mode == "gated"

    ungated_gate = SurpriseGate(arm_id=0, initial_threshold=0.50, gate_mode="always_escalate")
    assert ungated_gate.gate_mode == "always_escalate"

    # Successful tool result with zero error
    dummy_obs = [0.0] * 16
    tool_res = ToolResult(tool_name="write_file", target="app.py", success=True, returncode=0, stdout="ok")

    # In gated mode, clean execution does not escalate
    esc_gated, surprise_g, _ = gated_gate.evaluate(actual_obs=dummy_obs, tool_result=tool_res)
    assert not esc_gated
    assert gated_gate.silent_steps == 1

    # In always_escalate mode, clean execution still escalates every single time
    esc_ungated, surprise_u, _ = ungated_gate.evaluate(actual_obs=dummy_obs, tool_result=tool_res)
    assert esc_ungated
    assert ungated_gate.escalation_count == 1
    assert ungated_gate.silent_steps == 0


def test_fake_benchmark_provider_known_tokens():
    provider = FakeBenchmarkProvider(prompt_tokens=120, completion_tokens=30, estimated=False)
    ledger = UsageLedger()
    provider.set_ledger(ledger)

    resp = provider.generate("Implement sliding window rate limiter in limiter.py")
    assert resp.tokens_prompt == 120
    assert resp.tokens_completion == 30
    assert resp.total_tokens == 150
    assert not resp.estimated

    assert ledger.total_calls == 1
    assert ledger.total_tokens == 150
    assert not ledger.is_estimated


def test_single_benchmark_run_gated_vs_ungated():
    task = next(t for t in BENCHMARK_SUITE if t.id == "rate_limiter")

    with tempfile.TemporaryDirectory() as tmp_gated:
        # Run gated mode with fake provider
        fake_provider_g = FakeBenchmarkProvider(prompt_tokens=100, completion_tokens=25, estimated=False)
        res_g = run_single_benchmark_run(
            task=task,
            mode="gated",
            provider_name="fake",
            seed=42,
            temperature=0.0,
            workspace_dir=tmp_gated,
            custom_provider=fake_provider_g,
            max_cycles=3,
        )

        assert res_g["task"] == "rate_limiter"
        assert res_g["mode"] == "gated"
        assert res_g["acceptance_test_passed"] is True
        assert "limiter.py" in res_g["files_written"]
        assert res_g["tokens"]["estimated"] is False

    with tempfile.TemporaryDirectory() as tmp_ungated:
        # Run always_escalate mode with fake provider
        fake_provider_u = FakeBenchmarkProvider(prompt_tokens=100, completion_tokens=25, estimated=False)
        res_u = run_single_benchmark_run(
            task=task,
            mode="always_escalate",
            provider_name="fake",
            seed=42,
            temperature=0.0,
            workspace_dir=tmp_ungated,
            custom_provider=fake_provider_u,
            max_cycles=3,
        )

        assert res_u["task"] == "rate_limiter"
        assert res_u["mode"] == "always_escalate"
        assert res_u["acceptance_test_passed"] is True
        assert "limiter.py" in res_u["files_written"]

        # In always_escalate mode, arms do not quiesce after write, making more calls
        assert res_u["llm_calls"] > res_g["llm_calls"]
        assert res_u["tokens"]["total_tokens"] > res_g["tokens"]["total_tokens"]


def test_summary_markdown_statistics():
    fake_runs = [
        # Gated runs (3 runs)
        {
            "task": "rate_limiter",
            "task_name": "Sliding Window Rate Limiter",
            "mode": "gated",
            "provider": "fake",
            "model": "fake-eval-v1",
            "seed": 42,
            "temperature": 0.0,
            "wall_time_seconds": 1.2,
            "llm_calls": 8,
            "tokens": {"prompt_tokens": 800, "completion_tokens": 200, "total_tokens": 1000, "estimated": False},
            "acceptance_test_passed": True,
        },
        {
            "task": "rate_limiter",
            "task_name": "Sliding Window Rate Limiter",
            "mode": "gated",
            "provider": "fake",
            "model": "fake-eval-v1",
            "seed": 43,
            "temperature": 0.0,
            "wall_time_seconds": 1.1,
            "llm_calls": 8,
            "tokens": {"prompt_tokens": 800, "completion_tokens": 200, "total_tokens": 1000, "estimated": False},
            "acceptance_test_passed": True,
        },
        {
            "task": "rate_limiter",
            "task_name": "Sliding Window Rate Limiter",
            "mode": "gated",
            "provider": "fake",
            "model": "fake-eval-v1",
            "seed": 44,
            "temperature": 0.0,
            "wall_time_seconds": 1.3,
            "llm_calls": 8,
            "tokens": {"prompt_tokens": 800, "completion_tokens": 200, "total_tokens": 1000, "estimated": False},
            "acceptance_test_passed": True,
        },
        # Ungated runs (3 runs)
        {
            "task": "rate_limiter",
            "task_name": "Sliding Window Rate Limiter",
            "mode": "always_escalate",
            "provider": "fake",
            "model": "fake-eval-v1",
            "seed": 42,
            "temperature": 0.0,
            "wall_time_seconds": 2.5,
            "llm_calls": 24,
            "tokens": {"prompt_tokens": 2400, "completion_tokens": 600, "total_tokens": 3000, "estimated": False},
            "acceptance_test_passed": True,
        },
        {
            "task": "rate_limiter",
            "task_name": "Sliding Window Rate Limiter",
            "mode": "always_escalate",
            "provider": "fake",
            "model": "fake-eval-v1",
            "seed": 43,
            "temperature": 0.0,
            "wall_time_seconds": 2.4,
            "llm_calls": 24,
            "tokens": {"prompt_tokens": 2400, "completion_tokens": 600, "total_tokens": 3000, "estimated": False},
            "acceptance_test_passed": True,
        },
        {
            "task": "rate_limiter",
            "task_name": "Sliding Window Rate Limiter",
            "mode": "always_escalate",
            "provider": "fake",
            "model": "fake-eval-v1",
            "seed": 44,
            "temperature": 0.0,
            "wall_time_seconds": 2.6,
            "llm_calls": 24,
            "tokens": {"prompt_tokens": 2400, "completion_tokens": 600, "total_tokens": 3000, "estimated": False},
            "acceptance_test_passed": True,
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        summary_path = Path(tmpdir) / "summary.md"
        content = generate_summary_markdown(fake_runs, summary_path)

        assert summary_path.exists()
        assert "OctoFlow Swarm Benchmark Summary" in content
        assert "Methodology" in content
        assert "Limitations" in content
        # Check computed reduction: 1000 / 3000 = 0.333, reduction is 66.7%
        assert "66.7%" in content
        assert "rate_limiter" in content
        assert "**Tokens Estimated:** `False`" in content


def test_full_harness_output_files_and_json():
    with tempfile.TemporaryDirectory() as out_dir:
        result = run_benchmark_harness(
            task="rate_limiter",
            mode="both",
            provider="fake",
            runs=2,
            seed=100,
            out_dir=out_dir,
        )

        assert result["total_runs"] == 4  # 2 modes * 2 runs
        out_path = Path(out_dir)

        # Verify individual run JSON files
        assert (out_path / "rate_limiter_gated_run_1.json").exists()
        assert (out_path / "rate_limiter_gated_run_2.json").exists()
        assert (out_path / "rate_limiter_always_escalate_run_1.json").exists()
        assert (out_path / "rate_limiter_always_escalate_run_2.json").exists()
        assert (out_path / "summary.md").exists()

        # Check JSON schema and content
        data = json.loads((out_path / "rate_limiter_gated_run_1.json").read_text(encoding="utf-8"))
        assert data["task"] == "rate_limiter"
        assert data["mode"] == "gated"
        assert data["provider"] == "fake"
        assert data["seed"] == 100
        assert data["temperature"] == 0.0
        assert "tokens" in data
        assert "prompt_tokens" in data["tokens"]
        assert "completion_tokens" in data["tokens"]
        assert "total_tokens" in data["tokens"]
        assert "estimated" in data["tokens"]
        assert data["acceptance_test_passed"] is True
        assert "limiter.py" in data["files_written"]


def test_cli_bench_help():
    res = runner.invoke(app, ["bench", "--help"])
    assert res.exit_code == 0
    assert "--task" in res.output
    assert "--mode" in res.output
    assert "--provider" in res.output
    assert "--runs" in res.output
    assert "--seed" in res.output
    assert "--out" in res.output
