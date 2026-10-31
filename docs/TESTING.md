# OctoFlow Testing Strategy & Test Pyramid

## 1. Overview and Test Pyramid

OctoFlow adheres to a strict test pyramid designed for velocity, determinism, and zero external runtime dependencies in standard CI runs.

```
                  ▲
                 / \
                /   \     Live Tests (`-m live`)
               /     \    Opt-in, real LLM / network API calls
              /-------\
             /         \   Integration & Security (`-m integration`, `-m security`)
            /           \  Multi-arm orchestration, sandbox boundaries, PTY
           /-------------\
          /               \  Unit & Property Tests (`-m unit`)
         /                 \ Hermetic, in-memory, deterministic, zero I/O (<5s)
        ---------------------
```

### Key Guarantees
1. **Zero External Network Dependencies**: By default, pytest runs with `-m "not live"`. Any accidental attempt to create a network socket in default runs is intercepted and aborted with a clear error.
2. **Sub-30s Fast Feedback**: `make test-fast` executes pure unit tests in under 10 seconds.
3. **Core Module Coverage Floors**: A strict 80% line-coverage floor is enforced on all 9 critical core modules via `scripts/check_coverage.py`.
4. **Flake-Free Execution**: The test suite is resilient to test order randomization.

---

## 2. Pytest Markers

The following markers are registered in `pyproject.toml` and `pytest.ini`:

| Marker | Description | Typical Scope |
| :--- | :--- | :--- |
| `unit` | Hermetic, fast unit tests with zero network or filesystem side-effects. | `test_gate_properties.py`, `test_budget.py`, `test_settings_coverage.py`, `test_provider_coverage.py` |
| `integration` | Tests exercising multiple cooperating subsystems. | `test_consortium.py`, `test_e2e_orchestration.py` |
| `pty` | Tests requiring pseudo-terminal allocation (`pty.openpty()`) or raw interactive input simulation. | `test_router.py::test_pty_*`, `test_errors_logging.py::test_cockpit_silent_logging_through_pty` |
| `live` | Opt-in tests requiring live network access or real LLM cloud APIs. Excluded by default. | Live provider benchmarks, real endpoint probes |
| `integration_local` | Integration tests requiring a loopback server bound to `127.0.0.1`. Permitted by socket guard. | `test_server_security.py`, `test_ignition.py` |
| `characterization`| Parity tests verifying behavioral alignment against golden artifacts. | `test_gate_parity.py` |
| `security` | Confinement, path traversal, injection, permission, and credential redaction tests. | `test_tools_security.py`, `test_security_remediation_verified.py` |
| `slow` | Long-running benchmark or multi-iteration swarm runs (>5s). | Extended stress tests |

---

## 3. Network Isolation & Socket Interception

To guarantee that no test makes real network calls or leaks API costs unintentionally, an autouse fixture in `tests/conftest.py` intercepts `socket.create_connection`.

If a test without the `live` or `integration_local` marker attempts to open a network socket, it immediately fails:

```
RuntimeError: Real network socket connection attempted in hermetic test: ('api.anthropic.com', 443).
Mark test with @pytest.mark.live if real network access is intended,
or @pytest.mark.integration_local if connecting to localhost:127.0.0.1.
```

For tests that spin up temporary local telemetry servers on localhost (127.0.0.1), use the `integration_local` marker:

```python
import pytest

pytestmark = pytest.mark.integration_local
```

---

## 4. Makefile Targets

| Target | Command | Purpose | Duration Budget |
| :--- | :--- | :--- | :--- |
| `make test-fast` | `pytest tests/ -m "unit and not pty and not live" -q` | Fast local developer loop running unit tests. | < 30 seconds (< 5s actual) |
| `make test` | `pytest tests/ -m "not live" --cov=octoflow ... && python scripts/check_coverage.py` | Full test suite excluding live tests + coverage gate. | < 90 seconds |
| `make test-live` | `pytest tests/ -m "live" -q` | Live integration tests with real cloud providers. | As needed |
| `make check-coverage` | `python scripts/check_coverage.py` | Standalone check of coverage floors against `coverage.json`. | Instant |

---

## 5. Coverage Floors & Enforcement

Coverage is measured across the codebase with `--cov=octoflow`. The script `scripts/check_coverage.py` reads `coverage.json` and enforces a strict per-module **80% line coverage floor** on 9 critical components:

