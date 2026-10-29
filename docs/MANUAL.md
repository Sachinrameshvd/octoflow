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
9. [Cockpit Shell Pass-Through & Command Routing Safety](#9-cockpit-shell-pass-through--command-routing-safety)

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
  * `--open`: Automatically opens the primary live service URL in your default browser upon verified readiness (interactive local TTY only; prints URL in non-TTY/SSH). Never opens without this opt-in flag.
  * `--allow-dirty`: Permits running on a dirty working tree by snapshotting uncommitted changes via `git stash create`.
  * `--init-git`: Automatically initializes a git repository if the workspace is not already inside one.
  * `--no-checkpoint`: Runs without git checkpointing (for non-git workspaces or temporary testing).
  * `--dry-run`: Mock execution that writes no project files and creates no checkpoint.
* `./octo ps` (or `octos ps`): Lists active background ignition runtime services (Run ID, service type, PID, PGID, port, URL, and status).
* `./octo stop [run-id] [--all]` (or `octos stop`): Terminates running ignition services via isolated process group signals (`SIGTERM` with 3s grace, escalating to `SIGKILL`), updating registry state to `STOPPED`.
* `./octo undo [run-id]` (or `/undo` / `/rollback` in Cockpit): Safely undoes an OctoFlow run by checking out the original branch and deleting the isolated run branch (`git branch -D` exclusively for branches matching `octoflow/run-*` confirmed by `meta.json`). Restores stashed dirty changes if an allow-dirty snapshot was taken. Never touches other branches, never force-pushes, and never runs `git clean` on user files.
* `./octo runs` (or `octos runs`): Lists recent runs (run ID, goal summary, outcome status, mode, branch, timestamp).
* `./octos ui` (or `/ui`): Launches the 3D WebGL Constellation in your default browser.
* `/open` (Cockpit): Opens the running live application URL in your default browser.
* `/ignite` (Cockpit): Manually provisions and launches runtime services in the current workspace.
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
| `BEGIN PRIVATE KEY (header)` | `PRIVATE_KEY` | `[REDACTED_PRIVATE_KEY_BLOCK]` |
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

---

## 9. Cockpit Shell Pass-Through & Command Routing Safety

The OctoFlow interactive cockpit combines direct shell convenience with strict safety guardrails, protecting against accidental or malicious execution of pasted or misrouted commands without blocking the 20 FPS runner animation.

### 9.1 Input Classification Matrix

All cockpit input is parsed through `octoflow.router.classify_input()` into one of five deterministic route kinds:

| Route Kind | Trigger Criteria | Execution Mode | Confirmation |
| :--- | :--- | :--- | :--- |
| **`SWARM_GOAL`** | Natural language prose, goals starting with non-shell words, or prose arguments (e.g. `make a resume analyzer`, `list the requirements.txt issues`, `touch the code up`) | Dispatched to 8-arm multi-agent swarm conductor | None |
| **`SHELL_SIMPLE`** | Matches allowed shell commands (`mkdir`, `touch`, `ls`, `pwd`, `cat`, `grep`, `which`, `find`, `curl`, `chmod`, `kill`, `ps`, `git`, `cd`, `cp`, `mv`, `rm`, `rmdir`) with non-prose path/flag arguments and no compound operators | `subprocess.run(argv, shell=False, cwd=workspace, timeout=60)` with 64 KB captured output truncation | `y/N` if destructive; none if safe |
| **`SHELL_EXPLICIT`** | Prefixed with `!` or `$` (e.g. `!pytest -q`, `$ ls -l`), `/sh`, `/bash`, or compound commands containing `;`, `&&`, `\|\|`, `\|`, redirects, or subshells | `subprocess.run(command, shell=True, cwd=workspace, timeout=60)` | **Always requires `y/N` confirmation** displaying exact command |
| **`SLASH_COMMAND`** | Prefixed with `/` or matching known cockpit directives (`/help`, `/theme`, `/model`, `screensaver`, `manual`, `clear`, etc.) | In-process cockpit dispatch | None |
| **`EMPTY`** | Blank line or whitespace | No-op, re-prompts | None |

### 9.2 Destructive Command Guardrails (`y/N`)

Destructive commands always trigger a non-blocking confirmation prompt (`⚠ Confirm execution: <cmd> [y/N]: `), defaulting to **No**:
- `rm`, `rmdir`, `mv`
- `cp -r` / `cp -R` / `cp --recursive`
- `chmod -R` / `chmod --recursive`, `chown`, `dd`, `mkfs`
- `sudo` (any command elevated with sudo)
- Destructive Git operations: `git reset --hard`, `git clean`, `git push --force` (`-f`), `git checkout -- .`, `git restore .`, `git branch -D`
- Path traversal containing `..` or absolute paths targeting outside the active workspace

### 9.3 Non-Blocking 20 FPS Confirmation Loop

Confirmation prompts are rendered dynamically in the cockpit using non-blocking key inspection (`select.select` with raw cbreak mode).
- The 20 FPS benthic octopus runner and extruded banner animation continue cycling smoothly without interruption.
- The prompt never invokes blocking `input()` or `console.input()`.
- Striking `y` or `Y` confirms execution. Striking `n`, `N`, `Enter`, `Escape`, or any other key immediately aborts.

### 9.4 Bracketed Paste Protection

- Pasted chunks wrapped in bracketed-paste escape sequences (`\x1b[200~ ... \x1b[201~`) are cleanly inserted into the input buffer for interactive review and are **never auto-submitted**.
- Multi-line pastes display a line count indicator (`[X lines pasted]`) and are treated as a single `SWARM_GOAL` unless explicitly prefixed with `!`.
- Trailing newlines inside pasted blocks do not trigger execution.

### 9.5 In-Process Workspace Navigation (`cd`)

`cd` is handled entirely in-process by mutating the active `workspace` variable after verifying the target path exists and is a directory. The host process `os.chdir()` is never called, strictly isolating cockpit navigation from the runtime environment.

### 9.6 Session History & Deprecated Legacy Escape Hatch

- Executed commands are logged in memory and appended to `~/.octoflow/history` with restricted permissions `0600`.
- **Legacy Fallback:** Setting `OCTOFLOW_LEGACY_ROUTER=1` activates the pre-P1.3 unhardened router. This escape hatch is deprecated and will be removed in a future release.

