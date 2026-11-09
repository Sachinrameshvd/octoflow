# OctoFlow Published Swarm Benchmark Summary

**Generated At:** 2026-11-09T08:46:14+00:00  
**Hardware Environment:** Apple Silicon arm64 (8-core CPU, 16GB RAM)  
**Provider:** `ollama` | **Model:** `qwen2.5-coder:7b` | **Tokens Estimated:** `False` (Measured via Ollama response headers)  
**Temperature:** `0.0` | **Base Seed:** `42`  

---

## 1. Executive Summary & Empirical Verdict

- **Claim Evaluated:** *"80-90% fewer tokens with event-triggered surprise gating"*
- **Measured Empirical Token Reduction:** **35.0%** (3,118 tokens gated vs 4,798 tokens ungated on `rate_limiter`).
- **Empirical Verdict:** **CORRECTED AND MEASURED**. The empirical token reduction on real local foundation models is **35.0%**, not the theoretical 80-90% figure derived from synthetic multipliers. Gating also reduced total LLM calls by **33.3%** and wall-clock latency by **44.4%** while improving test pass rate from 0% to 100%.

---

## 2. Comparative Results Across Benchmark Tasks

| Task ID | Task Name | Mode | Runs | Pass Rate | LLM Calls (Min/Med/Max) | Total Tokens (Min/Med/Max) | Prompt Tokens (Med) | Comp Tokens (Med) | Wall Time (Med) | Token Savings |
|---|---|---|---|---|---|---|---|---|---|---|
| `rate_limiter` | Sliding Window Rate Limiter | **Gated** | 5 | **100.0% (5/5)** | 4 / 4.0 / 4 | 3,118 / 3,118.0 / 3,118 | 1,860.0 | 1,258.0 | 129.06s | **35.0% reduction** |
| `rate_limiter` | Sliding Window Rate Limiter | **Ungated** | 1 | **0.0% (0/1)** | 6 / 6.0 / 6 | 4,798 / 4,798.0 / 4,798 | 2,873.0 | 1,925.0 | 231.91s | Baseline (always_escalate) |
| `fastapi_todo` | Tiny FastAPI Todo API | **Gated** | 5 | **100.0% (5/5)** | 4 / 4.0 / 4 | 3,193 / 3,193.0 / 3,193 | 2,106.0 | 1,087.0 | 185.27s | - |

---

## 3. Raw Per-Run Data Files

All raw run results are recorded in this directory:
- `rate_limiter_gated_run_1.json` through `run_5.json`
- `rate_limiter_always_escalate_run_1.json`
- `fastapi_todo_gated_run_1.json` through `run_5.json`

---

## 4. Methodology & Accounting

1. **Isolation**: Every run executed in an isolated workspace sandbox.
2. **Measurement**: Token counts are **100% measured** directly from Ollama's HTTP JSON response headers (`prompt_eval_count`, `eval_count`). `estimated=False`.
3. **Acceptance Testing**: Automated acceptance suites executed via pytest directly against generated files (`limiter.py`, `app.py`).

---

## 5. Limitations

- Tested using local 7B parameter model (`qwen2.5-coder:7b`). Larger frontier models (e.g. Claude 3.5 Sonnet, GPT-4o) may exhibit different baseline prompt lengths.
- Benchmark tasks represent bounded algorithmic and web microservice challenges.
- Local inference latency depends heavily on available GPU/NPU memory bandwidth.
