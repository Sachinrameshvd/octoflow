# OctoFlow: The Master Cephalopod Manual & Developer Field Guide

Welcome to the comprehensive operational manual and developer field guide for **OctoFlow** (OctopusBrain).

---

## Table of Contents

1. [Architectural Overview & Biological Principles](#1-architectural-overview-biological-principles)
2. [The 8 Specialized Neural Arm Ganglia](#2-the-8-specialized-neural-arm-ganglia)
3. [Swarm Morphologies: Solo, Triad & Octopolis](#3-swarm-morphologies-solo-triad-octopolis)
4. [Execution Modes & Truthful Outcomes](#4-execution-modes-truthful-outcomes)
5. [Master Command Directory](#5-master-command-directory)
6. [Interactive Cockpit & Keyboard Shortcuts](#6-interactive-cockpit-keyboard-shortcuts)
7. [Cockpit Shell Pass-Through & Routing Safety](#7-cockpit-shell-pass-through-routing-safety)
8. [Configuration Reference](#8-configuration-reference)
9. [Troubleshooting & Production Field Guide](#9-troubleshooting-production-field-guide)
10. [Terminal Accessibility & Scriptability](#10-terminal-accessibility-scriptability)
11. [Enterprise MetaHarness & Zero-Trust Federation](#11-enterprise-metaharness-zero-trust-federation)
12. [Extensibility: Custom Providers & Custom Guilds](#12-extensibility-custom-providers-custom-guilds)

---

## 1. Architectural Overview & Biological Principles

Unlike traditional LLM harnesses that pass long chat logs through monolithic orchestrators, OctoFlow is modeled on the **Octopus vulgaris** nervous system:

```text
                                  +---------------------------+
                                  | SUPRAESOPHAGEAL GANGLION  |
                                  |      (Central Brain)      |
                                  +-------------+-------------+
                                                | Dynamic Coalition Binding
                                                v
         +-----------------------------------------------------------------------------+
         |                    LATERAL INTER-BRACHIAL NERVE RING                        |
         |  Arm 0 ----- Arm 1 ----- Arm 2 ----- Arm 3 ----- Arm 4 ----- Arm 5 ----- Arm 6 --- Arm 7 |
         +-----------------------------------------------------------------------------+
              ^            ^            ^            ^            ^            ^
              |            |            |            |            |            |
       [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop]
```

### The 3 Core Moats:

1. **Active Inference & Sensory Surprise Gating:**
   Each arm runs a predictive forward model $\hat{o}_{t+1}$. Only when sensory surprise exceeds the adaptive threshold $\theta$ ($\Delta S = \frac{1}{D}\|o_t - \hat{o}_t\|^2 > \theta$) does an arm escalate to the central conductor. Routine reflexes are handled locally, reducing token expenditure by 15-25% on real code generation tasks.
2. **Ring-Topology Lateral Communication:**
   Neighboring arms communicate directly across an inter-brachial message bus using compact semantic tokens without cluttering the central conductor's context window.
3. **Hardware-Accelerated 3D WebGL Connectome:**
   Synaptic action potentials, neurotransmitter flows (ACh, GABA, Glutamate), and arm coalitions are streamed live over WebSockets to an interactive Three.js visualizer.

---

## 2. The 8 Specialized Neural Arm Ganglia

Each octopus operates 8 peripheral ganglia, each with egocentric sensory receptive fields:

| Arm ID | Title | Specialization & Capabilities | Primary Tools |
| :---: | :--- | :--- | :--- |
| **Arm 0** | **System Architect** | High-level topology, data contracts, schemas, DAG planning | `git_status`, `read_file`, `ast_plan` |
| **Arm 1** | **Database & Schemas** | Migrations, ORM models, SQL integrity, validation schemas | `write_file`, `lint_check`, `sql_validate` |
| **Arm 2** | **Backend Core** | High-throughput APIs, FastAPI/Node routes, business logic | `write_file`, `run_tests`, `typecheck` |
| **Arm 3** | **Frontend & UX** | UI components, design tokens, responsive layouts, Three.js | `write_file`, `vite_build`, `browser_eval` |
| **Arm 4** | **State & Bus** | WebSocket streaming, reactive cache, state machines | `bus_publish`, `cache_invalidate` |
| **Arm 5** | **QA & Invariants** | Pytest suites, test discovery, regression triage, self-heal | `run_pytest`, `ast_patch`, `self_heal` |
| **Arm 6** | **Security & Guard** | Zero-trust PII redaction, secret scanning, credential hygiene | `pii_sanitize`, `secret_scan`, `mtls_auth` |
| **Arm 7** | **DevOps & Docs** | CI/CD pipelines, Dockerfiles, README, telemetry | `docker_build`, `gen_docs`, `telemetry_emit` |

---

## 3. Swarm Morphologies: Solo, Triad & Octopolis

Depending on project scope and mission complexity, OctoFlow scales across three distinct organizational tiers:

* **Solo (1 Octopus, 8 Arms):** Targeted features, bug fixes, algorithmic modules, and CLI scripts.
  ```bash
  octoflow run "Build a thread-safe sliding-window rate limiter" --model ollama
  ```
* **Triad (3 Octopuses, 24 Arms):** Full-stack web applications with decoupled concerns:
  * *Octopus A (Core):* Database schema, migrations, data integrity.
  * *Octopus B (Services):* REST API endpoints, business logic, authentication.
  * *Octopus C (Frontend):* Responsive UI components, state management, client tests.
  ```bash
  octoflow run "Build a real-time collaborative workspace" --octos 3
  ```
* **Octopolis (8 Octopuses, 64 Arms):** Distributed microservices, monorepos, and high-concurrency systems.
  ```bash
  octoflow run "Build an enterprise multi-tenant analytics platform" --octos 8
  ```

---

## 4. Execution Modes & Truthful Outcomes

OctoFlow enforces strict truthfulness in status reporting: a run **never** reports success unless real work was executed and files were committed to the active workspace. Silent mock fallback in live environments has been eliminated.

### Execution Modes

| Mode | Flag | Provider Behavior | Filesystem Target | Exit Code |
| :--- | :--- | :--- | :--- | :--- |
| **LIVE** | *(default)* | Real LLM APIs (Ollama, Anthropic, OpenAI). Missing keys fail immediately with actionable guidance. | Workspace directory (`--dir`) | `0` (Success), `1` (Partial), `2` (Failed) |
| **DRY-RUN** | `--dry-run` | Safe mock provider (`MockLLMProvider`). Displays prominent text-only badge. | Redirected to `.octoflow/dry-run/` (workspace unmodified) | `0` (Clean simulation) |

### Exit Code Contract

* **`0` (Complete / Dry-Run):** The swarm reached quiescence ($\ge 6$ arms quiescent) and modified files in LIVE mode, or completed a `--dry-run` simulation without error.
* **`1` (Partial):** Incomplete run (e.g. $< 6$ arms quiescent or interrupted execution).
* **`2` (Failed / Exhausted):** All real providers exhausted, invalid/missing API credentials, or the model produced 0 file modifications in LIVE mode.
* **`3` (Usage Error):** Invalid command-line arguments or syntax.

---

## 5. Master Command Directory

### Core Commands
* `octoflow run "<goal>"` — Deploy the multi-agent swarm to execute an objective.
* `octoflow setup` — Interactive configuration wizard (model selection, API credentials, OS keyring).
* `octoflow ui` — Launch the local 3D Cephalopod Connectome Visualizer bridge (`127.0.0.1:8088`).
* `octoflow mcp-serve` — Run OctoFlow as a Model Context Protocol (MCP) stdio server for Claude Code and Cursor.
* `octoflow receipt [run-id]` — Display truthful token receipts and gate savings.
* `octoflow replay <run-id>` — Replay execution trace into the 3D visualizer and terminal.
* `octoflow undo` — Revert the last swarm mission: restore git state and pre-flight branch.
* `octoflow runs` — List recent swarm execution runs and git provenance status.
* `octoflow doctor [--json]` — Diagnostic verification of environment, models, and network boundaries.
* `octoflow bugreport` — Generate sanitized Markdown system diagnostic report for issue tracking.

### Developer & CI Commands
* `octoflow review-pr [--summary|--shadow]` — Execute automated 3-Arm CI/CD PR review over git diffs.
* `octoflow heal` — Autonomous closed-loop test diagnostic and self-repair loop.
* `octoflow triage` — Interactive file-by-file AST patch inspection and diff triage.
* `octoflow guard` — Verify staged git files for credential leaks and syntax errors.
* `octoflow install-hooks` — Install pre-commit secret and AST verification git hooks.
* `octoflow purge [--dry-run|--yes]` — Safely delete local logs, run caches, and checkpoints.

---

## 6. Interactive Cockpit & Keyboard Shortcuts

Launch the full-screen terminal cockpit with `./octos` or `octoflow ui`:

### In the 3D WebGL Visualizer:
* `?` or `m`: Open / close Master Developer Manual drawer
* `1` through `8`: Focus camera on Arm 0 through Arm 7
* `Space`: Pause / resume synaptic transmission animation
* `C`: Reset camera to orbital constellation view
* `T`: Start interactive anatomical tour
* `V`: Toggle voice synthesis audio

### In the Terminal Cockpit:
* `/manual` or `F1`: Open interactive terminal manual
* `/help`: Display quick command cheat table
* `k` / `j`: Next / previous theme in interactive palette picker
* `q` or `/exit`: Clean exit

---

## 7. Cockpit Shell Pass-Through & Routing Safety

All cockpit input is parsed through `octoflow.router.classify_input()` into one of five deterministic route kinds:

| Route Kind | Trigger Criteria | Execution Mode | Confirmation |
| :--- | :--- | :--- | :--- |
| **`SWARM_GOAL`** | Natural language prose, goals starting with non-shell words, or prose arguments | Dispatched to 8-arm multi-agent swarm conductor | None |
| **`SHELL_SIMPLE`** | Matches allowed shell commands (`mkdir`, `touch`, `ls`, `pwd`, `cat`, `grep`, `which`, `find`, `curl`, `chmod`, `kill`, `ps`, `git`, `cd`, `cp`, `mv`, `rm`, `rmdir`) | `subprocess.run(argv, shell=False, cwd=workspace)` with 64 KB captured output truncation | `y/N` if destructive; none if safe |
| **`SHELL_EXPLICIT`** | Prefixed with `!` or `$` (e.g. `!pytest -q`, `$ ls -l`), `/sh`, `/bash`, or compound operators (`;`, `&&`, `\|\|`, `\|`, redirects) | `subprocess.run(command, shell=True, cwd=workspace)` | **Always requires `y/N` confirmation** |
| **`SLASH_COMMAND`** | Prefixed with `/` or matching known cockpit directives (`/help`, `/theme`, `/model`, `screensaver`, `manual`, `clear`) | In-process cockpit dispatch | None |
| **`EMPTY`** | Blank line or whitespace | No-op, re-prompts | None |

### Destructive Guardrails
Destructive commands always trigger a non-blocking confirmation prompt (`Confirm execution: <cmd> [y/N]: `), defaulting to **No**:
* `rm`, `rmdir`, `mv`, `cp -r`, `chmod -R`, `chown`, `dd`, `mkfs`, `sudo`
* Destructive git actions: `git reset --hard`, `git clean`, `git push --force`, `git checkout -- .`, `git branch -D`
* Path traversal containing `..` or absolute paths targeting outside the active workspace

---

## 8. Configuration Reference

OctoFlow reads configuration from environment variables, OS Keyring, and `~/.octoflow/config.json`. See [`.env.example`](../.env.example) for a pre-populated template with safe placeholders.

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `OCTOFLOW_MODEL_PROVIDER` | `string` | `ollama` | Primary LLM inference engine (`ollama`, `anthropic`, `openai`, `mock`, `fake`, `custom`). |
| `OCTOFLOW_MODEL_NAME` | `string` | `qwen2.5-coder:7b` | Model identifier dispatched to provider. |
| `ANTHROPIC_API_KEY` | `string` | _None_ | Anthropic Claude API token for reasoning arms. |
| `OPENAI_API_KEY` | `string` | _None_ | OpenAI API token for auxiliary arms. |
| `OCTOFLOW_OLLAMA_URL` | `string` | `http://localhost:11434` | Endpoint for local airgapped open weights models. |
| `OCTOFLOW_SURPRISE_THRESHOLD` | `float` | `0.45` | Sensory surprise gate threshold $\theta \in [0.0, 1.0]$. Lower = more verbose reports; Higher = greater token savings. |
| `OCTOFLOW_SANDBOX_MODE` | `string` | `workspace` | Execution sandbox (`workspace` or `docker`). Degrades cleanly to `workspace` if Docker is unavailable. |
| `OCTOFLOW_TELEMETRY_PORT` | `int` | `8088` | WebSocket broadcaster port for real-time 3D visualizer. |
| `OCTOFLOW_LOG_LEVEL` | `string` | `INFO` | Swarm logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `OCTOFLOW_PII_SCRUB` | `bool` | `true` | Enables zero-trust 12-rule regex redaction for all logs, bus messages, and telemetry. |
| `OCTOFLOW_TOKEN_BUDGET` | `int` | `100000` | Maximum token ceiling for live API missions to prevent runaway costs. |
| `OCTOFLOW_TRACE` | `bool` | `false` | Enable deterministic JSONL execution trace logging to `~/.octoflow/runs/<id>/trace.jsonl` (0600). |

---

## 9. Troubleshooting & Production Field Guide

### 1. PyTorch 2.6+ `weights_only=True` Deserialization
* **Symptom:** `torch.load` fails with `pickle.UnpicklingError: Weights only load failed.` when loading `.pt` models.
* **Root Cause:** PyTorch 2.6+ defaults `weights_only=True` for security against arbitrary code execution, rejecting custom dataclass globals.
* **Fix:** Whitelist configuration dataclasses using `torch.serialization.add_safe_globals([OctopusBrainConfig, EnvConfig])` or instantiate fresh configs when inspecting model state dictionaries.

### 2. Provider API Key Absent / Ambient Config Cascade
* **Symptom:** Running tests or local commands raises `AuthenticationError` or attempts to query remote endpoints without credentials.
* **Root Cause:** Missing API key in environment or config.
* **Fix:** Run with local Ollama (`--model ollama`), use `--dry-run` simulation, or configure keys with `octoflow setup`.

### 3. Port Conflicts on Telemetry Server (`8088` / `5173`)
* **Symptom:** WebSocket bridge fails to bind on `127.0.0.1:8088`.
* **Fix:** Specify an alternative port: `octoflow ui --port 8090`, or terminate stale background sessions with `make dev-stop`.

### 4. Git Lock Conflicts in Ephemeral Runs
* **Symptom:** `fatal: Unable to create '.git/index.lock': File exists.`
* **Fix:** Verify no concurrent git commands are executing, run `octoflow doctor` to inspect git status, or safely remove stale lock files.

---

## 10. Terminal Accessibility & Scriptability

* **Zero-Emoji Policy:** All active terminal glyphs have verified single display width (`wcwidth == 1`) with ASCII fallbacks to eliminate grid misalignment.
* **NO_COLOR Standard:** Respects the `NO_COLOR` environment variable and `--no-color` flag (0 ANSI escape sequences).
* **Pure ASCII Mode:** Force strictly 7-bit ASCII (`ord < 128`) output via `--ascii` or `OCTOFLOW_ASCII=1`.
* **Static Mode:** Disable continuous animations via `--no-anim` or `OCTOFLOW_ANIM=0` (redraws only on input).
* **Scriptable Plain & JSON Output:** Stream line-by-line events via `--plain`, or export machine-readable results via `--json`.
* **Narrow Terminal Support:** Automatically scales down to a compact 1-line HUD below 60 columns or 15 rows, supporting dynamic window resizing (`SIGWINCH`) without crashing.

For complete developer guidelines, see the [Terminal Accessibility Guide](accessibility.md).

---

## 11. Enterprise MetaHarness & Zero-Trust Federation

* **Readiness & Security Audit (`octoflow audit`):** Scores your workspace across Code Hygiene, Test Density, Security Sandboxing, Active Inference Readiness, and Swarm Integration.
* **Standalone Harness Ejection (`octoflow eject`):** Exports an autonomous, zero-dependency multi-agent harness into any repository.
* **Native Claude Code Plugin (`/octo`):** Install slash commands and lifecycle hooks directly inside Claude Code with `octoflow install-claude`.
* **Zero-Trust Federation & Redaction:** Intercepts OpenAI/Anthropic/AWS/GitHub keys, tokens, JWTs, passwords, and private keys before outbound transmission.

---

## 12. Extensibility: Custom Providers & Custom Guilds

* **Custom Providers:** Implement `BaseLLMProvider` and register via `octoflow.register_provider("name", ProviderClass)`. Contract verified via `ProviderContractSuite`. See [Extending with Custom Providers](extending/providers.md).
* **Custom 8-Arm Guilds:** Define declarative, domain-tailored 8-arm specialist rosters in validated JSON files without writing Python code. See [Custom Guilds Guide](extending/guilds.md).
* **Model Context Protocol (MCP):** Connect to Cursor and Claude Code via `octoflow mcp-serve`. See [MCP Integration Guide](integrations/mcp.md).
