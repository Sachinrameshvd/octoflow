"""Comprehensive tests for Execution Trace logging and Replay engine (P8.4).

Verifies:
1. --trace creates ~/.octoflow/runs/<id>/trace.jsonl with mode 0600.
2. Default traces contain zero prompt text.
3. --trace-prompts records redacted prompts without leaking raw secrets.
4. octoflow replay reproduces the exact event sequence order.
5. Replay CLI options (--speed, --no-visualizer) function cleanly.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
from octoflow.cli import app
from octoflow.trace import (
    TraceLogger,
    replay_trace,
)
from typer.testing import CliRunner

runner = CliRunner()


def test_trace_creation_fake_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify fake-provider run with --trace creates trace.jsonl with mode 0600 and no prompt text."""
    monkeypatch.setenv("OCTOFLOW_RUNS_DIR", str(tmp_path))
    monkeypatch.setenv("OCTOFLOW_DRY_RUN", "1")

    result = runner.invoke(
        app,
        [
            "run",
            "Verify trace logging and zero prompt leakage",
            "--dry-run",
            "--plain",
            "--trace",
        ],
    )
    assert result.exit_code == 0, f"Run failed: {result.stdout}"

    # Verify trace.jsonl exists under tmp_path/<run_id>/
    trace_files = list(tmp_path.glob("*/trace.jsonl"))
    assert len(trace_files) >= 1, f"Expected trace.jsonl under {tmp_path}, found none"
    trace_file = trace_files[0]

    # Verify permissions mode 0600 (owner read/write only)
    file_stat = trace_file.stat()
    file_mode = stat.S_IMODE(file_stat.st_mode)
    assert file_mode == 0o600, f"Expected mode 0600, got {oct(file_mode)}"

    # Parse trace events and assert NO prompt text exists by default
    raw_content = trace_file.read_text(encoding="utf-8")
    lines = [json.loads(line) for line in raw_content.splitlines() if line.strip()]
    assert len(lines) > 0

    event_types = [entry["event_type"] for entry in lines]
    assert "mission_start" in event_types
    assert "mission_end" in event_types

    # Ensure no prompts or raw prompt fields leaked into trace payloads
    for entry in lines:
        payload = entry.get("payload", {})
        # Ensure direct prompt keys are absent
        for forbidden in ("prompt", "system_prompt", "user_prompt", "messages", "response_content"):
            assert forbidden not in payload, (
                f"Found forbidden prompt key '{forbidden}' in trace entry: {entry}"
            )


def test_trace_prompts_redacted(tmp_path: Path):
    """Verify --trace-prompts records prompts but scrubs secrets."""
    run_id = "test-prompts-run"
    tracer = TraceLogger(run_id=run_id, enabled=True, trace_prompts=True, base_dir=tmp_path)

    secret_key = "sk-ant-testsecretkey99999999999999999999"
    tracer.log_provider_request(
        provider="anthropic",
        model="claude-3-7-sonnet",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        prompt=f"Authorize with {secret_key} and generate code.",
        response="Code generated successfully.",
    )

    trace_file = tmp_path / run_id / "trace.jsonl"
    assert trace_file.exists()
    content = trace_file.read_text(encoding="utf-8")

    assert secret_key not in content, "Secret key leaked into trace.jsonl"
    assert "[REDACTED" in content
    assert "Code generated successfully." in content


def test_replay_exact_event_sequence_order(tmp_path: Path):
    """Verify replay reproduces the exact event sequence order."""
    run_id = "test-replay-order"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    trace_file = run_dir / "trace.jsonl"

    synthetic_events = [
        {
            "timestamp": 100.0,
            "event_type": "mission_start",
            "payload": {"objective": "Test replay"},
        },
        {
            "timestamp": 100.1,
            "event_type": "gate_eval",
            "payload": {"arm_id": 1, "surprise": 0.1, "threshold": 0.5, "decision": "reflex"},
        },
        {
            "timestamp": 100.2,
            "event_type": "tool_call",
            "payload": {"arm_id": 1, "tool_name": "read_file", "success": True},
        },
        {
            "timestamp": 100.3,
            "event_type": "provider_request",
            "payload": {"provider": "mock", "model": "sim", "total_tokens": 120},
        },
        {
            "timestamp": 100.4,
            "event_type": "telemetry",
            "payload": {"event_type": "STEP", "arm_id": 1, "role": "database", "summary": "step 1"},
        },
        {"timestamp": 100.5, "event_type": "mission_end", "payload": {"outcome": "complete"}},
    ]

    with trace_file.open("w", encoding="utf-8") as f:
        for evt in synthetic_events:
            f.write(json.dumps(evt) + "\n")
    trace_file.chmod(0o600)

    # Replay trace and verify order
    output_lines: list[str] = []
    resolved_id, replayed = replay_trace(
        run_id=run_id,
        speed=0.0,
        no_visualizer=True,
        base_dir=tmp_path,
        output_fn=output_lines.append,
    )

    assert resolved_id == run_id
    assert len(replayed) == len(synthetic_events)

    expected_types = [e["event_type"] for e in synthetic_events]
    actual_types = [e["event_type"] for e in replayed]
    assert actual_types == expected_types

    # Ensure formatted lines contain expected glyphs and descriptions
    combined_output = "\n".join(output_lines)
    assert "MISSION START" in combined_output
    assert "GATE" in combined_output
    assert "TOOL" in combined_output
    assert "LLM" in combined_output
    assert "TELEMETRY" in combined_output
    assert "MISSION END" in combined_output


def test_replay_cli_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify 'octoflow replay' CLI command functions with flags."""
    monkeypatch.setenv("OCTOFLOW_RUNS_DIR", str(tmp_path))

    run_id = "test-cli-replay"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    trace_file = run_dir / "trace.jsonl"
    trace_file.write_text(
        json.dumps(
            {
                "timestamp": 1.0,
                "event_type": "mission_start",
                "payload": {"objective": "CLI Replay"},
            }
        )
        + "\n"
        + json.dumps(
            {"timestamp": 1.1, "event_type": "mission_end", "payload": {"outcome": "complete"}}
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "latest_run_id").write_text(run_id, encoding="utf-8")

    result = runner.invoke(app, ["replay", "latest", "--speed", "0", "--no-visualizer"])
    assert result.exit_code == 0
    assert "OctoFlow Replay: Run [test-cli-replay]" in result.stdout
    assert "Replay of run [test-cli-replay] completed" in result.stdout
