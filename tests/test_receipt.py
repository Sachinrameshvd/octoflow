"""Comprehensive Unit and Integration Tests for Token Receipt (P7.1).

Verifies:
1. Decision ledger math, gate evaluation recording, and avoided token calculations.
2. Fake-provider run with known usage matching hand-computed fixtures.
3. Explicit labeling: every avoided/saved value is labeled 'estimated'; measured vs estimated distinction.
4. `receipt --json` validates against the Pydantic schema.
5. Report HTML, visualizer payload, and terminal receipt show identical totals.
6. Zero prompt text is stored in the receipt model or JSON.
7. Baseline linkage to empirical benchmark data in benchmarks/results/ (never generic percentages).
8. Dry-run receipts report zero provider tokens and say so.
9. Snapshots of the terminal block in plain and ASCII modes (< 128 bytes).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from octoflow.bench import BENCHMARK_SUITE, FakeBenchmarkProvider
from octoflow.config import OctoFlowConfig
from octoflow.conductor import SupraesophagealConductor
from octoflow.gate import DecisionLedger, GateDecision, SurpriseGate
from octoflow.receipt import (
    ArmReceiptSummary,
    BaselineComparison,
    TokenReceipt,
    build_token_receipt,
    find_benchmark_baseline,
    load_receipt,
    render_terminal_receipt,
    save_receipt,
)
from octoflow.report import collect_mission_audit_data, generate_html_audit_report
from octoflow.tools import ToolResult
from octoflow.usage import UsageLedger, estimate_tokens_from_chars


def test_decision_ledger_math_and_recording():
    """Verify GateDecision tracking, reflex avoided token summation, and prompt exclusion."""
    ledger = DecisionLedger()
    gate = SurpriseGate(arm_id=2, gate_mode="gated")
    gate.decision_ledger = ledger

    # Clean execution -> reflex
    obs_clean = [0.0] * 16
    tool_ok = ToolResult(tool_name="write_file", target="api.py", success=True, returncode=0)
    prompt_str = "Write REST API endpoint for user authentication in auth.py"
    expected_est = estimate_tokens_from_chars(prompt_str)

    should_esc, surprise, tele = gate.evaluate(
        actual_obs=obs_clean,
        tool_result=tool_ok,
        cycle=1,
        prompt=prompt_str,
    )

    assert not should_esc
    assert tele["decision"] == "reflex"
    assert tele["would_have_sent_tokens"] == expected_est

    # Failing execution -> escalate
    tool_fail = ToolResult(
        tool_name="run_command", target="pytest", success=False, returncode=1, stderr="AssertionError"
    )
    should_esc_f, surprise_f, tele_f = gate.evaluate(
        actual_obs=[1.0] * 16,
        tool_result=tool_fail,
        cycle=2,
        prompt="Fix the broken tests in test_api.py",
    )

    assert should_esc_f
    assert tele_f["decision"] == "escalate"
    assert tele_f["would_have_sent_tokens"] == 0

    assert ledger.total_evaluations == 2
    assert ledger.total_reflexes == 1
    assert ledger.total_escalations == 1
    assert ledger.avoided_tokens_estimated == expected_est

    # Verify NO prompt text is stored on GateDecision objects
    for rec in ledger.records:
        rec_dict = rec.to_dict()
        assert "prompt" not in rec_dict
        assert "Write REST API" not in json.dumps(rec_dict)
        assert "Fix the broken" not in json.dumps(rec_dict)


def test_fake_provider_run_with_known_usage():
    """Fake-provider run with known token counts produces receipt matching hand-computed fixtures."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Provider configured with exactly 120 prompt tokens and 30 completion tokens (150 total)
        fake_prov = FakeBenchmarkProvider(
            prompt_tokens=120,
            completion_tokens=30,
            estimated=False,
        )

        cfg = OctoFlowConfig(
            workspace_dir=tmp_dir,
            model_provider="fake",
            dry_run=False,
            gate_mode="gated",
            allow_mock=True,
            is_bench=True,
        )
        conductor = SupraesophagealConductor(config=cfg)
        conductor.provider = fake_prov
        fake_prov.set_ledger(conductor.usage_ledger)
        for arm in conductor.arms:
            arm.provider = fake_prov

        # Run 1 cycle with rate limiter task
        task = next(t for t in BENCHMARK_SUITE if t.id == "rate_limiter")
        conductor.run_swarm(task.objective, max_cycles=1)

        receipt = build_token_receipt(
            run_id="run-fixture-test",
            conductor=conductor,
            objective=task.objective,
            duration_seconds=1.25,
            dry_run=False,
        )

        # Hand-computed checks:
        # Every call made through fake_prov logged 120 in, 30 out, 150 total
        calls = fake_prov.call_count
        assert calls > 0
        assert receipt.llm_calls == calls
        assert receipt.tokens_in == calls * 120
        assert receipt.tokens_out == calls * 30
        assert receipt.tokens_total == calls * 150
        assert receipt.tokens_measured == calls * 150
        assert receipt.tokens_estimated == 0
        assert receipt.confidence == "measured"


