# 🐙 OctoFlow: The Master Cephalopod Manual & Developer Field Guide

Welcome to the official developer manual for **OctoFlow** (OctopusBrain) — the decentralized-centralized cephalopod neural architecture and multi-agent AI harness.

---

## 📑 Table of Contents

1. [Architectural Overview & Biological Principles](#1-architectural-overview--biological-principles)
2. [The 8 Specialized Neural Arm Ganglia](#2-the-8-specialized-neural-arm-ganglia)
3. [Swarm Morphologies: Solo, Triad & Octopolis](#3-swarm-morphologies-solo-triad--octopolis)
4. [Master Command Directory](#4-master-command-directory)
5. [Step-by-Step Developer Playbooks](#5-step-by-step-developer-playbooks)
6. [Zero-Trust Federation & 14-Rule PII Redaction](#6-zero-trust-federation--14-rule-pii-redaction)
7. [Claude Code, Cursor & MCP Server Integration](#7-claude-code-cursor--mcp-server-integration)
8. [Keyboard Shortcuts Cheatsheet](#8-keyboard-shortcuts-cheatsheet)

---

## 1. Architectural Overview & Biological Principles

Unlike traditional LLM harnesses that pass long chat logs through monolithic orchestrators, OctoFlow is modeled on the **Octopus vulgaris** nervous system:

```
                                  ┌───────────────────────────┐
                                  │ SUPRAESOPHAGEAL GANGLION  │
                                  │      (Central Brain)      │
                                  └─────────────┬─────────────┘
                                                │ Dynamic Coalition Binding
                                                ▼
         ┌─────────────────────────────────────────────────────────────────────────────┐
         │                    LATERAL INTER-BRACHIAL NERVE RING                        │
         │  Arm 0 ──── Arm 1 ──── Arm 2 ──── Arm 3 ──── Arm 4 ──── Arm 5 ──── Arm 6 ─── Arm 7 │
         └─────────────────────────────────────────────────────────────────────────────┘
              ▲            ▲            ▲            ▲            ▲            ▲
              │            │            │            │            │            │
       [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop]
```

### The 3 Core Moats:

1. **Active Inference & Sensory Surprise Gating:**
   Each arm runs a predictive forward model $\hat{o}_{t+1}$. Only when sensory surprise exceeds the adaptive threshold $\theta$ ($\Delta S = \frac{1}{D}\|o_t - \hat{o}_t\|^2 > \theta$) does an arm escalate to the central conductor. Routine reflexes are handled locally, cutting token expenditure by **$>80\%$**.
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
| **Arm 7** | **DevOps & Ignition** | Docker, dev server boots, CI/CD actions, rollback | `ignite_servers`, `git_commit`, `rollback` |

---

## 3. Swarm Morphologies: Solo, Triad & Octopolis

OctoFlow dynamically scales based on the objective complexity:

* **Solo (1 Octopus / 8 Arms):** Ideal for lightweight scripts, bug fixes, and single-file refactors.
* **The Triad (3 Octopuses / 24 Arms):** The default multi-agent swarm:
  * **Octopus 0 (Genesis):** Scaffolding, schemas, and package manifests.
  * **Octopus 1 (Engine):** Backend APIs, business logic, and databases.
  * **Octopus 2 (Sentinel):** Fullstack UI mount, visual tests, security, and live ignition.
* **Octopolis (8 Octopuses / 64 Arms):** Enterprise multi-service monorepos and cross-cloud systems.

---

## 4. Master Command Directory

Every command can be executed from the shell (`./octo <command>`) or inside the interactive cockpit (`/<command>`):

### System Health & Governance
* `./octo audit` (or `/audit`): Evaluates project readiness, test coverage, and security on a **1–100 scale** (A+ rating).
* `./octo eject` (or `/eject`): Exports a standalone, zero-dependency agent harness into `./octo-harness`.
* `./octo doctor` (or `/doctor`): Diagnoses Python environment, GPU/MPS acceleration, LLM keys, and node services.
* `./octo guard` (or `/guard`): Pre-commit guard scanning staged files for credentials and AST syntax errors.
* `./octo hooks` (or `/hooks`): Installs auto-guard into `.git/hooks/pre-commit`.

### Swarm Execution & Orchestration
* `./octos run` (or `./octo run "<goal>"`): Deploys the multi-octopus consortium on a specific mission.
* `./octos ui` (or `/ui`): Launches the 3D WebGL Constellation in your default browser.
* `./octo heal` (or `/heal`): Autonomous self-healing test repair loop (Arm 5 QA + Arm 2 Backend).
* `./octo triage` (or `/triage`): File-by-file interactive diff inspector with AST error triage.
* `./octo plan "<goal>"` (or `/plan <goal>`): Previews the 8-arm task allocation blueprint before execution.

### Federation & Privacy
* `./octo federation status`: Displays the active 14-rule PII filter and peer node trust levels.
* `./octo federation test-pii`: Interactively tests sample text against credential redaction patterns.

### Interface & Aesthetics
* `./octo theme` (or `/theme`): Interactive 8-palette theme picker (Catppuccin Mocha, Cyberpunk Neon, Tokyo Night, Nord Deep-Sea, Monokai Pro, Synthwave 84, Solarized Dark, Bioluminescent Teal).
* `./octo runner` (or `/runner`): Launches the retro 8-bit benthic dot-matrix runner game.
* `./octo screensaver`: Starts the ambient volumetric 3D extruded banner screensaver.

---

## 5. Step-by-Step Developer Playbooks

### Playbook A: Building a Feature from Scratch
1. Launch cockpit: `./octo`
2. Preview allocation: `/plan Build user authentication with JWT and bcrypt`
3. Deploy swarm: Type your prompt and press `Enter`.
4. Watch live 3D synaptic action potentials: Cmd+Click the visualizer link (`http://localhost:8088`).
5. Boot dev server: `/ignite`

### Playbook B: Fixing Failing Unit Tests (`/heal`)
1. Run: `./octo heal`
2. Arm 5 runs `pytest`, captures tracebacks, and identifies the root-cause AST nodes.
3. Arm 2 writes surgical code patches.
4. Arm 5 re-runs `pytest` to confirm convergence.

### Playbook C: Exporting a Standalone Harness to Another Repo
1. Run: `./octo eject --output /path/to/other/repo/agent-harness`
2. Commit the ejected files (`run.py`, `pii_guard.py`, `sensory_gate.py`, `arm_dispatcher.py`).
3. Run directly: `python agent-harness/run.py "Audit and fix security headers"`

---

## 6. Zero-Trust Federation & 14-Rule PII Redaction

OctoFlow automatically scrubs sensitive credentials from all inter-arm, inter-octopus, and cross-machine transmissions:

| Pattern | Rule Name | Action Taken |
| :--- | :--- | :--- |
| `sk-...` (20-60 chars) | `OPENAI_API_KEY` | `[REDACTED_OPENAI_KEY]` |
| `sk-ant-...` (20-80 chars) | `ANTHROPIC_API_KEY` | `[REDACTED_ANTHROPIC_KEY]` |
| `ghp_...` | `GITHUB_TOKEN` | `[REDACTED_GITHUB_TOKEN]` |
| `AKIA...` (16 chars) | `AWS_ACCESS_KEY` | `[REDACTED_AWS_ACCESS_KEY]` |
| `aws_secret_access_key` | `AWS_SECRET_KEY` | `[REDACTED_AWS_SECRET]` |
| `AIza...` (30-42 chars) | `GOOGLE_AI_KEY` | `[REDACTED_GOOGLE_KEY]` |
| `sk_live_...` | `STRIPE_KEY` | `[REDACTED_STRIPE_KEY]` |
| `xoxb-...` | `SLACK_TOKEN` | `[REDACTED_SLACK_TOKEN]` |
| `eyJ...` | `JWT_TOKEN` | `[REDACTED_JWT_TOKEN]` |
| `-----BEGIN PRIVATE KEY-----` | `PRIVATE_KEY` | `[REDACTED_PRIVATE_KEY_BLOCK]` |
| `password=...` | `GENERIC_PASSWORD` | `[REDACTED_SECRET]` |
| Email Addresses | `EMAIL_ADDRESS` | `[REDACTED_EMAIL]` |
| IPv4 Addresses | `IPV4_ADDRESS` | `[REDACTED_IP]` |
| Credit Card Numbers | `CREDIT_CARD` | `[REDACTED_CREDIT_CARD]` |

---

## 7. Claude Code, Cursor & MCP Server Integration

### 1-Command Claude Code Setup:
```bash
./octo install-claude
```
This generates `.claude-plugin/plugin.json`, `.claude-plugin/hooks/hooks.json`, and `.mcp.json`.

Inside Claude Code, you can invoke:
* `/octo` — Launches the cockpit.
* `/octo:audit` — Runs the 1-100 system diagnostic.
* `/octo:swarm` — Deploys the multi-octopus consortium.
* `/octo:heal` — Runs the self-healing repair loop.
* `/octo:eject` — Exports the standalone agent harness.

### Connecting via Stdio MCP Server (Cursor / Claude Desktop):
Add to your `claude_desktop_config.json` or `.mcp.json`:
```json
{
  "mcpServers": {
    "octoflow": {
      "command": "python3",
      "args": ["-m", "octoflow.cli", "mcp-serve"]
    }
  }
}
```

---

## 8. Keyboard Shortcuts Cheatsheet

### In the 3D WebGL Visualizer:
* `?` or `m`: **Open / Close Master Developer Manual Drawer**
* `1` through `8`: Focus camera on Arm 0 through Arm 7
* `Space`: Pause / Resume synaptic transmission animation
* `C`: Reset camera to orbital constellation view
* `T`: Start interactive anatomical tour
* `V`: Toggle voice synthesis audio

### In the Terminal Cockpit:
* `/manual` or `F1`: **Open interactive terminal manual**
* `/help`: Display quick command cheat table
* `k` / `j`: Next / Previous theme in interactive palette picker
* `q` or `/exit`: Exit cleanly
