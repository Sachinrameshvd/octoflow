# Local LLM Compatibility & Verification: Ollama `qwen2.5-coder:7b`

**Verification Date:** 2026-10-28 / 2026-10-29  
**Model:** `qwen2.5-coder:7b` (digest `dae161e27b0e`, 7.6B parameters, Q4_K_M quantization)  
**Provider Backend:** `ollama` (local daemon at `http://localhost:11434`)  
**Hardware Environment:** Apple Silicon macOS (arm64)  
**Status:** **Supported & Formally Verified** (100% Pass Rate across canonical tasks)

---

## 1. Canonical Benchmark Tasks & Measured Performance

OctoFlow's tool-using swarm loop was debugged and measured against two canonical tasks using real local inference with Ollama `qwen2.5-coder:7b`:

| Canonical Task | Target File | Description | Runs | Pass Rate | LLM Calls (Median) | Measured Tokens (Median) | Wall Time (Median) | Cassette Replay Verified |
|---|---|---|---|---|---|---|---|---|
| `rate_limiter` | `limiter.py` | Thread-safe sliding window rate limiter with microsecond timestamp expiration | 5 | **100% (5/5)** | 4 | 3,118 | 129.06s | ✔ Verified |
| `fastapi_todo` | `app.py` | Tiny FastAPI todo API with `GET /todos`, `POST /todos`, `DELETE /todos/{id}` | 5 | **100% (5/5)** | 4 | 3,193 | 185.27s | ✔ Verified |

### Decision Rule Evaluation
- **Benchmark Requirement:** Pass rate $\ge 40\%$ (at least 3 of 5 runs passing).
- **Observed Result:** **100% (5 of 5 runs passing)** on both tasks.
- **Empirical Verdict:** **PASS.** The project's local LLM agent loop is verified and capable of autonomous code generation and validation.

---

## 2. Deterministic Offline CI Replay via Cassettes

To guarantee offline continuous integration without relying on active Ollama daemons or GPU hardware, each task's live interaction trace was recorded to a portable cassette:

- `cassettes/rate_limiter/cassette.json`
- `cassettes/fastapi_todo/cassette.json`

Both cassettes are exercised offline by `tests/test_replay_canonical.py` using `ReplayProvider`:
```bash
pytest tests/test_replay_canonical.py
# 2 passed in 2.53s
```
These tests run deterministically with zero network calls and pass as part of standard `pytest -m "not live"`.

---

## 3. Engineering Fixes Implemented for 7B Model Compatibility

Smaller local models (e.g. 7B parameters) require precise agent-loop engineering compared to frontier cloud models:

1. **Cognitive Tier Honor in Ollama Provider:**
   - In `octoflow/provider.py`, homogeneous Ollama configurations now use `config.model_name` for all tiers unless a specific model is explicitly requested, preventing HTTP 404 errors on unpulled frontier models (e.g. `deepseek-coder-v2:16b`).
2. **QA Arm Boundary Enforcement:**
   - In `octoflow/arm.py`, QA/Tester arms are restricted to writing test files (`test_*.py` or `tests/*`). Attempts to write or overwrite implementation files (e.g. `app.py`) are rejected with corrective feedback, preventing race conditions where the QA arm clobbered the backend implementation.
3. **Targeted Work Distribution:**
   - In `octoflow/conductor.py`, targeted single-module tasks assign work specifically to the relevant arms (Backend API and QA). Non-essential arms remain quiescent, reducing token consumption and preventing cross-arm file contention.
4. **Explicit Parameter and Schema Contracts:**
   - 7B models benefit from unambiguous data models (such as `Todo(id: Optional[int] = None, title: str)`) and explicit reminders to import standard libraries (`time`, `threading`).
5. **Tool Call Parsing & Repair:**
   - `octoflow/arm.py` repairs common JSON syntax errors (such as trailing commas before closing braces/brackets) and converts parse failures into actionable feedback.