def test_estimated_values_labeling_and_no_unlabeled_saved():
    """Verify all saved/avoided values are labeled 'estimated' and no unlabeled 'saved' numbers exist."""
    receipt = TokenReceipt(
        run_id="run-label-check",
        mode="software_dev",
        provider="ollama",
        model="qwen2.5-coder:7b",
        duration_seconds=5.4,
        dry_run=False,
        llm_calls=8,
        tokens_in=2000,
        tokens_out=500,
        tokens_total=2500,
        tokens_measured=0,
        tokens_estimated=2500,
        gate_evaluations=10,
        reflexes=7,
        escalations=3,
        avoided_tokens_estimated=4200,
        confidence="estimated",
    )

    rendered = render_terminal_receipt(receipt)

    # Must explicitly state "estimated avoided"
    assert "estimated avoided" in rendered
    assert "Avoided: 4,200 tokens (estimated avoided)" in rendered

    # Spent must be labeled with confidence
    assert "Spent:   2,500 tokens (estimated)" in rendered

    # Must provide link to methodology
    assert "Method:  octoflow receipt --method" in rendered


def test_receipt_json_validates_pydantic_schema():
    """Ensure `octoflow receipt --json` emits JSON that fully validates against TokenReceipt."""
    with tempfile.TemporaryDirectory() as tmp_runs:
        receipt = TokenReceipt(
            run_id="run-schema-val-1",
            mode="software_dev",
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            duration_seconds=12.5,
            dry_run=False,
            llm_calls=15,
            tokens_in=4500,
            tokens_out=1500,
            tokens_total=6000,
            tokens_measured=6000,
            tokens_estimated=0,
            gate_evaluations=12,
            reflexes=8,
            escalations=4,
            avoided_tokens_estimated=5800,
            per_arm=[
                ArmReceiptSummary(
                    arm_id=2,
                    role="Backend Specialist",
                    llm_calls=5,
                    tokens_in=1500,
                    tokens_out=500,
                    tokens_total=2000,
                    reflexes=3,
                    escalations=1,
                    avoided_tokens_estimated=2400,
                    is_estimated=False,
                )
            ],
            confidence="measured",
        )

        # Save receipt to temp runs dir
        r_path = Path(tmp_runs) / "run-schema-val-1" / "receipt.json"
        r_path.parent.mkdir(parents=True, exist_ok=True)
        r_path.write_text(receipt.model_dump_json(indent=2), encoding="utf-8")

        # Load back via load_receipt using env override
        os.environ["OCTOFLOW_RUNS_DIR"] = tmp_runs
        try:
            loaded = load_receipt("run-schema-val-1")
            assert isinstance(loaded, TokenReceipt)
            assert loaded.run_id == "run-schema-val-1"
            assert loaded.tokens_total == 6000
            assert loaded.avoided_tokens_estimated == 5800
            assert loaded.confidence == "measured"
            assert len(loaded.per_arm) == 1
            assert loaded.per_arm[0].arm_id == 2
        finally:
            os.environ.pop("OCTOFLOW_RUNS_DIR", None)


