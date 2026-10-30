"""RunBudget and BudgetTracker for centralized resource limits enforcement.

Tracks and enforces:
- max_tokens: hard limit on total LLM tokens (default: 200_000)
- max_llm_calls: hard limit on total LLM completions (default: 200)
- max_wall_seconds: hard limit on wall clock duration (default: 1800s)
- max_heal_iterations: hard limit on test healing loops (default: 5)
- max_files_written: hard limit on files written into workspace (default: 200)
- no_limits: explicit opt-out for unrestricted execution
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from octoflow.errors import BudgetExceeded


def format_k(n: int | None) -> str:
    """Format token/call integers into readable shorthand (e.g. 41k, 200k, 1.2M)."""
    if n is None:
        return "unlimited"
    if n >= 1_000_000:
        val = n / 1_000_000
        return f"{val:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        val = n / 1_000
        # If whole thousands (e.g. 41000 -> 41k, 200000 -> 200k)
        if val == int(val):
            return f"{int(val)}k"
        return f"{val:.1f}k".replace(".0k", "k")
    return str(n)


def format_hud_line(tracker: BudgetTracker) -> str:
    """Format single-line budget status string for HUD / outcome ribbon."""
    return tracker.format_hud_line()


class RunBudget(BaseModel):
    """Enforceable resource limits for an autonomous swarm run."""

    max_tokens: int | None = Field(
        default=200_000, description="Max total tokens consumed across all LLM calls"
    )
    max_llm_calls: int | None = Field(default=200, description="Max total LLM completions allowed")
    max_wall_seconds: int | None = Field(
        default=1800, description="Max execution wall time in seconds"
    )
    max_heal_iterations: int | None = Field(
        default=5, description="Max test repair self-healing iterations"
    )
    max_files_written: int | None = Field(
        default=200, description="Max unique files written into workspace"
    )
    no_limits: bool = Field(default=False, description="Disable all budget limits explicitly")


class BudgetTracker:
    """Thread-safe resource monitor enforcing RunBudget limits at critical choke points."""

    def __init__(
        self,
        budget: RunBudget | None = None,
        clock: Callable[[], float] | None = None,
        tokens_consumed: int = 0,
        llm_calls_made: int = 0,
    ) -> None:
        self.budget = budget or RunBudget()
        self.clock = clock or time.time
        self.start_time: float = self.clock()

        self.tokens_used: int = tokens_consumed
        self.llm_calls: int = llm_calls_made
        self.files_written: int = 0
        self.files_written_set: set[str] = set()
        self.heal_iterations: int = 0

        self._lock = threading.Lock()

    @property
    def tokens_consumed(self) -> int:
        return self.tokens_used

    @tokens_consumed.setter
    def tokens_consumed(self, val: int) -> None:
        self.tokens_used = val

    @property
    def llm_calls_made(self) -> int:
        return self.llm_calls

    @llm_calls_made.setter
    def llm_calls_made(self, val: int) -> None:
        self.llm_calls = val

    def elapsed_seconds(self) -> float:
        """Return total elapsed wall time according to the injected clock."""
        return max(0.0, self.clock() - self.start_time)

    def check_wall_time(self) -> None:
        """Check wall clock limit and raise BudgetExceeded if exceeded."""
        if self.budget.no_limits:
            return
        if self.budget.max_wall_seconds is not None:
            elapsed = self.elapsed_seconds()
            if elapsed > self.budget.max_wall_seconds:
                raise BudgetExceeded(
                    limit_name="max_wall_seconds",
                    used=int(elapsed),
                    limit=self.budget.max_wall_seconds,
                    message=f"Wall-time limit exceeded: {int(elapsed)}s elapsed (limit {self.budget.max_wall_seconds}s).",
                )

    def check_llm_call(self) -> None:
        """Check budget constraints before making an LLM completion call.

        Increments call counter if allowed, or raises BudgetExceeded.
        """
        with self._lock:
            if not self.budget.no_limits:
                # 1. Wall time check
                if self.budget.max_wall_seconds is not None:
                    elapsed = self.elapsed_seconds()
                    if elapsed > self.budget.max_wall_seconds:
                        raise BudgetExceeded(
                            limit_name="max_wall_seconds",
                            used=int(elapsed),
                            limit=self.budget.max_wall_seconds,
                            message=f"Wall-time limit exceeded: {int(elapsed)}s elapsed (limit {self.budget.max_wall_seconds}s).",
                        )

                # 2. Call count check
                if (
                    self.budget.max_llm_calls is not None
                    and self.llm_calls >= self.budget.max_llm_calls
                ):
                    raise BudgetExceeded(
                        limit_name="max_llm_calls",
                        used=self.llm_calls,
                        limit=self.budget.max_llm_calls,
                        message=f"LLM call limit reached: {self.llm_calls}/{self.budget.max_llm_calls} calls.",
                    )

                # 3. Token limit check
                if (
                    self.budget.max_tokens is not None
                    and self.tokens_used >= self.budget.max_tokens
                ):
                    raise BudgetExceeded(
                        limit_name="max_tokens",
                        used=self.tokens_used,
                        limit=self.budget.max_tokens,
                        message=f"Token budget exceeded: {self.tokens_used}/{self.budget.max_tokens} tokens.",
                    )

            self.llm_calls += 1

    def record_tokens(self, tokens: int) -> None:
        """Accumulate token consumption and check against max_tokens limit."""
        if tokens <= 0:
            return
        with self._lock:
            self.tokens_used += tokens
            if not self.budget.no_limits and self.budget.max_tokens is not None:
                if self.tokens_used > self.budget.max_tokens:
                    raise BudgetExceeded(
                        limit_name="max_tokens",
                        used=self.tokens_used,
                        limit=self.budget.max_tokens,
                        message=f"Token budget exceeded: {self.tokens_used}/{self.budget.max_tokens} tokens.",
                    )

    def check_and_record_file_write(self, path: str) -> None:
        """Check file write limit before saving to workspace and record path."""
        with self._lock:
            if not self.budget.no_limits:
                # Wall time check
                if self.budget.max_wall_seconds is not None:
                    elapsed = self.elapsed_seconds()
                    if elapsed > self.budget.max_wall_seconds:
                        raise BudgetExceeded(
                            limit_name="max_wall_seconds",
                            used=int(elapsed),
                            limit=self.budget.max_wall_seconds,
                            message=f"Wall-time limit exceeded: {int(elapsed)}s elapsed (limit {self.budget.max_wall_seconds}s).",
                        )

                # Unique files written check
                if self.budget.max_files_written is not None:
                    if (
                        path not in self.files_written_set
                        and len(self.files_written_set) >= self.budget.max_files_written
                    ):
                        raise BudgetExceeded(
                            limit_name="max_files_written",
                            used=len(self.files_written_set),
                            limit=self.budget.max_files_written,
                            message=f"Files written limit reached: {len(self.files_written_set)}/{self.budget.max_files_written} files.",
                        )

            self.files_written_set.add(path)
            self.files_written = len(self.files_written_set)

    def check_heal_iteration(self) -> None:
        """Check healing loop budget before starting a repair iteration."""
        with self._lock:
            if not self.budget.no_limits:
                if (
                    self.budget.max_heal_iterations is not None
                    and self.heal_iterations >= self.budget.max_heal_iterations
                ):
                    raise BudgetExceeded(
                        limit_name="max_heal_iterations",
                        used=self.heal_iterations,
                        limit=self.budget.max_heal_iterations,
                        message=f"Max healing iterations reached: {self.heal_iterations}/{self.budget.max_heal_iterations}.",
                    )
            self.heal_iterations += 1

    def format_hud_line(self) -> str:
        """Return single-line budget status string for HUD / outcome ribbon.

        Example format:
        budget: tokens 41k/200k, calls 33/200
        """
        with self._lock:
            if self.budget.no_limits:
                tok_limit = "unlimited"
                call_limit = "unlimited"
                suffix = " (no limits)"
            else:
                tok_limit = format_k(self.budget.max_tokens)
                call_limit = (
                    str(self.budget.max_llm_calls)
                    if self.budget.max_llm_calls is not None
                    else "unlimited"
                )
                suffix = ""

            tok_used = format_k(self.tokens_used)
            return f"budget: tokens {tok_used}/{tok_limit}, calls {self.llm_calls}/{call_limit}{suffix}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize budget tracker statistics."""
        with self._lock:
            return {
                "tokens_used": self.tokens_used,
                "llm_calls": self.llm_calls,
                "files_written": self.files_written,
                "heal_iterations": self.heal_iterations,
                "elapsed_seconds": self.elapsed_seconds(),
                "budget": self.budget.model_dump(),
                "budget_line": self.format_hud_line(),
            }
