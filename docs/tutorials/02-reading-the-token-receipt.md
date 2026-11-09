# Tutorial 2: Reading the Truthful Token Receipt

**Estimated Duration:** 5 minutes  
**Verification:** Verified on 2026-11-09, OctoFlow v0.2.0  

This tutorial explains how to interpret OctoFlow's post-mission token receipt, understand the difference between measured and estimated metrics, and inspect arm-by-arm cost breakdowns.

---

## Prerequisites

Have at least one completed OctoFlow run or run a quick simulation:
```bash
octoflow run "Create a string utility library" --dry-run
```

---

## Step 1: View the Latest Run Receipt

Run the receipt command to display the post-flight accounting:

```bash
octoflow receipt
```

### Expected Output

```text
┌── Token Receipt: 1794049840-56720e ──────────────────────────────────────┐
│ Spent:   22,637 tokens (measured)                                        │
│ Avoided: 7,704 tokens (estimated avoided)                                │
│ Calls:   29 LLM completions | Gate: 29 evaluations (24 reflexes, 5 escalations)│
│ Top arms: Arm 5 (Integration): 8,215 · Arm 6 (Security): 4,664 · Arm 1 (Model): 2,981│
│ Method:  octoflow receipt --method                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Step 2: Understanding the Receipt Fields

1. **`Spent: 22,637 tokens (measured)`**:
   - The total number of tokens processed by the LLM provider across all cycles.
   - Tagged as **`measured`** when sourced directly from provider API response headers (Ollama `prompt_eval_count`/`eval_count`, Anthropic `usage`, OpenAI `usage`).
   - Tagged as **`estimated`** if heuristic fallback was used (`ceil(chars / 4)`).
2. **`Avoided: 7,704 tokens (estimated avoided)`**:
   - The total tokens saved by local sensory gating. When an arm's sensory change remains below threshold ($\Delta S_i \le \theta$), routine file edits execute as silent local reflexes without central LLM escalation.
   - Always labeled **`estimated avoided`** because it reflects the prompt size that *would have been dispatched* had the reflex escalated.
3. **`Calls: 29 LLM completions`**:
   - The total round-trip inference requests sent to the backend.
4. **`Gate: 29 evaluations (24 reflexes, 5 escalations)`**:
   - Shows how many decisions were resolved autonomously (reflexes) versus escalated to the conductor for replanning.

---

## Step 3: Inspecting Machine-Readable JSON

For programmatic consumption in CI or billing pipelines, pass `--json`:

```bash
octoflow receipt --json
```

### Expected Output Excerpt

```json
{
  "run_id": "1794049840-56720e",
  "mode": "software_dev",
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "tokens_measured": 22637,
  "tokens_estimated": 0,
  "gate_evaluations": 29,
  "reflexes": 24,
  "escalations": 5,
  "avoided_tokens_estimated": 7704,
  "confidence": "measured"
}
```

---

## Step 4: Reviewing Accounting Methodology

To inspect the mathematical formula and accounting invariants directly in the terminal, run:

```bash
octoflow receipt --method
```

---

## Next Steps

- Learn how to rollback a run: [Tutorial 3: Undoing a Run](03-undoing-a-run.md)
- Learn about the underlying gate math: [docs/architecture.md](../architecture.md#9-event-triggered-sensory-gate-math-worked-example)
