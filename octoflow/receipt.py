"""Token receipt model, aggregators, benchmark linkage, and terminal renderers.

Provides honest, transparent accounting of:
1. Measured vs estimated token expenditure.
2. Estimated tokens avoided via event-triggered sensory surprise gating (reflex vs escalate).
3. Empirical benchmark baseline comparisons from real data in benchmarks/results/.
4. Per-arm token allocation and budget utilization.
"""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from octoflow.budget import BudgetTracker, RunBudget
from octoflow.checkpoint import get_runs_dir
from octoflow.gate import DecisionLedger
from octoflow.glyphs import glyph, is_ascii_mode, is_plain_mode, sanitize_text
from octoflow.logging_config import get_logger
from octoflow.usage import UsageLedger

logger = get_logger("receipt")

RECEIPT_METHOD_EXPLANATION = (
    "Token usage is collected from provider API responses or estimated using character heuristics (ceil(chars/4)). "
    "Avoided tokens are estimated as the prompt size that would have been dispatched to the central conductor for each gate evaluation classified as a local reflex."
)


# -----------------------------------------------------------------------------
# Pydantic Receipt Models
# -----------------------------------------------------------------------------


class ArmReceiptSummary(BaseModel):
    """Token consumption and gate evaluation breakdown for a single specialist arm."""

    arm_id: int
    role: str
    llm_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_total: int = 0
    reflexes: int = 0
    escalations: int = 0
    avoided_tokens_estimated: int = 0
    is_estimated: bool = False


class BudgetUsageReceipt(BaseModel):
    """Resource budget utilization metrics."""

    max_tokens: int | None = None
    tokens_used: int = 0
    tokens_pct: float | None = None
    max_llm_calls: int | None = None
    calls_used: int = 0
    calls_pct: float | None = None
    max_wall_seconds: int | None = None
    wall_seconds_used: float = 0.0
    wall_pct: float | None = None


class BaselineComparison(BaseModel):
    """Empirical baseline comparison against recorded benchmark results."""

    task: str
    gated_tokens_median: int
    ungated_tokens_median: int
    run_count: int
    model: str
    label: str  # e.g. "measured in benchmark: gated X vs ungated Y (median of N runs, model M)"


class TokenReceipt(BaseModel):
    """Canonical truthful token receipt for an OctoFlow run."""

    run_id: str
    mode: str = "software_dev"
    provider: str = "mock"
    model: str = "default"
    duration_seconds: float = 0.0
    dry_run: bool = False

    # Totals
    llm_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_total: int = 0
    tokens_in_measured: int = 0
    tokens_in_estimated: int = 0
    tokens_out_measured: int = 0
    tokens_out_estimated: int = 0
    tokens_measured: int = 0
    tokens_estimated: int = 0

    # Gate Totals
    gate_evaluations: int = 0
    reflexes: int = 0
    escalations: int = 0
    avoided_tokens_estimated: int = 0

    # Breakdowns
    per_arm: list[ArmReceiptSummary] = Field(default_factory=list)
    budget_usage: BudgetUsageReceipt = Field(default_factory=BudgetUsageReceipt)
    baseline_comparison: BaselineComparison | None = None

    # Methodology & Confidence Note
    method: str = Field(default=RECEIPT_METHOD_EXPLANATION)
    confidence: str = "estimated"  # "measured" if all numbers are provider-measured, else "estimated"


# -----------------------------------------------------------------------------
# Benchmark Baseline Lookup
# -----------------------------------------------------------------------------


