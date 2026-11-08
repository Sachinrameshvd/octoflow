# OctoFlow Swarm Debugging & Contributor Inner Loop Guide

This guide details OctoFlow's developer-experience aids for debugging autonomous cephalopod swarm missions, replaying execution traces, diagnosing system health, and running the local development stack.

---

## 1. Structured Execution Traces (`--trace`)

When diagnosing issues or evaluating sensory gating decisions, enable the JSONL execution trace log:

```bash
# Via CLI flag
octoflow run "Build real-time markdown editor" --trace

# Or via environment variable
export OCTOFLOW_TRACE=1
octoflow run "Build real-time markdown editor"
```

### Trace Storage & Security (`0600`)
- **Location:** `~/.octoflow/runs/<run-id>/trace.jsonl` (or `$OCTOFLOW_RUNS_DIR/<run-id>/trace.jsonl`).
- **Permissions:** The trace file is created with mode `0600` (owner read/write only); the enclosing run folder has mode `0700`.
- **Zero-Egress Guarantee:** Trace logs are stored strictly on the local machine and are never uploaded or transmitted to any external server.

### What is Recorded in `trace.jsonl`:
1. **Gate Evaluations (`gate_eval`):** Arm index, role, cognitive cycle, sensory surprise delta ($\Delta S$), reflex threshold ($\theta$), and decision (`reflex` vs. `escalate`).
2. **Tool Calls (`tool_call`):** Arm index, role, tool name (e.g. `write_file`, `run_command`), sanitized arguments, return code, outcome, and elapsed time in milliseconds.
3. **Provider Requests (`provider_request`):** Provider backend (`mock`, `anthropic`, `openai`, `ollama`), model identifier, token counts (`prompt_tokens`, `completion_tokens`, `total_tokens`), latency in milliseconds, and status.
4. **Telemetry Events (`telemetry`):** State transitions, coalition bindings/dissolutions, and arm quiescence.

### Privacy Policy: Prompts are NEVER Logged by Default
By default, `trace.jsonl` contains **zero prompt text** and zero model response text.

If you explicitly need prompts recorded for prompt engineering or offline fine-tuning, you must pass `--trace-prompts`:
```bash
octoflow run "Debug parser" --trace --trace-prompts
```
When `--trace-prompts` is enabled, a visible warning banner is displayed in the terminal. Even with prompts enabled, all credentials (API keys, authorization headers, bearer tokens, private keys) are automatically sanitized using OctoFlow's multi-pattern redactor before writing to disk.

### Sample Trace Excerpt (`trace.jsonl`)
```jsonl
{"timestamp": 1794146568.5591, "event_type": "mission_start", "payload": {"objective": "Test trace recording", "mode": "software_dev", "model": "mock", "dry_run": true, "octos": "1"}}
{"timestamp": 1794146573.2189, "event_type": "tool_call", "payload": {"arm_id": 1, "role": "database", "tool_name": "write_file", "arguments": {"action": "write_file", "path": "reverse_words.py"}, "success": false, "returncode": 1, "elapsed_ms": 0.0, "error": "Could not acquire lock on 'reverse_words.py' for Arm 1"}}
{"timestamp": 1794146573.2201, "event_type": "gate_eval", "payload": {"arm_id": 1, "role": "database", "cycle": 1, "surprise": 0.65, "threshold": 0.5, "decision": "escalate", "tokens_avoided": 0}}
{"timestamp": 1794146573.2245, "event_type": "provider_request", "payload": {"provider": "mock", "model": "mock", "prompt_tokens": 120, "completion_tokens": 45, "total_tokens": 165, "latency_ms": 12.4, "status": "success"}}
{"timestamp": 1794146573.2310, "event_type": "telemetry", "payload": {"event_type": "STEP", "arm_id": 0, "role": "System Architect", "cycle": 1, "summary": "write_file(reverse_words.py): Implemented reverse_words function"}}
{"timestamp": 1794146573.8920, "event_type": "mission_end", "payload": {"outcome": "complete", "execution_time": 4.74}}
```

---

## 2. Deterministic Swarm Replay (`octoflow replay`)

The `octoflow replay` command reproduces a recorded run step-by-step into the terminal as human-readable lines, while concurrently broadcasting telemetry packets to the 3D connectome visualizer bridge.

```bash
# Replay the most recent run
octoflow replay

# Replay a specific run ID
octoflow replay run-1794146568

# Fast-forward replay at 5x speed
octoflow replay latest --speed 5.0

# Instantaneous replay for scripting or terminal inspection
octoflow replay latest --speed 0

# Terminal-only replay without opening/broadcasting to the 3D visualizer
octoflow replay latest --no-visualizer
```

