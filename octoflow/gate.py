"""Event-Triggered Sensory Surprise Gating System.

Implements the biological predictive coding check:
    ΔS_i = (1 / D) * ||o_t - ô_t||²

Decides whether an arm executes silently or escalates an alert to the central
conductor when sensory surprise exceeds the adaptive threshold θ.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np

from octoflow.tools import ToolResult


class SurpriseGate:
    """Computes sensory surprise and enforces event-triggered silent execution."""

    def __init__(
        self,
        arm_id: int,
        obs_dim: int = 16,
        initial_threshold: float = 0.50,
        adaptation_rate: float = 0.05,
        forward_model: Optional[Any] = None,
        backend: str = "numpy",
    ):
        self.arm_id = arm_id
        self.obs_dim = obs_dim
        self.threshold = float(initial_threshold)
        self.adaptation_rate = adaptation_rate
        self.forward_model = forward_model
        self.backend = backend.strip().lower() if isinstance(backend, str) else "numpy"

        # Running statistics
        self.total_steps = 0
        self.escalation_count = 0
        self.silent_steps = 0
        self.surprise_history: list = []

    def compute_surprise(
        self,
        actual_obs: Union[Any, np.ndarray],
        expected_obs: Optional[Union[Any, np.ndarray]] = None,
        hidden_state: Optional[Any] = None,
        action_vector: Optional[Any] = None,
    ) -> float:
        """Compute the scalar sensory surprise ΔS_i = (1/D) * ||o_t - ô_t||²."""
        if self.backend == "torch":
            try:
                import torch
            except ImportError:
                raise ImportError(
                    "PyTorch is required when gate backend='torch'. Install with: pip install 'octoflow[ml]'"
                )
            if isinstance(actual_obs, np.ndarray):
                actual_t = torch.tensor(actual_obs, dtype=torch.float32)
            else:
                actual_t = actual_obs.detach().cpu()

            # Corrupted / NaN / Inf inputs must trigger maximum sensory surprise
            if torch.isnan(actual_t).any() or torch.isinf(actual_t).any():
                return 1.0

            if self.forward_model is not None and hidden_state is not None and action_vector is not None:
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
            surprise = float(torch.mean(diff ** 2).item())
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
        if self.forward_model is not None and hidden_state is not None and action_vector is not None:
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
            baseline = np.zeros(self.obs_dim, dtype=np.float32)
            if self.obs_dim > 0:
                baseline[-1] = 1.0  # Quiescence expected on last dimension
            predicted_arr = baseline

        # Ensure matching array shapes across varying dimensions
        if actual_arr.shape != predicted_arr.shape:
            min_dim = min(actual_arr.size, predicted_arr.size)
            if min_dim == 0:
                return 0.0
            actual_arr = actual_arr.reshape(-1)[:min_dim]
            predicted_arr = predicted_arr.reshape(-1)[:min_dim]

        # Mean squared sensory prediction error across D dimensions
        diff = actual_arr - predicted_arr
        surprise = float(np.mean(diff ** 2))

        # Scale surprise into [0.0, 1.0] range
        surprise_norm = float(np.clip(surprise * 4.0, 0.0, 1.0))
        return surprise_norm

    def evaluate(
        self,
        actual_obs: Union[Any, np.ndarray],
        tool_result: ToolResult,
        expected_obs: Optional[Union[Any, np.ndarray]] = None,
    ) -> Tuple[bool, float, Dict[str, float]]:
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

        should_escalate = (surprise > self.threshold)

        if should_escalate:
            self.escalation_count += 1
            # Slightly raise threshold to prevent infinite panic loops
            self.threshold = min(0.90, self.threshold + self.adaptation_rate * 0.5)
        else:
            self.silent_steps += 1
            # Slowly decay threshold back towards baseline
            self.threshold = max(0.25, self.threshold - self.adaptation_rate * 0.1)

        savings_pct = (self.silent_steps / max(1, self.total_steps)) * 100.0

        telemetry = {
            "arm_id": float(self.arm_id),
            "surprise": surprise,
            "threshold": self.threshold,
            "should_escalate": 1.0 if should_escalate else 0.0,
            "silent_steps": float(self.silent_steps),
            "escalations": float(self.escalation_count),
            "savings_pct": savings_pct,
        }

        return should_escalate, surprise, telemetry

    @staticmethod
    def compute_generation_parameters(surprise: float) -> Tuple[float, float]:
        """Modulate LLM generation temperature & top_p based on biophysical surprise.

        Low surprise (< 0.3) -> deterministic, grounded generation (temperature ~0.15 - 0.25).
        High surprise (> 0.6) -> creative exploration and alternative hypotheses (temperature up to 0.75).
        """
        temp = float(np.clip(0.18 + surprise * 0.55, 0.10, 0.85))
        top_p = float(np.clip(1.0 - surprise * 0.25, 0.70, 1.0))
        return temp, top_p
