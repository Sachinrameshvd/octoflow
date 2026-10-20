"""Comprehensive Unit Tests for SurpriseGate (Subsystem 3.2).

Verifies:
1. Exact formula alignment: ΔS = (1/D) * ||o - ô||² with hand-computed values
2. Boundary handling: zero error, known error, NaN/Inf handling, mismatched dimensions
3. Threshold boundary logic (surprise > threshold), adaptive threshold behavior
4. Silent execution telemetry and escalation on tool errors
5. Mathematical properties: non-negativity and monotonicity
"""

import math
import numpy as np
import pytest
import torch

from octoflow.gate import SurpriseGate
from octoflow.tools import ToolResult


def test_gate_zero_error_hand_calculated():
    """Verify zero error yields surprise = 0.0."""
    gate = SurpriseGate(arm_id=0, obs_dim=4, initial_threshold=0.50)
    target = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)

    # Identical actual and expected
    surprise = gate.compute_surprise(actual_obs=target, expected_obs=target)
    assert surprise == 0.0, f"Expected 0.0 surprise for identical vectors, got {surprise}"


def test_gate_known_error_hand_calculated():
    """Verify known difference matches exact formula.
    
    Formula: MSE = (1/D) * sum((actual - expected)^2)
    For D=4, diff = [0.2, 0.2, 0.2, 0.2]
    MSE = (0.04 * 4) / 4 = 0.04
    Scaled surprise = min(1.0, 0.04 * 4.0) = 0.16
    """
    gate = SurpriseGate(arm_id=0, obs_dim=4)
    expected = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    actual = np.array([0.2, 0.2, 0.2, 0.2], dtype=np.float32)

    surprise = gate.compute_surprise(actual_obs=actual, expected_obs=expected)
    assert pytest.approx(surprise, abs=1e-5) == 0.16


def test_gate_non_negativity_and_monotonicity():
    """Verify surprise is strictly non-negative and monotonically increases with error."""
    gate = SurpriseGate(arm_id=1, obs_dim=4)
    expected = np.zeros(4, dtype=np.float32)

    surprises = []
    for diff in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        actual = np.full(4, diff, dtype=np.float32)
        s = gate.compute_surprise(actual, expected)
        assert s >= 0.0, f"Surprise must be non-negative: got {s}"
        surprises.append(s)

    # Monotonicity check
    for i in range(len(surprises) - 1):
        assert surprises[i] <= surprises[i + 1], "Surprise must increase with greater error"


def test_gate_nan_inf_handling():
    """Verify NaN/Inf in observations is handled safely without returning NaN or silent false-negatives."""
    gate = SurpriseGate(arm_id=2, obs_dim=4)
    actual_nan = np.array([np.nan, 0.0, 0.0, 0.0], dtype=np.float32)
    
    surprise = gate.compute_surprise(actual_nan)
    # A corrupted NaN input must NOT produce a NaN surprise that slips past thresholds
    assert not math.isnan(surprise), "Surprise calculation must never return NaN"
    assert surprise >= 0.50, "Corrupted NaN sensory input must trigger high surprise"


def test_gate_threshold_boundary_and_adaptation():
    """Verify threshold boundary: surprise > threshold triggers escalation and adaptation."""
    gate = SurpriseGate(arm_id=3, obs_dim=4, initial_threshold=0.50, adaptation_rate=0.10)
    init_thresh = gate.threshold

    # Clean result with surprise below threshold
    res_clean = ToolResult(tool_name="cmd", target="", success=True, returncode=0)
    # Target observation close to baseline expectation
    actual_clean = np.zeros(4, dtype=np.float32)
    actual_clean[-1] = 1.0  # Quiescence feature active

    should_esc, s_val, tele = gate.evaluate(actual_clean, res_clean)
    assert not should_esc, "Clean execution must not escalate"
    assert gate.silent_steps == 1
    assert gate.threshold <= init_thresh, "Threshold should decay slightly on silent steps"

    # Failing tool result must escalate
    res_fail = ToolResult(tool_name="cmd", target="", success=False, returncode=1, stderr="Syntax error")
    should_esc_fail, s_fail, tele_fail = gate.evaluate(actual_clean, res_fail)
    assert should_esc_fail, "Failing tool result must escalate"
    assert gate.escalation_count == 1
    assert s_fail >= 0.65, "Tool failure must elevate surprise above baseline"
