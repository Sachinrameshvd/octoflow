"""CodeSensoryEncoder: Neural-Symbolic Sensory Observation Encoder.

Maps discrete software and ML execution signals (exit codes, stderr stack traces,
git diff deltas, execution latency, and error types) into continuous 16-dimensional
sensory observation vectors for the cephalopod forward-model predictive network.
"""

from __future__ import annotations

import math
import os
from typing import Any, Protocol, runtime_checkable

import numpy as np

from octoflow.tools import ToolResult


@runtime_checkable
class SensoryEncoder(Protocol):
    """Protocol for sensory observation encoders."""

    obs_dim: int
    backend: str

    def encode(
        self,
        result: ToolResult,
        step: int = 0,
        max_steps: int = 15,
        as_tensor: bool | None = None,
        device: Any | None = None,
    ) -> np.ndarray | Any: ...


class CodeSensoryEncoder:
    """Encodes tool execution outcomes into continuous biophysical sensory observations."""

    def __init__(self, obs_dim: int = 16, backend: str = "numpy"):
        self.obs_dim = obs_dim
        self.backend = backend.strip().lower() if isinstance(backend, str) else "numpy"

        # Common error signature keywords for semantic feature extraction
        self.syntax_keywords = ["syntaxerror", "indentationerror", "parseerror", "unexpected token"]
        self.oom_keywords = ["outofmemory", "cuda out of memory", "oom", "memoryerror"]
        self.test_keywords = ["failed", "assertionerror", "test failed", "failures=", "errors="]
        self.missing_keywords = [
            "filenotfounderror",
            "modulenotfounderror",
            "no such file",
            "importerror",
        ]
        self.type_keywords = ["typeerror", "valueerror", "validationerror", "attributeerror"]

    def encode(
        self,
        result: ToolResult,
        step: int = 0,
        max_steps: int = 15,
        as_tensor: bool | None = None,
        device: Any | None = None,
    ) -> np.ndarray | Any:
        """Convert a ToolResult into a normalized sensory observation vector of shape (obs_dim,).

        Feature Layout (16 dimensions):
            0: Normalized exit code (0.0 for clean 0, 1.0 for non-zero)
            1: Stderr presence indicator (0.0 or 1.0)
            2: Log-scaled stderr length: log(1 + len) / 10.0
            3: Log-scaled stdout length: log(1 + len) / 10.0
            4: Normalized lines written / diff delta: min(1.0, lines / 100.0)
            5: Normalized execution time: min(1.0, ms / 10000.0)
            6: Syntax / parser error indicator (0.0 or 1.0)
            7: CUDA / Memory OOM error indicator (0.0 or 1.0)
            8: Test failure / assertion error indicator (0.0 or 1.0)
            9: Missing file or module import error (0.0 or 1.0)
            10: Type / Schema / Validation error (0.0 or 1.0)
            11: Tool category ID: read(0.2), write(0.4), run(0.6), list(0.8)
            12: Step progress fraction: min(1.0, step / max_steps)
            13: Lock conflict / contention flag (0.0 or 1.0)
            14: Timeout expired flag (0.0 or 1.0)
            15: Quiescence / clean success indicator (1.0 if clean exit and no stderr, else 0.0)
        """
        features = np.zeros(self.obs_dim, dtype=np.float32)

        stderr_lower = result.stderr.lower()
        stdout_lower = result.stdout.lower()

        # Feature 0: Exit code
        features[0] = 0.0 if result.returncode == 0 else min(1.0, abs(result.returncode) / 128.0)

        # Feature 1 & 2: Stderr
        stderr_len = len(result.stderr)
        features[1] = 1.0 if stderr_len > 0 else 0.0
        features[2] = min(1.0, math.log1p(stderr_len) / 10.0)

        # Feature 3: Stdout
        stdout_len = len(result.stdout)
        features[3] = min(1.0, math.log1p(stdout_len) / 10.0)

        # Feature 4: Diff lines
        features[4] = min(1.0, result.diff_lines / 100.0)

        # Feature 5: Latency
        features[5] = min(1.0, result.execution_time_ms / 10000.0)

        # Feature 6-10: Semantic Error Classification
        combined_text = f"{stderr_lower} {stdout_lower}"
        features[6] = 1.0 if any(k in combined_text for k in self.syntax_keywords) else 0.0
        features[7] = 1.0 if any(k in combined_text for k in self.oom_keywords) else 0.0
        features[8] = 1.0 if any(k in combined_text for k in self.test_keywords) else 0.0
        features[9] = 1.0 if any(k in combined_text for k in self.missing_keywords) else 0.0
        features[10] = 1.0 if any(k in combined_text for k in self.type_keywords) else 0.0

        # Feature 11: Tool category
        tool_map = {"read_file": 0.2, "write_file": 0.4, "run_command": 0.6, "list_dir": 0.8}
        features[11] = tool_map.get(result.tool_name, 0.5)

        # Feature 12: Progress fraction
        features[12] = min(1.0, max(0.0, step / max(1, max_steps)))

        # Feature 13: Lock conflict
        features[13] = 1.0 if "filelockerror" in stderr_lower else 0.0

        # Feature 14: Timeout
        features[14] = 1.0 if "timeoutexpired" in stderr_lower or result.returncode == 124 else 0.0

        # Feature 15: Quiescence / clean success
        is_clean = result.returncode == 0 and stderr_len == 0 and result.success
        features[15] = 1.0 if is_clean else 0.0

        return_tensor = (self.backend == "torch") if as_tensor is None else bool(as_tensor)
        if return_tensor:
            try:
                import torch
            except ImportError as err:
                raise ImportError(
                    "PyTorch is required when as_tensor=True or backend='torch'. "
                    "Install with: pip install 'octoflow[ml]'"
                ) from err
            t = torch.tensor(features, dtype=torch.float32)
            if device:
                t = t.to(device)
            return t
        return features