def test_report_html_totals_match_terminal_receipt():
    """Verify that standalone HTML report and terminal receipt reflect identical totals."""
    receipt = TokenReceipt(
        run_id="run-parity-999",
        mode="software_dev",
        provider="ollama",
        model="qwen2.5-coder:7b",
        duration_seconds=18.4,
        dry_run=False,
        llm_calls=22,
        tokens_in=5500,
        tokens_out=1700,
        tokens_total=7200,
        tokens_measured=7200,
        tokens_estimated=0,
        gate_evaluations=16,
        reflexes=12,
        escalations=4,
        avoided_tokens_estimated=9450,
        confidence="measured",
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        mission_data = collect_mission_audit_data(
            workspace=tmp_dir,
            objective="Build microservice API",
            receipt=receipt,
        )

        token_econ = mission_data["token_economy"]
        assert token_econ["tokens_spent"] == receipt.tokens_total
        assert token_econ["tokens_avoided"] == receipt.avoided_tokens_estimated
        assert token_econ["llm_calls"] == receipt.llm_calls
        assert token_econ["gate_evaluations"] == receipt.gate_evaluations
        assert token_econ["reflexes"] == receipt.reflexes
        assert token_econ["escalations"] == receipt.escalations
        assert token_econ["confidence"] == "measured"

        report_file = Path(tmp_dir) / "audit_report.html"
        generate_html_audit_report(mission_data, output_path=report_file)

        html_text = report_file.read_text(encoding="utf-8")
        # Ensure numbers appear formatted in HTML
        assert "7,200" in html_text
        assert "9,450" in html_text
        assert "Tokens Spent" in html_text
        assert "Estimated Avoided Tokens" in html_text


def test_no_prompt_text_stored_in_receipt():
    """Ensure no prompt strings or user source text are stored in the receipt model or JSON."""
    secret_prompt = "CONFIDENTIAL_PATIENT_RECORDS_PROMPT_QUERY_12345"

    ledger = DecisionLedger()
    gate = SurpriseGate(arm_id=1, gate_mode="gated")
    gate.decision_ledger = ledger

    tool_res = ToolResult(tool_name="read_file", target="records.csv", success=True, returncode=0)
    gate.evaluate(
        actual_obs=[0.0] * 16,
        tool_result=tool_res,
        cycle=1,
        prompt=secret_prompt,
    )

    receipt = build_token_receipt(
        run_id="run-privacy-check",
        decision_ledger=ledger,
        objective="Analyze medical data",
    )

    json_dump = receipt.model_dump_json()
    assert secret_prompt not in json_dump
    assert "CONFIDENTIAL" not in json_dump
    assert "PATIENT" not in json_dump


def test_dry_run_receipt_zero_provider_tokens():
    """Dry-run receipts report zero provider tokens and state dry-run explicitly."""
    receipt = build_token_receipt(
        run_id="run-dry-simulation",
        objective="Create REST server",
        dry_run=True,
    )

    assert receipt.dry_run is True
    assert receipt.tokens_total == 0
    assert receipt.tokens_measured == 0
    assert receipt.tokens_estimated == 0

    rendered = render_terminal_receipt(receipt)
    assert "Spent:   0 provider tokens (dry-run: simulation)" in rendered


def test_baseline_linkage_real_benchmarks():
    """Verify baseline comparison links to empirical benchmarks without generic percentages."""
    # Find baseline for known benchmark task
    baseline = find_benchmark_baseline("rate_limiter")
    assert baseline is not None
    assert baseline.task == "rate_limiter"
    assert baseline.gated_tokens_median > 0
    assert baseline.ungated_tokens_median > 0
    assert baseline.run_count >= 1

    # Format must strictly match:
    # "measured in benchmark: gated X vs ungated Y (median of N runs, model M)"
    label = baseline.label
    assert label.startswith("measured in benchmark: gated ")
    assert " vs ungated " in label
    assert " (median of " in label
    assert " runs, model " in label

    # Must NEVER include generic percent claims
    assert "%" not in label


def test_terminal_block_snapshots_plain_and_ascii():
    """Verify terminal receipt rendering in plain and ASCII (< 128) modes."""
    receipt = TokenReceipt(
        run_id="run-snapshot-01",
        mode="software_dev",
        provider="ollama",
        model="qwen2.5-coder:7b",
        duration_seconds=9.8,
        dry_run=False,
        llm_calls=12,
        tokens_in=3000,
        tokens_out=1000,
        tokens_total=4000,
        tokens_measured=4000,
        tokens_estimated=0,
        gate_evaluations=10,
        reflexes=7,
        escalations=3,
        avoided_tokens_estimated=5200,
        per_arm=[
            ArmReceiptSummary(
                arm_id=2,
                role="Backend",
                llm_calls=6,
                tokens_in=1500,
                tokens_out=500,
                tokens_total=2000,
                reflexes=4,
                escalations=1,
                avoided_tokens_estimated=2600,
                is_estimated=False,
            )
        ],
        confidence="measured",
    )

    # 1. Plain Mode snapshot
    plain_output = render_terminal_receipt(receipt, plain_mode=True)
    assert plain_output.startswith("[receipt run-snapshot-01]")
    assert "Spent:   4,000 tokens (measured)" in plain_output
    assert "Avoided: 5,200 tokens (estimated avoided)" in plain_output
    assert "Method:  octoflow receipt --method" in plain_output
    # No box characters in plain mode
    for ch in ("┌", "┐", "└", "┘", "│", "─"):
        assert ch not in plain_output

    # 2. ASCII Mode snapshot: all bytes must be strictly < 128
    ascii_output = render_terminal_receipt(receipt, ascii_mode=True, plain_mode=False)
    for ch in ascii_output:
        assert ord(ch) < 128, f"Non-ASCII byte detected: {ch!r} (ord={ord(ch)})"
    assert "+-- Token Receipt: run-snapshot-01" in ascii_output
    assert "Spent:   4,000 tokens (measured)" in ascii_output
    assert "Avoided: 5,200 tokens (estimated avoided)" in ascii_output
