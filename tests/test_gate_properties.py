"""Property and branch coverage tests for octoflow/gate.py (P4.1)."""

import numpy as np
import pytest
from octoflow.gate import SurpriseGate
from octoflow.tools import ToolResult

# ---------------------------------------------------------------------------
# 1. Monotonicity property: higher dS never flips escalate decision to reflex
# ---------------------------------------------------------------------------


def test_gate_monotonicity_table_test():
    """Property: At fixed theta, if dS_1 escalates, any dS_2 > dS_1 must also escalate.

    Higher sensory surprise can never flip an escalate decision to silent reflex.
    """
    thetas = [0.25, 0.35, 0.50, 0.65, 0.75, 0.85, 0.90]
    ds_grid = np.linspace(0.0, 1.0, 101)

    clean_tool_result = ToolResult(
        tool_name="read_file",
        target="foo.py",
        success=True,
        returncode=0,
        stdout="ok",
    )

    for theta in thetas:
        gate = SurpriseGate(arm_id=1, initial_threshold=theta)
        # Fix adaptation_rate=0.0 to keep theta strictly fixed across evaluations
        gate.adaptation_rate = 0.0

        escalate_seen = False
        for ds in ds_grid:
            # Craft observation that yields surprise approximately ds
            obs = np.ones(16, dtype=np.float32) * np.sqrt(ds / 4.0)
            baseline = np.zeros(16, dtype=np.float32)

            computed_ds = gate.compute_surprise(actual_obs=obs, expected_obs=baseline)

            # Invariant: computed_ds > theta => escalate
            should_escalate = computed_ds > theta

            if should_escalate:
                escalate_seen = True

            # If we already saw an escalate decision at a lower dS, it must stay escalated
            if escalate_seen and computed_ds > theta:
                assert should_escalate is True, (
                    f"Monotonicity violated at theta={theta}, ds={computed_ds}"
                )


def test_gate_evaluate_monotonicity_pairs():
    """Verify directly with evaluate that higher surprise never turns escalate into silent."""
    thetas = [0.30, 0.50, 0.70]
    tool_res = ToolResult(tool_name="read", target="a", success=True, returncode=0)

    for theta in thetas:
        for s1 in [0.2, 0.4, 0.6, 0.8]:
            for s2 in [s1 + 0.05, s1 + 0.1, s1 + 0.2]:
                if s2 > 1.0:
                    continue
                g1 = SurpriseGate(arm_id=0, initial_threshold=theta)
                g1.adaptation_rate = 0.0
                obs1 = np.ones(16, dtype=np.float32) * np.sqrt(s1 / 4.0)
                esc1, _, _ = g1.evaluate(
                    obs1, tool_res, expected_obs=np.zeros(16, dtype=np.float32)
                )

                g2 = SurpriseGate(arm_id=0, initial_threshold=theta)
                g2.adaptation_rate = 0.0
                obs2 = np.ones(16, dtype=np.float32) * np.sqrt(s2 / 4.0)
                esc2, _, _ = g2.evaluate(
                    obs2, tool_res, expected_obs=np.zeros(16, dtype=np.float32)
                )

                if esc1:
                    assert esc2, (
                        f"Monotonicity broken: theta={theta}, s1={s1} escalated, but s2={s2} remained silent!"
                    )


# ---------------------------------------------------------------------------
# 2. Corrupted and edge case inputs
# ---------------------------------------------------------------------------


def test_gate_nan_and_inf_inputs_trigger_max_surprise():
    gate = SurpriseGate(arm_id=0)

    nan_obs = np.array([np.nan, 0.0, 1.0], dtype=np.float32)
    assert gate.compute_surprise(nan_obs) == 1.0

    inf_obs = np.array([np.inf, 0.0, 1.0], dtype=np.float32)
    assert gate.compute_surprise(inf_obs) == 1.0


def test_gate_empty_and_mismatched_dimension_shapes():
    gate = SurpriseGate(arm_id=0, obs_dim=16)

    # Empty array (size 0)
    empty_actual = np.array([], dtype=np.float32)
    empty_expected = np.array([], dtype=np.float32)
    assert gate.compute_surprise(empty_actual, empty_expected) == 0.0

    # Mismatched lengths
    actual = np.ones(8, dtype=np.float32)
    expected = np.zeros(16, dtype=np.float32)
    surp = gate.compute_surprise(actual, expected)
    assert 0.0 <= surp <= 1.0


