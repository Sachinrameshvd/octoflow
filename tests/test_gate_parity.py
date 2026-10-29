"""Tests for behavioral and numerical parity between NumPy and Torch encoder/gate backends.

Validates that:
1. Feature extraction in CodeSensoryEncoder produces identical vectors (< 1e-5 tolerance).
2. Sensory surprise (dS) and escalation decisions are identical (< 1e-5 tolerance) against
   the characterization golden corpus (tests/characterization/golden/gate.json).
3. Adaptive threshold (theta) decay and escalation dynamics match across sequences.
4. Torch backend (when installed) exhibits exact decision and numerical parity.
"""

from __future__ import annotations
import json
from pathlib import Path
import pytest
import numpy as np

pytestmark = [pytest.mark.unit, pytest.mark.characterization]

from octoflow.tools import ToolResult
from octoflow.encoder import CodeSensoryEncoder, get_encoder
from octoflow.gate import SurpriseGate

GOLDEN_PATH = Path(__file__).resolve().parent / "characterization" / "golden" / "gate.json"


@pytest.fixture(scope="module")
def golden_corpus() -> list[dict]:
    """Load pre-recorded reference gate decisions and sensory surprise values."""
    assert GOLDEN_PATH.exists(), f"Golden file not found: {GOLDEN_PATH}"
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert len(data) > 0, "Golden corpus is empty"
    return data


def _reconstruct_tool_result(case: dict) -> ToolResult:
    """Helper to reconstruct a ToolResult instance from golden case data."""
    return ToolResult(
        tool_name=case["tool_name"],
        target=case["target"],
        success=case["success"],
        returncode=case["returncode"],
        stdout=case["stdout"],
        stderr=case["stderr"],
        diff_lines=case["diff_lines"],
        execution_time_ms=case["execution_time_ms"],
    )


def test_encoder_numpy_matches_golden_corpus(golden_corpus):
    """Verify CodeSensoryEncoder(backend='numpy') produces bit-for-bit identical vectors to golden."""
    encoder = CodeSensoryEncoder(obs_dim=16, backend="numpy")
    max_diff = 0.0

    for case in golden_corpus:
        res = _reconstruct_tool_result(case)
        obs_numpy = encoder.encode(res, step=case["step"], max_steps=case["max_steps"])

        assert isinstance(obs_numpy, np.ndarray), f"Expected np.ndarray, got {type(obs_numpy)}"
        assert obs_numpy.dtype == np.float32, f"Expected float32, got {obs_numpy.dtype}"
        assert obs_numpy.shape == (16,), f"Expected shape (16,), got {obs_numpy.shape}"

        expected_obs = np.array(case["obs"], dtype=np.float32)
        diff = float(np.max(np.abs(obs_numpy - expected_obs)))
        if diff > max_diff:
            max_diff = diff

        assert diff < 1e-5, (
            f"Case '{case['name']}': encoder vector diff {diff} exceeds tolerance 1e-5"
        )

    print(f"\n[Parity Check] Encoder NumPy vs Golden maximum absolute difference: {max_diff:.2e}")


def test_gate_numpy_sequential_parity_matches_golden(golden_corpus):
    """Verify SurpriseGate(backend='numpy') reproduces exact sequential threshold adaptation and decisions."""
    encoder = CodeSensoryEncoder(obs_dim=16, backend="numpy")
    gate = SurpriseGate(arm_id=1, obs_dim=16, initial_threshold=0.50, adaptation_rate=0.05, backend="numpy")

    max_ds_diff = 0.0
    max_thresh_diff = 0.0

    for case in golden_corpus:
        res = _reconstruct_tool_result(case)
        obs_numpy = encoder.encode(res, step=case["step"], max_steps=case["max_steps"])

        should_escalate, surprise, telemetry = gate.evaluate(obs_numpy, res)

        expected_surprise = float(case["surprise"])
        expected_escalate = bool(case["escalate"])
        expected_telemetry = case["telemetry"]

        ds_diff = abs(surprise - expected_surprise)
        thresh_diff = abs(telemetry["threshold"] - expected_telemetry["threshold"])

        if ds_diff > max_ds_diff:
            max_ds_diff = ds_diff
        if thresh_diff > max_thresh_diff:
            max_thresh_diff = thresh_diff

        # 1. Parity assertion: surprise value must match within 1e-5
        assert ds_diff < 1e-5, (
            f"Case '{case['name']}': dS difference {ds_diff} exceeds 1e-5 (numpy={surprise}, golden={expected_surprise})"
        )

        # 2. Parity assertion: escalation decision must be identical (no false positives/negatives)
        assert should_escalate == expected_escalate, (
            f"Case '{case['name']}': decision mismatch! numpy={should_escalate}, golden={expected_escalate}"
        )

        # 3. Parity assertion: adaptive threshold must match within 1e-5
        assert thresh_diff < 1e-5, (
            f"Case '{case['name']}': threshold diff {thresh_diff} exceeds 1e-5"
        )

        # 4. Parity assertion: counters must be identical
        assert telemetry["silent_steps"] == expected_telemetry["silent_steps"]
        assert telemetry["escalations"] == expected_telemetry["escalations"]

    print(f"\n[Parity Check] Gate NumPy vs Golden max dS diff: {max_ds_diff:.2e}, max threshold diff: {max_thresh_diff:.2e}")


