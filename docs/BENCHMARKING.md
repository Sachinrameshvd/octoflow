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
