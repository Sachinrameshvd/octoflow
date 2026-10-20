"""Truthful Run State & Outcome Models for OctoFlow."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RunMode(str, Enum):
    """Execution mode of the swarm."""
    LIVE = "live"
    DRY_RUN = "dry_run"


class RunOutcome(str, Enum):
    """Terminal state outcome of a swarm mission."""
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class OctoFlowError(Exception):
    """Base exception for all OctoFlow runtime errors."""
    pass


class ProviderExhaustedError(OctoFlowError):
    """Raised when all configured LLM providers fail in live mode."""

    def __init__(self, message: str, failures: Optional[List[Dict[str, Any]]] = None):
        self.failures = failures or []
        formatted_failures = []
        for f in self.failures:
            cls_name = f.get("error_class") or "ProviderError"
            prov = f.get("provider") or f.get("name") or "unknown"
            hint = f.get("hint") or ""
            reason = f.get("reason") or "Failed"
            entry = f"• [{prov}] {cls_name}: {reason}"
            if hint:
                entry += f" (Hint: {hint})"
            formatted_failures.append(entry)

        full_msg = message
        if formatted_failures and "\n• [" not in message:
            full_msg += "\n" + "\n".join(formatted_failures)
        super().__init__(full_msg)


@dataclass
class RunResult:
    """Standardized result of a swarm run."""
    mode: RunMode
    outcome: RunOutcome
    provider_used: str
    model: str
    files_written: List[str] = field(default_factory=list)
    tests_run: int = 0
    tests_passed: int = 0
    reason: Optional[str] = None
    tokens_consumed: int = 0
    total_cost_dollars: float = 0.0
    token_reduction_pct: float = 0.0
    execution_time_seconds: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            val = getattr(self, key)
            if isinstance(val, Enum):
                return val.value
            return val
        if key in self.extra:
            return self.extra[key]
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extra[key] = value

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key) or (key in self.extra)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