def find_benchmark_baseline(
    task_or_objective: str, results_dir: Path | str | None = None
) -> BaselineComparison | None:
    """Find matching benchmark runs in benchmarks/results/ and compute median baseline.

    Format strictly enforced:
    'measured in benchmark: gated X vs ungated Y (median of N runs, model M)'
    Never returns a generic percentage.
    """
    if not task_or_objective:
        return None

    obj_lower = task_or_objective.lower().replace("-", "_").replace(" ", "_")

    # Canonical benchmark tasks supported by real evaluation datasets
    known_tasks = [
        ("lru_cache", ["lru", "lru_cache", "cache"]),
        ("rate_limiter", ["rate_limiter", "limiter", "sliding_window"]),
        ("jwt_validator", ["jwt", "jwt_validator", "auth_token"]),
        ("dag_topo_sort", ["dag", "topo", "dag_topo_sort", "topological"]),
        ("fastapi_todo", ["fastapi", "todo", "fastapi_todo"]),
    ]

    matched_task = None
    for task_id, aliases in known_tasks:
        if task_id in obj_lower or any(alias in obj_lower for alias in aliases):
            matched_task = task_id
            break

    if not matched_task:
        return None

    if results_dir is not None:
        b_dir = Path(results_dir).resolve()
    else:
        # Search relative to repo root
        cur = Path(__file__).resolve().parent.parent / "benchmarks" / "results"
        if cur.exists():
            b_dir = cur
        else:
            return None

    if not b_dir.exists():
        return None

    # Collect gated and ungated (always_escalate) runs
    gated_files = sorted(b_dir.glob(f"{matched_task}_gated_run_*.json"))
    ungated_files = sorted(b_dir.glob(f"{matched_task}_always_escalate_run_*.json"))

    if not gated_files or not ungated_files:
        return None

    gated_totals: list[int] = []
    ungated_totals: list[int] = []
    model_name = "unknown"

    for f in gated_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            toks = data.get("tokens", {}).get("total_tokens")
            if toks is not None:
                gated_totals.append(int(toks))
            if "model" in data:
                model_name = data["model"]
        except Exception:
            pass

    for f in ungated_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            toks = data.get("tokens", {}).get("total_tokens")
            if toks is not None:
                ungated_totals.append(int(toks))
            if "model" in data and model_name == "unknown":
                model_name = data["model"]
        except Exception:
            pass

    if not gated_totals or not ungated_totals:
        return None

    gated_med = int(round(statistics.median(gated_totals)))
    ungated_med = int(round(statistics.median(ungated_totals)))
    run_count = len(gated_totals)

    label = f"measured in benchmark: gated {gated_med:,} vs ungated {ungated_med:,} (median of {run_count} runs, model {model_name})"

    return BaselineComparison(
        task=matched_task,
        gated_tokens_median=gated_med,
        ungated_tokens_median=ungated_med,
        run_count=run_count,
        model=model_name,
        label=label,
    )


# -----------------------------------------------------------------------------
# Receipt Construction & Calculation
# -----------------------------------------------------------------------------


