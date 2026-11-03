# Truthful Token Receipts & Sensory Gate Accounting (P7.1)

OctoFlow provides an honest, transparent, and mathematically rigorous accounting of every token spent and avoided during swarm execution.

---

## 1. Principles of Truthful Accounting

1. **No Vanity Metrics**: OctoFlow never fabricates generic multipliers or claims savings against hypothetical tools.
2. **Explicit Labeling**: Every number is labeled as either **measured** (sourced directly from provider API usage headers/response objects) or **estimated** (derived from standard character heuristics).
3. **Avoided Tokens vs Spent Tokens**: Tokens avoided via local reflexes are explicitly labeled as **`estimated avoided`** and never presented as measured cost reductions.
4. **Zero Prompt Exposure**: Receipts track token volumes, evaluation decisions, and biophysical metrics ($\Delta S_i, \theta$), but **never store raw prompt text**, safeguarding user confidentiality.

---

## 2. Methodology & Mathematical Model

The computation methodology is formally defined in two sentences:

> *Token usage is collected from provider API responses or estimated using character heuristics (`ceil(chars / 4)`). Avoided tokens are estimated as the prompt size that would have been dispatched to the central conductor for each gate evaluation classified as a local reflex.*

### Sensory Surprise Gate Accounting

For each arm cycle, the biophysical predictive coding gate evaluates:
$$\Delta S_i = \frac{1}{D} \|o_t - \hat{o}_t\|^2$$

- **Reflex ($\Delta S_i \le \theta$)**: The arm executes silently without escalating to central attention. The prompt that would have been dispatched to the central conductor is measured with `estimate_tokens_from_chars(prompt)` and recorded in the decision ledger as `would_have_sent_tokens` (flagged estimated).
- **Escalate ($\Delta S_i > \theta$)**: Sensory surprise exceeds the adaptive threshold $\theta$, triggering conductor intervention. `would_have_sent_tokens` is 0.

Total avoided tokens:
$$\text{Avoided Tokens (estimated)} = \sum_{j \in \text{reflexes}} \text{would\_have\_sent\_tokens}_j$$

### Confidence Classification

- **`measured`**: All completion calls were metered directly by the provider API (e.g. Ollama, Anthropic, OpenAI) with zero unmetered fallbacks, or a dry-run execution with zero provider tokens.
- **`estimated`**: One or more calls required character-heuristic estimation (`ceil(len(text) / 4)`).

---

## 3. Annotated Sample Receipt (Fake Benchmark Provider)

> **Notice**: The sample below was generated using OctoFlow's deterministic `FakeBenchmarkProvider` (120 prompt tokens, 30 completion tokens per call) running the canonical O(1) LRU Cache task.

### Terminal Boxed View

```text
┌── Token Receipt: run-fixture-lru-01 ───────────────────────────────┐
│ Spent:   1,500 tokens (measured)                                   │
│ Avoided: 4,320 tokens (estimated avoided)                          │
│ Calls:   10 LLM completions | Gate: 8 evaluations (6 reflexes, 2 escalations)
│ Top arms: Arm 2 (Backend): 600 · Arm 0 (Architect): 450 · Arm 6 (Chaos): 300
│ Baseline: measured in benchmark: gated 4,400 vs ungated 4,800 (median of 3 runs, model fake-model-v1)
│ Method:  octoflow receipt --method                                 │
└────────────────────────────────────────────────────────────────────┘
```

### Terminal Plain View (`--plain` or Non-TTY)

```text
[receipt run-fixture-lru-01]
  Spent:   1,500 tokens (measured)
  Avoided: 4,320 tokens (estimated avoided)
  Calls:   10 LLM completions
  Gate:    8 evaluations (6 reflexes, 2 escalations)
  Top arms: arm 2 (Backend API): 600, arm 0 (System Architect): 450, arm 6 (Chaos & QA): 300
  Baseline: measured in benchmark: gated 4,400 vs ungated 4,800 (median of 3 runs, model fake-model-v1)
  Method:  octoflow receipt --method
```

### JSON Schema Output (`receipt --json`)

```json
{
  "run_id": "run-fixture-lru-01",
  "mode": "software_dev",
  "provider": "fake",
  "model": "fake-model-v1",
  "duration_seconds": 1.25,
  "dry_run": false,
  "llm_calls": 10,
  "tokens_in": 1200,
  "tokens_out": 300,
  "tokens_total": 1500,
  "tokens_in_measured": 1200,
  "tokens_in_estimated": 0,
  "tokens_out_measured": 300,
  "tokens_out_estimated": 0,
  "tokens_measured": 1500,
  "tokens_estimated": 0,
  "gate_evaluations": 8,
  "reflexes": 6,
  "escalations": 2,
  "avoided_tokens_estimated": 4320,
  "per_arm": [
    {
      "arm_id": 2,
      "role": "Backend API Specialist",
      "llm_calls": 4,
      "tokens_in": 450,
      "tokens_out": 150,
      "tokens_total": 600,
      "reflexes": 3,
      "escalations": 1,
      "avoided_tokens_estimated": 2160,
      "is_estimated": false
    },
    {
      "arm_id": 0,
      "role": "System Architect",
      "llm_calls": 3,
      "tokens_in": 338,
      "tokens_out": 112,
      "tokens_total": 450,
      "reflexes": 2,
      "escalations": 1,
      "avoided_tokens_estimated": 1440,
      "is_estimated": false
    },
    {
      "arm_id": 6,
      "role": "Chaos & QA Specialist",
      "llm_calls": 2,
      "tokens_in": 225,
      "tokens_out": 75,
      "tokens_total": 300,
      "reflexes": 1,
      "escalations": 0,
      "avoided_tokens_estimated": 720,
      "is_estimated": false
    }
  ],
  "budget_usage": {
    "max_tokens": 200000,
    "tokens_used": 1500,
    "tokens_pct": 0.8,
    "max_llm_calls": 200,
    "calls_used": 10,
    "calls_pct": 5.0,
    "max_wall_seconds": 1800,
    "wall_seconds_used": 1.25,
    "wall_pct": 0.1
  },
  "baseline_comparison": {
    "task": "lru_cache",
    "gated_tokens_median": 4400,
    "ungated_tokens_median": 4800,
    "run_count": 3,
    "model": "fake-model-v1",
    "label": "measured in benchmark: gated 4,400 vs ungated 4,800 (median of 3 runs, model fake-model-v1)"
  },
  "method": "Token usage is collected from provider API responses or estimated using character heuristics (ceil(chars/4)). Avoided tokens are estimated as the prompt size that would have been dispatched to the central conductor for each gate evaluation classified as a local reflex.",
  "confidence": "measured"
}
```

---

## 4. CLI Usage

```bash
# View the receipt for the most recent run
octoflow receipt

# View a specific historical run
octoflow receipt run-1730501234-a1b2c3

# Emit machine-readable JSON (validates against TokenReceipt pydantic schema)
octoflow receipt --json

# View the mathematical calculation methodology and accounting rules
octoflow receipt --method
```

---

## 5. Empirical Benchmark Baselines

When an execution corresponds to a canonical task present in `benchmarks/results/`, OctoFlow automatically computes medians across all recorded runs:
- Format: `measured in benchmark: gated X vs ungated Y (median of N runs, model M)`
- If no empirical benchmark exists for a given task, the baseline comparison is omitted entirely.
