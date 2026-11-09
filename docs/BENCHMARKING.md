# OctoFlow Swarm Benchmarking & Evaluation Methodology

This document outlines the fair, reproducible benchmarking harness implemented in `octoflow/bench.py` and invoked via `octoflow bench`. It defines how execution modes are evaluated, how token consumption is measured versus estimated, and how real-provider benchmarks are executed.

---

## 1. Objective & Scope

The headline project claim *"80-90% fewer tokens with event-triggered surprise gating"* previously lacked empirical validation. In prior versions, token savings were calculated synthetically using a hardcoded `tokens_used * 8` multiplier. 

The benchmark harness replaces theoretical claims with honest, reproducible measurements comparing the **gated swarm** against an **ungated baseline** on identical tasks under isolated sandbox conditions.

---

## 2. Benchmark Tasks

The evaluation suite runs four standardized algorithmic and architectural challenges:

1. **Sliding Window Rate Limiter (`rate_limiter`):**
   - *Target:* `limiter.py`
   - *Objective:* Thread-safe `SlidingWindowRateLimiter` supporting `allow_request(client_id, limit, window_sec)`.
   - *Acceptance:* Validated via `test_limiter.py` using `pytest`.
2. **O(1) LRU Cache (`lru_cache`):**
   - *Target:* `lru.py`
   - *Objective:* Capacity-bounded cache supporting `get(key)` and `put(key, value)` with least-recently-used eviction.
   - *Acceptance:* Validated via `test_lru.py` using `pytest`.
3. **HMAC-SHA256 JWT Tokenizer (`jwt_validator`):**
   - *Target:* `auth.py`
   - *Objective:* Pure-hashlib HMAC-SHA256 payload signing and token verification.
   - *Acceptance:* Validated via `test_auth.py` using `pytest`.
4. **Topological DAG Resolver (`dag_topo_sort`):**
   - *Target:* `topo.py`
   - *Objective:* Dependency resolution with valid topological order and cycle detection.
   - *Acceptance:* Validated via `test_topo.py` using `pytest`.
5. **Tiny FastAPI Todo API (`fastapi_todo`):**
   - *Target:* `app.py`
   - *Objective:* REST endpoints `GET /todos`, `POST /todos`, and `DELETE /todos/{id}` with 404 validation.
   - *Acceptance:* Validated via `test_app.py` using `TestClient` and `pytest`.

### Verified Live Local LLM Performance (Ollama `qwen2.5-coder:7b`)

Hardware environment: Apple Silicon arm64 (8-core CPU, 16GB RAM), local Ollama inference server.  
All token counts shown below are **MEASURED directly from native Ollama HTTP response headers** (`prompt_eval_count`, `eval_count`; `estimated=False`).

| Benchmark Task | Target File | Execution Mode | Runs | Pass Rate | LLM Calls (Min/Med/Max) | Total Tokens (Min/Med/Max) | Prompt Tokens (Med) | Comp Tokens (Med) | Wall Time (Med) | Gated Token Savings |
|---|---|---|---|---|---|---|---|---|---|---|
| `rate_limiter` | `limiter.py` | **Gated** | 5 | **100% (5/5)** | 4 / 4.0 / 4 | 3,118 / 3,118 / 3,118 | 1,860 | 1,258 | 129.06s | **35.0% reduction** |
| `rate_limiter` | `limiter.py` | **Ungated** | 1 | **0.0% (0/1)** | 6 / 6.0 / 6 | 4,798 / 4,798 / 4,798 | 2,873 | 1,925 | 231.91s | Baseline (always_escalate) |
| `fastapi_todo` | `app.py` | **Gated** | 5 | **100% (5/5)** | 4 / 4.0 / 4 | 3,193 / 3,193 / 3,193 | 2,106 | 1,087 | 185.27s | - |

#### Key Empirical Insights from Live Evaluation
1. **Token & Call Efficiency**: On the `rate_limiter` challenge, sensory surprise gating reduced token consumption by **35.0%** (3,118 vs 4,798 tokens) and LLM calls by **33.3%** (4 vs 6 calls) compared to the ungated baseline.
2. **Reliability & Swarm Coordination**: In ungated mode, unquenched specialist arms continued emitting redundant file modifications, leading to race conditions and test failures (0/1 pass rate). In gated mode, once sensory surprise dropped below $\theta \le 0.48$, the arm entered silent quiescence, allowing the QA arm to verify the code without interference, achieving a **100% pass rate (5/5)**.
3. **Wall-Clock Latency**: Gated execution completed in **129.06s** median wall time compared to **231.91s** ungated (44.4% faster).
4. **Raw Benchmark Artifacts**: Raw JSON outputs for all runs are committed under [`benchmarks/results/published/`](../benchmarks/results/published/).

*For complete failure taxonomy, root cause analysis, and cassette replay, see [`docs/audit/P3.2-failure-taxonomy.md`](audit/P3.2-failure-taxonomy.md) and [`docs/model-compatibility.md`](model-compatibility.md).*

