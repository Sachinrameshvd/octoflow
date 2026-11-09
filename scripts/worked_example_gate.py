#!/usr/bin/env python3
"""Worked example script demonstrating Event-Triggered Sensory Surprise Gate Math.

Referenced in docs/architecture.md (Section 9).
Reproduces the exact observation encoding, mean squared prediction error,
scalar sensory surprise scaling, threshold adaptation, and reflex vs. escalate decisions.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure current workspace is prioritized over ambient installed packages
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
from octoflow.encoder import CodeSensoryEncoder  # noqa: E402
from octoflow.gate import SurpriseGate  # noqa: E402
from octoflow.tools import ToolResult  # noqa: E402


def main() -> None:
    encoder = CodeSensoryEncoder(obs_dim=16, backend="numpy")
    gate = SurpriseGate(arm_id=2, obs_dim=16, initial_threshold=0.50, adaptation_rate=0.05)

    # -------------------------------------------------------------------------
    # Scenario A: Routine successful file write (Reflex Loop)
    # -------------------------------------------------------------------------
    res_routine = ToolResult(
        tool_name="write_file",
        target="limiter.py",
        success=True,
        returncode=0,
        stdout="Wrote 42 bytes to limiter.py",
        stderr="",
        diff_lines=15,
        execution_time_ms=18.0,
    )
    obs_routine = encoder.encode(res_routine, step=1, max_steps=10)

    # Expected observation: normal clean execution expectation
    expected_routine = np.zeros(16, dtype=np.float32)
    expected_routine[11] = 0.4  # tool category: write_file
    expected_routine[15] = 1.0  # quiescence / clean success indicator

    escalate_a, dS_a, telem_a = gate.evaluate(
        actual_obs=obs_routine,
        tool_result=res_routine,
        expected_obs=expected_routine,
        cycle=1,
        would_have_sent_tokens=240,
    )

    diff_sq_a = (obs_routine - expected_routine) ** 2
    raw_mse_a = float(np.mean(diff_sq_a))

    print("=== SCENARIO A: ROUTINE WRITE (REFLEX) ===")
    print(f"Obs Dimension: {obs_routine.shape[0]}")
    print(f"Actual Obs Vector:   {[round(float(x), 4) for x in obs_routine]}")
    print(f"Expected Obs Vector: {[round(float(x), 4) for x in expected_routine]}")
    print(f"Raw MSE: {raw_mse_a:.6f}")
    print(f"Normalized Surprise (Delta S): {dS_a:.4f}")
    print(f"Threshold (theta) before: 0.5000, after: {gate.threshold:.4f}")
    print(f"Decision: {telem_a['decision'].upper()} (Escalate={escalate_a})")
    print(f"Tokens Avoided (estimated): {telem_a['would_have_sent_tokens']}")

    # -------------------------------------------------------------------------
    # Scenario B: Test assertion failure (Escalate to Central Conductor)
    # -------------------------------------------------------------------------
    res_failure = ToolResult(
        tool_name="run_command",
        target="pytest test_limiter.py",
        success=False,
        returncode=1,
        stdout="",
        stderr='AssertionError: assert False where False = allow_request("client_1")',
        diff_lines=0,
        execution_time_ms=120.0,
    )
    obs_failure = encoder.encode(res_failure, step=2, max_steps=10)
    expected_failure = expected_routine  # Conductor expected success

    escalate_b, dS_b, telem_b = gate.evaluate(
        actual_obs=obs_failure,
        tool_result=res_failure,
        expected_obs=expected_failure,
        cycle=2,
        would_have_sent_tokens=320,
    )

    diff_sq_b = (obs_failure - expected_failure) ** 2
    raw_mse_b = float(np.mean(diff_sq_b))

    print("\n=== SCENARIO B: TEST FAILURE (ESCALATE) ===")
    print(f"Actual Obs Vector:   {[round(float(x), 4) for x in obs_failure]}")
    print(f"Expected Obs Vector: {[round(float(x), 4) for x in expected_failure]}")
    print(f"Raw MSE: {raw_mse_b:.6f}")
    print(f"Normalized Surprise (Delta S): {dS_b:.4f}")
    print(f"Threshold (theta) before: {telem_a['threshold']:.4f}, after: {gate.threshold:.4f}")
    print(f"Decision: {telem_b['decision'].upper()} (Escalate={escalate_b})")
    print(f"Tokens Avoided (estimated): {telem_b['would_have_sent_tokens']}")


if __name__ == "__main__":
    main()
