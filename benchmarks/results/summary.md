# OctoFlow Swarm Benchmark Summary

**Generated At:** 2026-10-26T18:56:04.496350+00:00  
**Provider:** `fake` | **Model:** `fake-model-v1` | **Tokens Estimated:** `False`  
**Runs per Configuration:** 24 total runs | **Temperature:** `0.0` | **Base Seed:** `42`  

---

## 1. Executive Summary & Headline Claim Verification

- **Headline Claim Evaluated:** *"80-90% fewer tokens with event-triggered surprise gating"*
- **Measured Median Token Reduction:** **8.3%**
- **Empirical Verdict:** **CORRECTED**: The measured empirical token reduction is **8.3%**, which does NOT support the headline claim of '80-90% fewer tokens'. Token consumption claims must reflect measured evidence rather than theoretical extrapolations.

---

## 2. Comparative Results Across Benchmark Tasks

| Task ID | Task Name | Mode | Calls (Min/Med/Max) | Total Tokens (Min/Med/Max) | Prompt Tokens (Med) | Comp Tokens (Med) | Wall Time | Pass Rate | Gated Savings |
|---|---|---|---|---|---|---|---|---|---|
| `rate_limiter` | Sliding Window Rate Limiter | Gated | 22 / 22.0 / 22 | 4400 / 4400.0 / 4400 | 3300.0 | 1100.0 | 0.01s | 100.0% | 8.3% reduction |
| `rate_limiter` | Sliding Window Rate Limiter | Ungated (always_escalate) | 24 / 24.0 / 24 | 4800 / 4800.0 / 4800 | 3600.0 | 1200.0 | 0.01s | 100.0% | - |
| `lru_cache` | O(1) LRU Cache | Gated | 22 / 22.0 / 22 | 4400 / 4400.0 / 4400 | 3300.0 | 1100.0 | 0.01s | 100.0% | 8.3% reduction |
| `lru_cache` | O(1) LRU Cache | Ungated (always_escalate) | 24 / 24.0 / 24 | 4800 / 4800.0 / 4800 | 3600.0 | 1200.0 | 0.01s | 100.0% | - |
| `jwt_validator` | HMAC-SHA256 JWT Tokenizer | Gated | 22 / 22.0 / 22 | 4400 / 4400.0 / 4400 | 3300.0 | 1100.0 | 0.01s | 100.0% | 8.3% reduction |
| `jwt_validator` | HMAC-SHA256 JWT Tokenizer | Ungated (always_escalate) | 24 / 24.0 / 24 | 4800 / 4800.0 / 4800 | 3600.0 | 1200.0 | 0.01s | 100.0% | - |
| `dag_topo_sort` | Topological DAG Resolver | Gated | 22 / 22.0 / 22 | 4400 / 4400.0 / 4400 | 3300.0 | 1100.0 | 0.01s | 100.0% | 8.3% reduction |
| `dag_topo_sort` | Topological DAG Resolver | Ungated (always_escalate) | 24 / 24.0 / 24 | 4800 / 4800.0 / 4800 | 3600.0 | 1200.0 | 0.01s | 100.0% | - |

---

## 3. Methodology

### Benchmark Tasks & Verification
Evaluated against 4 standard algorithmic and architectural challenges:
1. **Rate Limiter (`rate_limiter`):** Thread-safe sliding window rate limiter in `limiter.py`.
2. **LRU Cache (`lru_cache`):** O(1) capacity-evicting LRU cache in `lru.py`.
3. **JWT Validator (`jwt_validator`):** HMAC-SHA256 signature and verification in `auth.py`.
4. **DAG Topological Sort (`dag_topo_sort`):** Dependency resolution and cycle detection in `topo.py`.

### Execution Environment & Isolation
- Each benchmark run executes in an isolated sandbox workspace.
- Acceptance testing is executed inside the sandbox using standard `pytest` running acceptance test suites directly against generated code.

### Gated vs. Ungated (`always_escalate`) Baseline
- **Gated Mode (`gated`):** Arms encode sensory feedback from tool executions into state observations. When sensory surprise $\Delta S_i \le \theta$, the arm enters quiescence and suppresses subsequent LLM queries for that mission phase.
- **Ungated Baseline (`always_escalate`):** Arms force escalation on every evaluation cycle (equivalent to $\theta = 0$), bypassing silent auto-quiescence and invoking the LLM model on every cycle across all arms.

### Determinism & Temperature
- Temperature was fixed to `0.0` where supported by the provider to maximize reproducibility.
- Random seeds were pinned starting at seed `42` for client-side ordering and mock sampling.
- **Nondeterminism Disclosure:** Even at temperature 0, distributed frontier LLM APIs (e.g. Anthropic, OpenAI) may exhibit non-deterministic generation due to floating-point batching order and mixture-of-experts routing in production infrastructure.

---

## 4. Limitations & Data Caveats

- **Token Measurement Fidelity:**
  - ✔ **Tokens were MEASURED**: Token usage was obtained directly from API provider response headers (`prompt_tokens`, `completion_tokens`).
- **Provider & Model Scope:**
  - Evaluated using provider `fake` with model `fake-model-v1`.
  - Results using mock or fake providers represent synthetic execution traces designed for verification of accounting and harness mechanics, NOT empirical performance of neural foundation models.
- **Task Scope:**
  - The challenge tasks test targeted Python algorithmic implementations. Real-world multi-file software refactorings may involve differing ratios of silent file inspection versus escalation.