---

## 3. Gated Mode vs. Ungated Baseline

Execution mode is configured through `gate_mode` in settings, config, and the CLI (`--mode gated|ungated|both`):

- **Gated Mode (`gated`):**
  Arms execute their assigned domain actions. Sensory observations are encoded via `CodeSensoryEncoder`. When sensory surprise satisfies $\Delta S_i \le \theta$, the arm becomes quiescent (`is_quiescent = True`) and suppresses subsequent LLM queries for subsequent cycles of that mission phase.
- **Ungated Baseline (`always_escalate`):**
  Arms force escalation on every evaluation cycle (equivalent to $\theta = 0$), bypassing silent auto-quiescence. Every arm cycle that is evaluated invokes the LLM backend up to `max_cycles`.

Both modes run against the same task objectives in isolated sandboxes using identical configurations.

---

## 4. Usage Accounting (`UsageLedger`)

Token usage is tracked per run using `UsageLedger` in `octoflow/usage.py`:

- **Measured Usage:** Providers that return native usage headers (Anthropic `usage`, OpenAI `usage`, Ollama `prompt_eval_count`/`eval_count`, Gemini `usage_metadata`) record exact `prompt_tokens` and `completion_tokens` with `estimated=False`.
- **Estimated Usage:** When usage metadata is missing or unavailable, tokens are estimated using the standard character heuristic:
  $$\text{tokens} = \lceil \frac{\text{len(text)}}{4} \rceil$$
  and flagged with `estimated=True`.
- **Ledger Aggregation:** The ledger aggregates total calls, prompt tokens, completion tokens, and preserves an `is_estimated` flag indicating if any estimate was used during the run.

### Limitations of Estimated Token Counts
Character-based estimation (`ceil(chars / 4)`) provides a rough approximation for English text and code. However:
1. Subword tokenizers (e.g. Byte-Pair Encoding in Claude and GPT models) vary significantly depending on code syntax, whitespace, and special characters.
2. Estimated counts can deviate from real token usage by ±15-20%.
3. **Never present estimated tokens as exact model counts.** The benchmark summary explicitly distinguishes measured from estimated runs.

---

## 5. How to Run the Benchmark

### Running with Fake Provider (Sample / Verification)
The `fake` provider runs deterministic, zero-cost simulations with known token usage to verify accounting and result generation:

```bash
# Run all tasks with both gated and ungated modes (3 repetitions)
octoflow bench --task all --mode both --provider fake --runs 3 --out benchmarks/results/

# Run a single task in gated mode
octoflow bench --task rate_limiter --mode gated --provider fake --runs 1
```

### Running Real-Provider Benchmarks
To evaluate real foundation models, ensure your API key or local daemon is active:

#### Anthropic (Claude 3.5 Sonnet)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
octoflow bench --task all --mode both --provider anthropic --model claude-3-5-sonnet-20241022 --runs 3 --out benchmarks/results/
```

#### OpenAI (GPT-4o)
```bash
export OPENAI_API_KEY="sk-..."
octoflow bench --task all --mode both --provider openai --model gpt-4o --runs 3 --out benchmarks/results/
```

#### Local Ollama (e.g. Qwen 2.5 Coder)
```bash
# Ensure ollama daemon is running: ollama run qwen2.5-coder:7b
octoflow bench --task all --mode both --provider ollama --model qwen2.5-coder:7b --runs 3 --out benchmarks/results/
```

---

## 6. Output Files & Statistics

Each benchmark invocation produces:
1. **Per-Run JSON Files:** Stored in `{out_dir}/{task_id}_{mode}_run_{idx}.json` containing:
   - `task`, `task_name`, `category`, `mode`, `provider`, `model`, `seed`, `temperature`, `wall_time_seconds`
   - `llm_calls`, `tokens` (`prompt_tokens`, `completion_tokens`, `total_tokens`, `estimated`)
   - `files_written`, `acceptance_test_passed`, `outcome`, `settings`
2. **Summary Document (`summary.md`):** Aggregates across runs:
   - Median, min, and max for LLM calls, total tokens, prompt tokens, completion tokens, and wall time
   - Pass rate percentage per task and mode
   - Ratio of gated to ungated token consumption ($1 - \frac{\text{gated}}{\text{ungated}}$)
   - Headline claim evaluation: explicitly states whether measured numbers support or correct the 80-90% claim
   - Auto-generated Methodology and Limitations sections based on provider and estimation flags

---

## 7. Determinism & Temperature

- Temperature defaults to `0.0` where the provider permits to maximize reproducibility.
- Pseudo-random seeds are pinned (default: `seed = 42 + run_idx - 1`) for client-side repeatability.
- **Nondeterminism Disclosure:** Even at temperature 0, frontier LLM APIs exhibit non-determinism due to server-side floating-point accumulation order across GPU clusters and mixture-of-experts batch scheduling. Results should be interpreted using the recorded median across multiple runs.