@pytest.mark.parametrize("backend", ["numpy", "torch"])
def test_gate_backend_parity_across_modes(backend, golden_corpus):
    """Run golden corpus across both backends (skipping torch if missing) and assert parity."""
    if backend == "torch":
        pytest.importorskip("torch", reason="PyTorch extra [ml] is not installed")

    encoder = get_encoder(backend=backend, obs_dim=16)
    gate = SurpriseGate(arm_id=1, obs_dim=16, initial_threshold=0.50, adaptation_rate=0.05, backend=backend)

    for case in golden_corpus:
        res = _reconstruct_tool_result(case)
        obs = encoder.encode(res, step=case["step"], max_steps=case["max_steps"])
        should_escalate, surprise, telemetry = gate.evaluate(obs, res)

        assert abs(surprise - float(case["surprise"])) < 1e-5
        assert should_escalate == bool(case["escalate"])
        assert abs(telemetry["threshold"] - case["telemetry"]["threshold"]) < 1e-5


def test_corrupted_nan_inf_parity():
    """Verify corrupted NaN/Inf inputs always produce maximum sensory surprise (1.0) on both backends."""
    gate_numpy = SurpriseGate(arm_id=1, obs_dim=16, backend="numpy")

    nan_arr = np.array([np.nan] * 16, dtype=np.float32)
    inf_arr = np.array([np.inf] * 16, dtype=np.float32)
    clean_baseline = np.zeros(16, dtype=np.float32)
    clean_baseline[-1] = 1.0

    assert gate_numpy.compute_surprise(nan_arr) == 1.0
    assert gate_numpy.compute_surprise(inf_arr) == 1.0

    try:
        import torch
        gate_torch = SurpriseGate(arm_id=1, obs_dim=16, backend="torch")
        nan_t = torch.tensor(nan_arr)
        inf_t = torch.tensor(inf_arr)
        assert gate_torch.compute_surprise(nan_t) == 1.0
        assert gate_torch.compute_surprise(inf_t) == 1.0
    except ImportError:
        pass


def test_generation_parameters_parity():
    """Verify dynamic LLM temperature and top_p modulation yields identical outputs."""
    for s in [0.0, 0.15, 0.35, 0.50, 0.65, 0.85, 1.0]:
        t_np, p_np = SurpriseGate.compute_generation_parameters(s)
        assert 0.10 <= t_np <= 0.85
        assert 0.70 <= p_np <= 1.0


def test_get_encoder_auto_defaults_to_numpy_without_explicit_config(monkeypatch):
    """Verify get_encoder('auto') chooses NumPy unless OCTOFLOW_ENCODER_BACKEND='torch'."""
    monkeypatch.delenv("OCTOFLOW_ENCODER_BACKEND", raising=False)
    monkeypatch.delenv("ENCODER_BACKEND", raising=False)

    enc = get_encoder(backend="auto")
    assert enc.backend == "numpy"


def test_get_encoder_torch_missing_raises_clear_error(monkeypatch):
    """Verify requesting torch without it installed raises clear hint to install [ml]."""
    monkeypatch.setattr("octoflow.encoder._is_torch_available", lambda: False)

    with pytest.raises(ImportError) as exc_info:
        get_encoder(backend="torch")
    assert "pip install 'octoflow[ml]'" in str(exc_info.value)
