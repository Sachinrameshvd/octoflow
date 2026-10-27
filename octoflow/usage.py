"""Token usage accounting and aggregation ledger for OctoFlow LLM providers.

Tracks prompt tokens, completion tokens, call counts, and whether token counts
were measured directly from provider API responses or estimated using character heuristics.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class UsageRecord:
    """Individual record of an LLM completion call and its token consumption."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated: bool
    provider: str = ""
    model: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UsageLedger:
    """Thread-safe ledger aggregating token usage and call statistics per run."""

    def __init__(self) -> None:
        self.records: List[UsageRecord] = []
        self._lock = threading.Lock()

    def record(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        estimated: bool,
        provider: str = "",
        model: str = "",
    ) -> UsageRecord:
        """Add a single LLM usage record to the ledger."""
        p_tok = max(0, int(prompt_tokens))
        c_tok = max(0, int(completion_tokens))
        rec = UsageRecord(
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=p_tok + c_tok,
            estimated=bool(estimated),
            provider=str(provider),
            model=str(model),
        )
        with self._lock:
            self.records.append(rec)
        return rec

    @property
    def total_calls(self) -> int:
        with self._lock:
            return len(self.records)

    @property
    def prompt_tokens(self) -> int:
        with self._lock:
            return sum(r.prompt_tokens for r in self.records)

    @property
    def completion_tokens(self) -> int:
        with self._lock:
            return sum(r.completion_tokens for r in self.records)

    @property
    def total_tokens(self) -> int:
        with self._lock:
            return sum(r.total_tokens for r in self.records)

    @property
    def is_estimated(self) -> bool:
        """True if any record in the ledger was estimated rather than measured directly."""
        with self._lock:
            return any(r.estimated for r in self.records)

    @property
    def measured_calls(self) -> int:
        with self._lock:
            return sum(1 for r in self.records if not r.estimated)

    @property
    def estimated_calls(self) -> int:
        with self._lock:
            return sum(1 for r in self.records if r.estimated)

    @property
    def measured_prompt_tokens(self) -> int:
        with self._lock:
            return sum(r.prompt_tokens for r in self.records if not r.estimated)

    @property
    def measured_completion_tokens(self) -> int:
        with self._lock:
            return sum(r.completion_tokens for r in self.records if not r.estimated)

    @property
    def estimated_prompt_tokens(self) -> int:
        with self._lock:
            return sum(r.prompt_tokens for r in self.records if r.estimated)

    @property
    def estimated_completion_tokens(self) -> int:
        with self._lock:
            return sum(r.completion_tokens for r in self.records if r.estimated)

    def summary(self) -> Dict[str, Any]:
        """Return aggregated usage summary dictionary."""
        with self._lock:
            calls = len(self.records)
            prompt = sum(r.prompt_tokens for r in self.records)
            comp = sum(r.completion_tokens for r in self.records)
            total = prompt + comp
            is_est = any(r.estimated for r in self.records)
            m_prompt = sum(r.prompt_tokens for r in self.records if not r.estimated)
            m_comp = sum(r.completion_tokens for r in self.records if not r.estimated)
            e_prompt = sum(r.prompt_tokens for r in self.records if r.estimated)
            e_comp = sum(r.completion_tokens for r in self.records if r.estimated)

        return {
            "total_calls": calls,
            "prompt_tokens": prompt,
            "completion_tokens": comp,
            "total_tokens": total,
            "is_estimated": is_est,
            "measured_calls": calls - sum(1 for r in self.records if r.estimated),
            "estimated_calls": sum(1 for r in self.records if r.estimated),
            "measured_prompt_tokens": m_prompt,
            "measured_completion_tokens": m_comp,
            "estimated_prompt_tokens": e_prompt,
            "estimated_completion_tokens": e_comp,
        }

    def reset(self) -> None:
        """Clear all records in the ledger."""
        with self._lock:
            self.records.clear()


def estimate_tokens_from_chars(text: str) -> int:
    """Standard character-based token estimator: ceil(len(text) / 4)."""
    if not text:
        return 0
    return math.ceil(len(text) / 4)