### Replay Terminal Output Format
```text
◈ OctoFlow Replay: Run [run-1794146568] (252 events, speed=1.0x)
• Trace source: /Users/username/.octoflow/runs/run-1794146568/trace.jsonl
• Visualizer bridge: http://127.0.0.1:8088 (ws://127.0.0.1:8088/ws/telemetry)
------------------------------------------------------------------------------
[19:32:48] MISSION START ◈ Mode: software_dev | Objective: Build rate limiter
[19:32:53] TELEMETRY ◈ SWARM_INIT Arm 0 [Cephalopod Core] cycle=1
[19:32:53] TOOL ◈ Arm 1 write_file({"path": "rate_limiter.py"}) -> FAILED (rc=1)
[19:32:53] GATE ● Arm 1 [database] cycle=1 ΔS=0.650 (θ=0.500) -> ESCALATE
[19:32:53] LLM  ◈ mock:mock tokens=165 latency=12.4ms status=success
[19:32:53] TELEMETRY ◈ STEP Arm 0 [System Architect] cycle=1 - Implemented core spec
[19:32:53] MISSION END ◈ Outcome: COMPLETE (elapsed: 4.74s)
------------------------------------------------------------------------------
✔ Replay of run [run-1794146568] completed (252 events rendered).
```

---

## 3. Contributor Inner Loop (`make dev` & `make dev-stop`)

When hacking on the Python core and the 3D WebGL visualizer simultaneously:

```bash
# Start both the Python telemetry server and Vite dev server
make dev

# Check URLs printed in terminal:
# • Telemetry Server:   http://127.0.0.1:8088 (WebSocket on /ws/telemetry)
# • Vite 3D Visualizer: http://localhost:5173 (Hot Module Replacement enabled)

# When finished:
make dev-stop
```

The telemetry server starts with `--dev`, allowing cross-origin WebSocket requests from Vite's local dev server (`http://localhost:5173` and `http://127.0.0.1:5173`) while maintaining strict host DNS-rebinding protection.

---

## 4. Environment Diagnostics & Issue Bug Reports

### Machine-Readable Diagnostics (`doctor --json`)
```bash
octoflow doctor --json
```
Returns a structured JSON payload listing all subsystem statuses (`Python Runtime`, `Git Repository`, `3D Visualizer Dist`, `Telemetry Port 8088`, `Anthropic API`, `OpenAI API`, `Local Ollama`, `Vertical Lobe LTP`, and `ML / Encoder Backend`).

### Redacted Bug Report (`octoflow bugreport`)
Before opening an issue on GitHub, run:
```bash
octoflow bugreport
```
This generates a complete Markdown block ready to copy and paste into GitHub issues:
- System platform, architecture, and Python version
- Git commit hash and branch
- Doctor health summary
- Configuration settings (all keys containing `key`, `secret`, `token`, `password`, or `auth` are replaced with `[REDACTED_CREDENTIAL]`)
- Relevant environment variables (all sensitive values masked)
- Recent 50 log lines (all strings passed through multi-rule secret redactor)

---

## 5. Visual Studio Code Debugging

Pre-configured launch targets and tasks are located in `.vscode/`:

### Debug Configurations (`.vscode/launch.json`):
- **OctoFlow CLI: Run (Dry-run with Trace):** Launches a sample swarm mission in dry-run mode with `--trace` and `--plain` attached to the Python debugger.
- **OctoFlow CLI: Replay Latest Run:** Replays the last recorded trace directly in the integrated terminal.
- **OctoFlow CLI: Doctor Diagnostics:** Runs `octoflow doctor --json`.
- **OctoFlow CLI: Bug Report:** Runs `octoflow bugreport`.
- **Pytest: Fast Unit Tests:** Runs the non-live pytest test suite.

### VS Code Tasks (`.vscode/tasks.json`):
- `make dev` (Start Telemetry + Vite Dev Stack)
- `make dev-stop` (Stop Dev Stack)
- `pytest tests/ -m 'not live' -q` (Run Unit Tests)
- `ruff check . && ruff format --check .` (Lint & Format Check)

---

## 6. Verification Walkthrough: Reproducing a Failed Run via Replay

When a swarm run fails or produces unexpected code:
1. Locate the run ID from the failure ribbon: e.g. `run-1794146568`.
2. Inspect the raw event log:
   ```bash
   cat ~/.octoflow/runs/run-1794146568/trace.jsonl | grep '"event_type": "gate_eval"'
   ```
3. Look for elevated sensory surprise spikes ($\Delta S > \theta$):
   ```text
   GATE ● Arm 1 [database] cycle=1 ΔS=0.650 (θ=0.500) -> ESCALATE
   ```
4. Replay the run step-by-step with `--speed 1.0` while observing the 3D connectome at `http://127.0.0.1:8088`:
   ```bash
   octoflow replay run-1794146568 --speed 1.0
   ```
5. Observe the tool call immediately preceding the escalation:
   ```text
   TOOL ◈ Arm 1 write_file(...) -> FAILED (rc=1): Could not acquire lock on 'reverse_words.py'
   ```
   The trace immediately reveals that Arm 1 failed due to a file contention lock held by Arm 0, prompting sensory escalation to the Supraesophageal Conductor.