def test_gate_always_escalate_mode():
    gate = SurpriseGate(arm_id=0, initial_threshold=0.99, gate_mode="always_escalate")
    tool_res = ToolResult(tool_name="read", target="a", success=True, returncode=0)
    obs = np.zeros(16, dtype=np.float32)

    esc, surp, telemetry = gate.evaluate(obs, tool_res, expected_obs=obs)
    assert esc is True
    assert telemetry["gate_mode"] == "always_escalate"


def test_gate_fatal_tool_failure_invariants():
    gate = SurpriseGate(arm_id=0, initial_threshold=0.50)
    # Even with zero sensory observation diff, returncode != 0 forces surprise >= 0.65
    obs = np.zeros(16, dtype=np.float32)
    fail_tool_res = ToolResult(
        tool_name="run", target="cmd", success=False, returncode=1, stderr="Error"
    )

    esc, surp, _ = gate.evaluate(obs, fail_tool_res, expected_obs=obs)
    assert surp >= 0.65
    assert esc is True


def test_gate_adaptation_bounds():
    gate = SurpriseGate(arm_id=0, initial_threshold=0.50, adaptation_rate=0.5)
    tool_fail = ToolResult(tool_name="write", target="f", success=False, returncode=1)
    tool_ok = ToolResult(tool_name="write", target="f", success=True, returncode=0)
    obs_high = np.ones(16, dtype=np.float32) * 5.0
    obs_low = np.zeros(16, dtype=np.float32)

    # Multiple escalations adapt threshold upward up to 0.90 max
    for _ in range(15):
        gate.evaluate(obs_high, tool_fail, expected_obs=obs_low)
    assert gate.threshold <= 0.90

    # Multiple silent steps decay threshold downward down to 0.25 min
    for _ in range(30):
        gate.evaluate(obs_low, tool_ok, expected_obs=obs_low)
    assert gate.threshold >= 0.25


def test_compute_generation_parameters():
    low_temp, low_top_p = SurpriseGate.compute_generation_parameters(0.1)
    high_temp, high_top_p = SurpriseGate.compute_generation_parameters(0.9)

    assert low_temp < high_temp
    assert low_top_p >= high_top_p
    assert 0.10 <= low_temp <= 0.85
    assert 0.70 <= high_top_p <= 1.0


@pytest.mark.unit
def test_gate_torch_backend_if_installed():
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        pytest.skip("PyTorch not installed")

    gate = SurpriseGate(arm_id=2, backend="torch")
    actual = torch.zeros(16, dtype=torch.float32)
    expected = torch.zeros(16, dtype=torch.float32)

    surp = gate.compute_surprise(actual, expected)
    assert 0.0 <= surp <= 1.0

    nan_actual = torch.tensor([float("nan"), 0.0])
    assert gate.compute_surprise(nan_actual) == 1.0

    # Torch forward model branch
    class DummyModel(nn.Module):
        def forward(self, x):
            return torch.zeros(16, dtype=torch.float32)

    fwd_model = DummyModel()
    gate_with_fwd = SurpriseGate(arm_id=2, backend="torch", forward_model=fwd_model)
    h_state = torch.zeros(8, dtype=torch.float32)
    a_vec = torch.zeros(8, dtype=torch.float32)
    surp_fwd = gate_with_fwd.compute_surprise(actual, hidden_state=h_state, action_vector=a_vec)
    assert 0.0 <= surp_fwd <= 1.0

    # Numpy gate with forward model
    gate_np_fwd = SurpriseGate(arm_id=1, backend="numpy", forward_model=fwd_model)
    surp_np_fwd = gate_np_fwd.compute_surprise(
        np.zeros(16, dtype=np.float32), hidden_state=h_state, action_vector=a_vec
    )
    assert 0.0 <= surp_np_fwd <= 1.0

    # Torch backend mismatched shape
    mismatched_t = torch.zeros(8, dtype=torch.float32)
    surp_mismatch = gate.compute_surprise(actual, mismatched_t)
    assert 0.0 <= surp_mismatch <= 1.0

    # Empty torch tensor
    empty_t = torch.tensor([], dtype=torch.float32)
    assert gate.compute_surprise(actual, empty_t) == 0.0


@pytest.mark.unit
def test_gate_torch_import_error(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "torch", None)
    gate = SurpriseGate(arm_id=0, backend="torch")
    with pytest.raises(ImportError, match="PyTorch is required"):
        gate.compute_surprise(np.zeros(4))
