# Tutorial 8: Running Swarm Algorithmic Benchmarks

**Estimated Duration:** 8 minutes  
**Verification:** Verified on 2026-11-09, OctoFlow v0.2.0  

This tutorial shows how to execute OctoFlow's reproducible benchmark harness, compare the **gated swarm** against an **ungated baseline**, and inspect empirical token savings.

---

## What Does the Benchmark Evaluate?

The benchmark suite (`octoflow bench`) tests identical programming challenges under two execution modes:
1. **Gated Mode (`gated`)**: Arms utilize event-triggered sensory gating ($\Delta S_i \le \theta$). Routine cycles execute silently as local reflexes, suppressing redundant LLM queries.
2. **Ungated Mode (`ungated` / `always_escalate`)**: Every arm cycle unconditionally escalates to the LLM backend up to the cycle limit ($\theta = 0$), establishing the chatty baseline.

---

## Step 1: Run a Benchmark with the Fake Provider

To verify the benchmark harness instantly with zero API cost, use the deterministic `fake` provider:

```bash
octoflow bench --task rate_limiter --mode both --provider fake --runs 1
```

### Expected Output

```text
◈ OctoFlow Benchmark Suite
• Task: rate_limiter (Sliding Window Rate Limiter)
• Provider: fake (model: fake-model-v1)
• Mode: both (comparing Gated vs. Ungated)

[1/2] Running Gated Mode (Run 1/1)...
  • Outcome: COMPLETE (tests passed)
  • LLM Calls: 4 | Tokens: 3,118 | Time: 1.25s

[2/2] Running Ungated Mode (Run 1/1)...
  • Outcome: COMPLETE (tests passed)
  • LLM Calls: 8 | Tokens: 6,240 | Time: 2.10s

┌── Benchmark Comparison Summary: rate_limiter ────────────────────────────┐
│ Gated Tokens:   3,118 (median)                                           │
│ Ungated Tokens: 6,240 (median)                                           │
│ Measured Token Savings: 50.0% reduction                                  │
│ Pass Rate: 100% (Gated) vs 100% (Ungated)                                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Step 2: Run a Single Task on Local Ollama

To evaluate your local Ollama model (`qwen2.5-coder:7b`):

```bash
octoflow bench --task rate_limiter --mode gated --provider ollama --model qwen2.5-coder:7b --runs 1
```

---

## Step 3: Run the Full Evaluation Suite

To run all canonical tasks (`rate_limiter`, `lru_cache`, `jwt_validator`, `dag_topo_sort`, `fastapi_todo`) and save structured JSON artifacts:

```bash
octoflow bench --task all --mode both --provider fake --runs 3 --out benchmarks/results/
```

This generates:
- Per-run JSON files: `benchmarks/results/{task}_{mode}_run_{idx}.json`
- An aggregated Markdown report: `benchmarks/results/summary.md`

---

## Step 4: Review Real-World Benchmark Results

To inspect historical empirical results across models, read the official methodology doc:

```bash
cat docs/benchmarks.md
```

*Note: On real code generation tasks with `qwen2.5-coder:7b`, measured token savings range between 15% and 25%. See [docs/benchmarks.md](../benchmarks.md) for complete details.*

---

## Next Steps

- Consult the FAQ for common operational questions: [docs/FAQ.md](../FAQ.md)
- Troubleshoot common errors: [docs/TROUBLESHOOTING.md](../TROUBLESHOOTING.md)

