"""Event-Triggered Sensory Surprise Gating System.

Implements the biological predictive coding check:
    ΔS_i = (1 / D) * ||o_t - ô_t||²

Decides whether an arm executes silently or escalates an alert to the central
conductor when sensory surprise exceeds the adaptive threshold θ.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from octoflow.tools import ToolResult
from octoflow.usage import estimate_tokens_from_chars


@dataclass
class GateDecision:
    """Individual record of an event-triggered sensory gate evaluation."""

    arm: int
    cycle: int
    dS: float
    theta: float
    decision: str  # "reflex" | "escalate"
    would_have_sent_tokens: int
    estimated: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": int(self.arm),
            "cycle": int(self.cycle),
            "dS": round(float(self.dS), 4),
            "theta": round(float(self.theta), 4),
            "decision": str(self.decision),
            "would_have_sent_tokens": int(self.would_have_sent_tokens),
            "estimated": bool(self.estimated),
            "timestamp": float(self.timestamp),
        }


class DecisionLedger:
    """Thread-safe ledger recording all gate evaluations and avoided token estimates."""

    def __init__(self) -> None:
        self.records: list[GateDecision] = []
        self._lock = threading.Lock()

    def record(
        self,
        arm: int,
        cycle: int,
        dS: float,
        theta: float,
        decision: str,
        would_have_sent_tokens: int,
        estimated: bool = True,
    ) -> GateDecision:
        rec = GateDecision(
            arm=int(arm),
            cycle=int(cycle),
            dS=float(dS),
            theta=float(theta),
            decision=str(decision),
            would_have_sent_tokens=max(0, int(would_have_sent_tokens)),
            estimated=bool(estimated),
        )
        with self._lock:
            self.records.append(rec)
        return rec

    @property
    def total_evaluations(self) -> int:
        with self._lock:
            return len(self.records)

    @property
    def total_reflexes(self) -> int:
        with self._lock:
            return sum(1 for r in self.records if r.decision == "reflex")

    @property
    def total_escalations(self) -> int:
        with self._lock:
            return sum(1 for r in self.records if r.decision == "escalate")

    @property
    def avoided_tokens_estimated(self) -> int:
        with self._lock:
            return sum(r.would_have_sent_tokens for r in self.records if r.decision == "reflex")

    def to_list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in self.records]

    def reset(self) -> None:
        with self._lock:
            self.records.clear()


class SurpriseGate:
    """Computes sensory surprise and enforces event-triggered silent execution."""

    def __init__(
        self,
        arm_id: int,
        obs_dim: int = 16,
        initial_threshold: float = 0.50,
        adaptation_rate: float = 0.05,
        forward_model: Any | None = None,
        backend: str = "numpy",
        gate_mode: str = "gated",
    ):
        self.arm_id = arm_id
        self.obs_dim = obs_dim
        self.threshold = float(initial_threshold)
        self.adaptation_rate = adaptation_rate
        self.forward_model = forward_model
        self.backend = backend.strip().lower() if isinstance(backend, str) else "numpy"
        self.gate_mode = (
            "always_escalate"
            if str(gate_mode).strip().lower() in ("always_escalate", "ungated")
            else "gated"
        )

        self.total_steps = 0
        self.escalation_count = 0
        self.silent_steps = 0
        self.surprise_history: list[float] = []
        self.decisions: list[GateDecision] = []
        self.decision_ledger: DecisionLedger | None = None

    def compute_surprise(
        self,
        actual_obs: Any | np.ndarray,
        expected_obs: Any | np.ndarray | None = None,
        hidden_state: Any | None = None,
        action_vector: Any | None = None,
    ) -> float:
        """Compute the scalar sensory surprise ΔS_i = (1/D) * ||o_t - ô_t||²."""
        if self.backend == "torch":
            try:
                import torch
            except ImportError as err:
                raise ImportError(
                    "PyTorch is required when gate backend='torch'. Install with: pip install 'octoflow[ml]'"
                ) from err
            if isinstance(actual_obs, np.ndarray):
                actual_t = torch.tensor(actual_obs, dtype=torch.float32)
            else:
                actual_t = actual_obs.detach().cpu()

            # Corrupted / NaN / Inf inputs must trigger maximum sensory surprise
            if torch.isnan(actual_t).any() or torch.isinf(actual_t).any():
                return 1.0

            if (
                self.forward_model is not None
                and hidden_state is not None
                and action_vector is not None
            ):
                with torch.no_grad():
                    fwd_in = torch.cat([hidden_state, action_vector], dim=-1)
                    predicted_t = self.forward_model(fwd_in).squeeze()
            elif expected_obs is not None:
                if isinstance(expected_obs, np.ndarray):
                    predicted_t = torch.tensor(expected_obs, dtype=torch.float32)
                else:
                    predicted_t = expected_obs.detach().cpu()
            else:
                baseline = torch.zeros(self.obs_dim, dtype=torch.float32)
                if self.obs_dim > 0:
                    baseline[-1] = 1.0
                predicted_t = baseline

            if actual_t.shape != predicted_t.shape:
                min_dim = min(actual_t.numel(), predicted_t.numel())
                if min_dim == 0:
                    return 0.0
                actual_t = actual_t.view(-1)[:min_dim]
                predicted_t = predicted_t.view(-1)[:min_dim]

            diff = actual_t - predicted_t
            surprise = float(torch.mean(diff**2).item())
            return float(max(0.0, min(1.0, surprise * 4.0)))

        # NumPy path (default, lightweight)
        if hasattr(actual_obs, "detach"):
            actual_arr = actual_obs.detach().cpu().numpy().astype(np.float32)
        else:
            actual_arr = np.asarray(actual_obs, dtype=np.float32)

        # Corrupted / NaN / Inf inputs must trigger maximum sensory surprise (never silent false-negative)
        if np.isnan(actual_arr).any() or np.isinf(actual_arr).any():
            return 1.0

        # If forward model is provided, compute predicted observation ô_t from (h_t, action)
        if (
            self.forward_model is not None
            and hidden_state is not None
            and action_vector is not None
        ):
            import torch

            with torch.no_grad():
                fwd_in = torch.cat([hidden_state, action_vector], dim=-1)
                predicted_t = self.forward_model(fwd_in).squeeze()
                predicted_arr = predicted_t.detach().cpu().numpy().astype(np.float32)
        elif expected_obs is not None:
            if hasattr(expected_obs, "detach"):
                predicted_arr = expected_obs.detach().cpu().numpy().astype(np.float32)
            else:
                predicted_arr = np.asarray(expected_obs, dtype=np.float32)
        else:
            # Analytical baseline expectation: clean execution (exit code 0, no stderr, quiescence=1.0)
            baseline_arr = np.zeros(self.obs_dim, dtype=np.float32)
            if self.obs_dim > 0:
                baseline_arr[-1] = 1.0  # Quiescence expected on last dimension
            predicted_arr = baseline_arr

        # Handle empty observations
        if actual_arr.size == 0 or predicted_arr.size == 0:
            return 0.0

        # Ensure matching array shapes across varying dimensions
        if actual_arr.shape != predicted_arr.shape:
            min_dim = min(actual_arr.size, predicted_arr.size)
            actual_arr = actual_arr.reshape(-1)[:min_dim]
            predicted_arr = predicted_arr.reshape(-1)[:min_dim]

        # Mean squared sensory prediction error across D dimensions
        diff = actual_arr - predicted_arr
        surprise = float(np.mean(diff**2))

        # Scale surprise into [0.0, 1.0] range
        surprise_norm = float(np.clip(surprise * 4.0, 0.0, 1.0))
        return surprise_norm

    def evaluate(
        self,
        actual_obs: Any | np.ndarray,
        tool_result: ToolResult,
        expected_obs: Any | np.ndarray | None = None,
        cycle: int | None = None,
        prompt: str | None = None,
        would_have_sent_tokens: int | None = None,
    ) -> tuple[bool, float, dict[str, Any]]:
        """Evaluate whether to escalate or remain silent.

        Returns:
            should_escalate: True if ΔS_i > θ, False for silent execution.
            surprise: The computed scalar sensory surprise.
            telemetry: Dictionary containing surprise, threshold, and savings rate.
        """
        self.total_steps += 1
        surprise = self.compute_surprise(actual_obs, expected_obs)
        self.surprise_history.append(surprise)

        # Invariant checks: explicit non-zero returncode or crash guarantees surprise elevation
        if tool_result.returncode != 0 or not tool_result.success:
            # Ensure significant surprise for fatal tool crashes
            surprise = max(surprise, 0.65)

        if self.gate_mode == "always_escalate":
            should_escalate = True
        else:
            should_escalate = surprise > self.threshold

        cur_cycle = int(cycle) if cycle is not None else self.total_steps
        current_threshold = self.threshold

        if should_escalate:
            decision = "escalate"
            self.escalation_count += 1
            # Slightly raise threshold to prevent infinite panic loops
            self.threshold = min(0.90, self.threshold + self.adaptation_rate * 0.5)
            avoided = 0
        else:
            decision = "reflex"
            self.silent_steps += 1
            # Slowly decay threshold back towards baseline
            self.threshold = max(0.25, self.threshold - self.adaptation_rate * 0.1)
            if would_have_sent_tokens is not None:
                avoided = max(0, int(would_have_sent_tokens))
            elif prompt:
                avoided = estimate_tokens_from_chars(prompt)
            else:
                avoided = 0

        dec_record = GateDecision(
            arm=self.arm_id,
            cycle=cur_cycle,
            dS=surprise,
            theta=current_threshold,
            decision=decision,
            would_have_sent_tokens=avoided,
            estimated=True,
        )
        self.decisions.append(dec_record)
        if self.decision_ledger is not None:
            self.decision_ledger.record(
                arm=self.arm_id,
                cycle=cur_cycle,
                dS=surprise,
                theta=current_threshold,
                decision=decision,
                would_have_sent_tokens=avoided,
                estimated=True,
            )

        try:
            from octoflow.trace import get_active_tracer

            tracer = get_active_tracer()
            if tracer and tracer.enabled:
                tracer.log_gate_eval(
                    arm_id=self.arm_id,
                    cycle=cur_cycle,
                    surprise=surprise,
                    threshold=current_threshold,
                    decision=decision,
                    tokens_avoided=avoided,
                )
        except Exception:
            pass

        savings_pct = (self.silent_steps / max(1, self.total_steps)) * 100.0

        telemetry = {
            "arm_id": float(self.arm_id),
            "surprise": surprise,
            "threshold": self.threshold,
            "should_escalate": 1.0 if should_escalate else 0.0,
            "silent_steps": float(self.silent_steps),
            "escalations": float(self.escalation_count),
            "savings_pct": savings_pct,
            "gate_mode": self.gate_mode,
            "decision": decision,
            "would_have_sent_tokens": avoided,
            "cycle": cur_cycle,
        }

        return should_escalate, surprise, telemetry

    @staticmethod
    def compute_generation_parameters(surprise: float) -> tuple[float, float]:
        """Modulate LLM generation temperature & top_p based on biophysical surprise.

        Low surprise (< 0.3) -> deterministic, grounded generation (temperature ~0.15 - 0.25).
        High surprise (> 0.6) -> creative exploration and alternative hypotheses (temperature up to 0.75).
        """
        temp = float(np.clip(0.18 + surprise * 0.55, 0.10, 0.85))
        top_p = float(np.clip(1.0 - surprise * 0.25, 0.70, 1.0))
        return temp, top_p