def build_token_receipt(
    run_id: str,
    usage_ledger: UsageLedger | None = None,
    decision_ledger: DecisionLedger | None = None,
    budget_tracker: BudgetTracker | None = None,
    conductor: Any | None = None,
    objective: str = "",
    mode: str = "software_dev",
    provider: str = "mock",
    model: str = "default",
    duration_seconds: float = 0.0,
    dry_run: bool = False,
    benchmark_results_dir: Path | str | None = None,
) -> TokenReceipt:
    """Build a complete, truthful TokenReceipt from ledgers and run artifacts."""
    # Resolve ledgers from conductor if provided
    if conductor is not None:
        if usage_ledger is None:
            usage_ledger = getattr(conductor, "usage_ledger", None)
        if decision_ledger is None:
            decision_ledger = getattr(conductor, "decision_ledger", None)
        if budget_tracker is None:
            budget_tracker = getattr(conductor, "budget_tracker", None)
        if not provider or provider == "mock":
            if getattr(conductor, "provider", None):
                provider = getattr(conductor.provider, "provider_name", provider)
                model = getattr(conductor.provider, "model", model)

    # 1. Process usage ledger
    if usage_ledger is not None:
        u_summary = usage_ledger.summary()
        llm_calls = u_summary["total_calls"]
        tokens_in = u_summary["prompt_tokens"]
        tokens_out = u_summary["completion_tokens"]
        tokens_total = u_summary["total_tokens"]
        tokens_in_measured = u_summary["measured_prompt_tokens"]
        tokens_in_estimated = u_summary["estimated_prompt_tokens"]
        tokens_out_measured = u_summary["measured_completion_tokens"]
        tokens_out_estimated = u_summary["estimated_completion_tokens"]
        tokens_measured = tokens_in_measured + tokens_out_measured
        tokens_estimated = tokens_in_estimated + tokens_out_estimated
        is_est = u_summary["is_estimated"]
    else:
        llm_calls = 0
        tokens_in = 0
        tokens_out = 0
        tokens_total = 0
        tokens_in_measured = 0
        tokens_in_estimated = 0
        tokens_out_measured = 0
        tokens_out_estimated = 0
        tokens_measured = 0
        tokens_estimated = 0
        is_est = False

    # 2. Process decision ledger
    if decision_ledger is not None:
        gate_evaluations = decision_ledger.total_evaluations
        reflexes = decision_ledger.total_reflexes
        escalations = decision_ledger.total_escalations
        avoided_tokens = decision_ledger.avoided_tokens_estimated
        records = decision_ledger.records
    else:
        gate_evaluations = 0
        reflexes = 0
        escalations = 0
        avoided_tokens = 0
        records = []

    # 3. Dry-run enforcement (Task 6)
    if dry_run:
        # Dry-run receipts show zero provider tokens and say so
        tokens_in = 0
        tokens_out = 0
        tokens_total = 0
        tokens_in_measured = 0
        tokens_in_estimated = 0
        tokens_out_measured = 0
        tokens_out_estimated = 0
        tokens_measured = 0
        tokens_estimated = 0
        confidence = "measured"
    else:
        # Confidence is "measured" if all numbers were provider-measured and calls > 0
        if not is_est and llm_calls > 0:
            confidence = "measured"
        elif llm_calls == 0 and gate_evaluations == 0:
            confidence = "measured"
        else:
            confidence = "estimated"

    # 4. Per-arm breakdowns
    per_arm_list: list[ArmReceiptSummary] = []
    arms = getattr(conductor, "arms", []) if conductor else []

    if arms:
        for arm in arms:
            arm_id = arm.arm_id
            role_name = getattr(arm.role, "title", f"Arm {arm_id}")
            # Filter decisions for this arm
            arm_decs = [d for d in records if d.arm == arm_id]
            arm_reflexes = sum(1 for d in arm_decs if d.decision == "reflex")
            arm_escalations = sum(1 for d in arm_decs if d.decision == "escalate")
            arm_avoided = sum(d.would_have_sent_tokens for d in arm_decs if d.decision == "reflex")

            # Per-arm tokens from arm's provider or records
            arm_toks = getattr(arm, "total_tokens", 0)
            arm_calls = arm.step_count

            # If dry_run, zero provider tokens
            if dry_run:
                arm_toks = 0

            # Approximate prompt / completion split for arm if total is known
            arm_in = int(round(arm_toks * 0.75))
            arm_out = arm_toks - arm_in

            per_arm_list.append(
                ArmReceiptSummary(
                    arm_id=arm_id,
                    role=role_name,
                    llm_calls=arm_calls,
                    tokens_in=arm_in,
                    tokens_out=arm_out,
                    tokens_total=arm_toks,
                    reflexes=arm_reflexes,
                    escalations=arm_escalations,
                    avoided_tokens_estimated=arm_avoided,
                    is_estimated=is_est or dry_run,
                )
            )
    elif records:
        # Reconstruct from decision records
        seen_arms = sorted(set(d.arm for d in records))
        for arm_id in seen_arms:
            arm_decs = [d for d in records if d.arm == arm_id]
            arm_reflexes = sum(1 for d in arm_decs if d.decision == "reflex")
            arm_escalations = sum(1 for d in arm_decs if d.decision == "escalate")
            arm_avoided = sum(d.would_have_sent_tokens for d in arm_decs if d.decision == "reflex")
            per_arm_list.append(
                ArmReceiptSummary(
                    arm_id=arm_id,
                    role=f"Arm {arm_id}",
                    llm_calls=0,
                    tokens_in=0,
                    tokens_out=0,
                    tokens_total=0,
                    reflexes=arm_reflexes,
                    escalations=arm_escalations,
                    avoided_tokens_estimated=arm_avoided,
                    is_estimated=True,
                )
            )

    # 5. Budget usage
    budget_usage = BudgetUsageReceipt()
    if budget_tracker is not None:
        b = budget_tracker.budget
        toks_used = 0 if dry_run else tokens_total
        calls_used = 0 if dry_run else llm_calls
        wall_used = round(budget_tracker.elapsed_seconds(), 2)

        budget_usage = BudgetUsageReceipt(
            max_tokens=b.max_tokens,
            tokens_used=toks_used,
            tokens_pct=round((toks_used / b.max_tokens) * 100, 1) if b.max_tokens else None,
            max_llm_calls=b.max_llm_calls,
            calls_used=calls_used,
            calls_pct=round((calls_used / b.max_llm_calls) * 100, 1) if b.max_llm_calls else None,
            max_wall_seconds=b.max_wall_seconds,
            wall_seconds_used=wall_used,
            wall_pct=round((wall_used / b.max_wall_seconds) * 100, 1)
            if b.max_wall_seconds
            else None,
        )

    # 6. Baseline comparison
    baseline_comp = find_benchmark_baseline(
        objective, results_dir=benchmark_results_dir
    )

    return TokenReceipt(
        run_id=run_id,
        mode=mode,
        provider=provider,
        model=model,
        duration_seconds=round(duration_seconds, 2),
        dry_run=dry_run,
        llm_calls=llm_calls,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tokens_total=tokens_total,
        tokens_in_measured=tokens_in_measured,
        tokens_in_estimated=tokens_in_estimated,
        tokens_out_measured=tokens_out_measured,
        tokens_out_estimated=tokens_out_estimated,
        tokens_measured=tokens_measured,
        tokens_estimated=tokens_estimated,
        gate_evaluations=gate_evaluations,
        reflexes=reflexes,
        escalations=escalations,
        avoided_tokens_estimated=avoided_tokens,
        per_arm=per_arm_list,
        budget_usage=budget_usage,
        baseline_comparison=baseline_comp,
        method=RECEIPT_METHOD_EXPLANATION,
        confidence=confidence,
    )