def _is_torch_available() -> bool:
    """Check if torch is importable without eagerly importing it."""
    try:
        import importlib.util

        return importlib.util.find_spec("torch") is not None
    except Exception:
        try:
            import torch  # noqa: F401

            return True
        except ImportError:
            return False


def _get_configured_backend() -> str:
    """Consult env vars and settings for user-configured encoder backend."""
    env_backend = os.environ.get("OCTOFLOW_ENCODER_BACKEND") or os.environ.get("ENCODER_BACKEND")
    if env_backend:
        return env_backend.strip().lower()
    try:
        from octoflow.settings import load_settings

        settings = load_settings()
        return settings.defaults.encoder_backend.strip().lower()
    except Exception:
        return "numpy"


def get_encoder(backend: str = "auto", obs_dim: int = 16) -> CodeSensoryEncoder:
    """Factory function returning a configured sensory encoder.

    Parameters:
        backend: "auto" | "numpy" | "torch"
            - "auto": picks torch only if torch is importable AND the user explicitly
              set encoder_backend="torch" in configuration or environment; the default is NumPy.
            - "numpy": uses the NumPy-native encoder path without importing ML frameworks.
            - "torch": explicitly requests the PyTorch backend; raises ImportError if not installed.
        obs_dim: observation vector dimensionality (default: 16).

    Returns:
        CodeSensoryEncoder instance configured with the resolved backend.
    """
    b = backend.strip().lower()
    if b == "auto":
        configured = _get_configured_backend()
        if configured == "torch" and _is_torch_available():
            selected = "torch"
        else:
            selected = "numpy"
    elif b == "torch":
        if not _is_torch_available():
            raise ImportError(
                "PyTorch is required for backend='torch'. Install with: pip install 'octoflow[ml]'"
            )
        selected = "torch"
    elif b == "numpy":
        selected = "numpy"
    else:
        raise ValueError(
            f"Unknown backend '{backend}'. Supported backends: 'auto', 'numpy', 'torch'."
        )

    return CodeSensoryEncoder(obs_dim=obs_dim, backend=selected)