1. `octoflow/gate.py`: Surprise calculation, monotonicity properties, threshold adaptation.
2. `octoflow/encoder.py`: Multi-modal AST / file / diff feature extraction.
3. `octoflow/provider.py`: Anthropic, OpenAI, Ollama, Failover, CascadePool, retry backoffs.
4. `octoflow/tools.py`: Workspace confinement, subprocess sandbox, allowlist validation.
5. `octoflow/router.py`: Cockpit classifier, destructive command detection, bracketed paste.
6. `octoflow/settings.py`: Schema validation, defaults, file/env/cli precedence, migrations.
7. `octoflow/outcome.py`: Run states (`COMPLETE`, `PARTIAL`, `FAILED`), truthfulness contracts.
8. `octoflow/budget.py`: Token, call, wall-clock, file, and healing iteration budgets.
9. `octoflow/errors.py`: Error hierarchy, exit code mapping (0, 1, 2, 3, 70), secret redaction.

If any of these modules drops below 80% line coverage, `scripts/check_coverage.py` outputs a detailed diagnostic table and exits with code 1.

---

## 6. Deterministic Replay Cassettes

OctoFlow uses replay cassettes for complex arm and provider interactions to eliminate network latency and nondeterminism.

### How Replay Cassettes Work
- Cassettes store prompt-to-completion mappings or recorded event streams in `tests/characterization/golden/` or JSON cassettes.
- `MockLLMProvider` and `ReplayProvider` read pre-recorded responses matching user prompts or roles.

### How to Add a New Replay Cassette
1. **Create the cassette file**: Place a JSON dictionary or array in `tests/characterization/golden/<name>.json`.
2. **Structure the cassette entries**:
   ```json
   {
     "prompts": {
       "architect": "As the System Architect, I specify module boundaries...",
       "database": "CREATE TABLE sessions (...);"
     }
   }
   ```
3. **Use the cassette in tests**:
   ```python
   from octoflow.provider import MockLLMProvider

   provider = MockLLMProvider()
   provider.script_responses["custom task"] = "Expected response content"
   ```
4. **Assert behavior**: Run the test with `make test-fast`.

---

## 7. Running Live Tests

To execute tests requiring live external services:

1. Export credentials for target providers:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   export OPENAI_API_KEY="sk-..."
   ```
2. Run `make test-live`:
   ```bash
   make test-live
   ```
   Or run specific live tests:
   ```bash
   pytest tests/ -m "live" -v
   ```

---

## 8. Performance Baseline & Regression Testing (P4.3)

OctoFlow tracks key CLI, TUI, and rendering performance metrics to prevent silent latency and CPU regressions:

### 8.1 Performance Measurement Script

The script `scripts/perf_baseline.py` benchmarks and collects:
- **CLI Startup Time:** Wall-clock duration of `octoflow.cli --help` (median of 10 runs).
- **Import Latencies:** Isolated import times for `octoflow` and `octoflow.cli`.
- **Cockpit Idle Metrics:** CPU % and RSS memory sampled over 60 seconds inside a real PTY.
- **Frame Render Time:** p50 and p95 latencies over 600 frames using `build_cockpit_grid`.
- **Visualizer Distribution Size:** Raw and gzipped bundle sizes, with chunk breakdowns.

### 8.2 Usage & Commands

```bash
# Run comprehensive baseline (full 60s idle, 10 help runs, 600 frames)
python scripts/perf_baseline.py --output benchmarks/perf/baseline.json

# Run fast smoke baseline for local testing or CI (< 15s)
python scripts/perf_baseline.py --quick --output benchmarks/perf/baseline.json

# Validate against soft thresholds
python scripts/perf_baseline.py --quick --check-thresholds benchmarks/perf/thresholds.json
```

### 8.3 Soft Performance Thresholds (`benchmarks/perf/thresholds.json`)

| Metric | Soft Ceiling Threshold | Actual Measured (P4.3) |
| :--- | :--- | :--- |
| CLI Help Startup | `< 0.50s` | `0.225s` |
| CLI Module Import | `< 0.40s` | `0.206s` |
| Cockpit Frame Render (p95) | `< 25.0ms` | `0.428ms` |
| Cockpit Idle CPU (median) | `< 15.0%` | `4.30%` |
| Cockpit Idle RSS | `< 150 MB` | `53.4 MB` |

### 8.4 CI Performance Job

A non-blocking informational GitHub Actions workflow job (`perf`) runs `scripts/perf_baseline.py --quick` on pull requests to ensure regressions are caught early without blocking standard test pipelines.