# -----------------------------------------------------------------------------
# Terminal Renderer (Task 3)
# -----------------------------------------------------------------------------


def render_terminal_receipt(
    receipt: TokenReceipt,
    width: int = 76,
    ascii_mode: bool | None = None,
    plain_mode: bool | None = None,
) -> str:
    """Render a compact, truthful boxed block receipt for terminal output.

    Explicitly labels:
    - Spent tokens (measured vs estimated, or zero for dry-run)
    - Avoided tokens ('estimated avoided')
    - Total calls
    - Top 3 arms by tokens
    - Benchmark baseline (if applicable)
    - Link to method ('octoflow receipt --method')
    """
    ascii_active = is_ascii_mode() if ascii_mode is None else ascii_mode
    plain_active = is_plain_mode() if plain_mode is None else plain_mode

    # 1. Plain Mode: line-oriented without decorative boxes
    if plain_active:
        lines = []
        lines.append(f"[receipt {receipt.run_id}]")
        if receipt.dry_run:
            lines.append("  Spent:   0 provider tokens (dry-run: simulation)")
        else:
            lines.append(
                f"  Spent:   {receipt.tokens_total:,} tokens ({receipt.confidence})"
            )
        lines.append(
            f"  Avoided: {receipt.avoided_tokens_estimated:,} tokens (estimated avoided)"
        )
        lines.append(f"  Calls:   {receipt.llm_calls} LLM completions")
        lines.append(
            f"  Gate:    {receipt.gate_evaluations} evaluations ({receipt.reflexes} reflexes, {receipt.escalations} escalations)"
        )

        # Top arms
        sorted_arms = sorted(receipt.per_arm, key=lambda a: a.tokens_total, reverse=True)
        top_arms = sorted_arms[:3]
        if top_arms and not receipt.dry_run:
            top_strs = [f"arm {a.arm_id} ({a.role}): {a.tokens_total:,}" for a in top_arms]
            lines.append(f"  Top arms: {', '.join(top_strs)}")

        if receipt.baseline_comparison:
            lines.append(f"  Baseline: {receipt.baseline_comparison.label}")

        lines.append("  Method:  octoflow receipt --method")
        return "\n".join(lines)

    # 2. Boxed Mode (Standard or ASCII)
    tl = "+" if ascii_active else "┌"
    tr = "+" if ascii_active else "┐"
    bl = "+" if ascii_active else "└"
    br = "+" if ascii_active else "┘"
    hz = "-" if ascii_active else "─"
    vt = "|" if ascii_active else "│"
    bullet = "*" if ascii_active else "•"

    inner_width = max(60, width - 2)

    # Build internal lines
    content_lines: list[str] = []

    # Title header
    header_title = f" Token Receipt: {receipt.run_id} "
    fill_len = max(0, inner_width - len(header_title) - 2)
    top_border = f"{tl}{hz * 2}{header_title}{hz * fill_len}{tr}"

    # Line 1: Spent
    if receipt.dry_run:
        spent_str = "Spent:   0 provider tokens (dry-run: simulation)"
    else:
        spent_str = f"Spent:   {receipt.tokens_total:,} tokens ({receipt.confidence})"
    content_lines.append(spent_str)

    # Line 2: Avoided (strictly 'estimated avoided')
    avoided_str = f"Avoided: {receipt.avoided_tokens_estimated:,} tokens (estimated avoided)"
    content_lines.append(avoided_str)

    # Line 3: Calls & Gate
    calls_str = f"Calls:   {receipt.llm_calls} LLM completions | Gate: {receipt.gate_evaluations} evaluations ({receipt.reflexes} reflexes, {receipt.escalations} escalations)"
    content_lines.append(calls_str)

    # Line 4: Top arms by tokens
    sorted_arms = sorted(receipt.per_arm, key=lambda a: a.tokens_total, reverse=True)
    top_arms = sorted_arms[:3]
    if top_arms and not receipt.dry_run:
        arm_fragments = [
            f"Arm {a.arm_id} ({a.role.split()[0]}): {a.tokens_total:,}" for a in top_arms
        ]
        top_str = f"Top arms: {(' · ' if not ascii_active else ' | ').join(arm_fragments)}"
        content_lines.append(top_str)

    # Line 5: Baseline comparison (only when present)
    if receipt.baseline_comparison:
        content_lines.append(f"Baseline: {receipt.baseline_comparison.label}")

    # Line 6: Method link
    content_lines.append("Method:  octoflow receipt --method")

    # Render formatted box
    box_lines = [top_border]
    for c in content_lines:
        c_clean = sanitize_text(c) if ascii_active else c
        if ascii_active:
            c_clean = c_clean.replace("•", "*").replace("·", "|").replace("—", "-")
            c_clean = "".join(ch if ord(ch) < 128 else "?" for ch in c_clean)
        pad_len = max(0, inner_width - len(c_clean) - 1)
        box_lines.append(f"{vt} {c_clean}{' ' * pad_len}{vt}")

    bottom_border = f"{bl}{hz * inner_width}{br}"
    box_lines.append(bottom_border)

    return "\n".join(box_lines)


# -----------------------------------------------------------------------------
# Storage & Retrieval (Task 4)
# -----------------------------------------------------------------------------


def get_receipt_path(run_id: str) -> Path:
    """Return the filesystem path to receipt.json for a specific run."""
    run_dir = get_runs_dir() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir / "receipt.json"


def save_receipt(receipt: TokenReceipt, run_id: str | None = None) -> Path:
    """Save the TokenReceipt to ~/.octoflow/runs/<id>/receipt.json."""
    rid = run_id or receipt.run_id
    path = get_receipt_path(rid)
    # Validate against pydantic schema before writing
    payload = receipt.model_dump_json(indent=2)
    path.write_text(payload, encoding="utf-8")
    return path


def load_receipt(run_id: str | None = None) -> TokenReceipt:
    """Load a TokenReceipt from ~/.octoflow/runs/<id>/receipt.json or latest run."""
    runs_dir = get_runs_dir()

    if run_id:
        p = runs_dir / run_id / "receipt.json"
        if not p.exists():
            raise FileNotFoundError(f"Receipt file not found for run '{run_id}': {p}")
        return TokenReceipt.model_validate_json(p.read_text(encoding="utf-8"))

    # Pick the latest run with a receipt.json
    candidates = sorted(runs_dir.glob("*/receipt.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No token receipts found under {runs_dir}")

    return TokenReceipt.model_validate_json(candidates[0].read_text(encoding="utf-8"))

