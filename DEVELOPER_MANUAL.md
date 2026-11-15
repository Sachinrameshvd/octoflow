# OctoFlow: Developer Runbook & Operational Manual

> **Cephalopod Active Inference Architecture & 3D WebGL Connectome**  
> Complete operational manual for software engineers, ML researchers, and QA evaluators.

---

## Table of Contents
1. [Quick Start (60 Seconds)](#1-quick-start-60-seconds)
2. [System Prerequisites](#2-system-prerequisites)
3. [Repository Architecture](#3-repository-architecture)
4. [Running the 3D WebGL Connectome Showcase](#4-running-the-3d-webgl-connectome-showcase)
5. [Running the Python Swarm Engine & CLI](#5-running-the-python-swarm-engine--cli-octos--octoflow)
6. [Hands-On Demos: Building & Running Real Projects](#6-hands-on-demos-building--running-real-projects)
   - [Demo 1: Autonomous Code Generation from Scratch (Sliding-Window Rate Limiter)](#demo-1-autonomous-code-generation-from-scratch-sliding-window-rate-limiter)
   - [Demo 2: Running the Full Turnkey Application (AI Resume & ATS Match Analyzer)](#demo-2-running-the-full-turnkey-application-ai-resume--ats-match-analyzer)
7. [The 8 Neural Arm Ganglia Roster](#7-the-8-neural-arm-ganglia-roster)
8. [IDE & Agent Integration (Claude Code & Cursor MCP)](#8-ide--agent-integration)
9. [Running Automated Test Suites](#9-running-automated-test-suites)
10. [Troubleshooting & Developer FAQ](#10-troubleshooting--developer-faq)

---

## 1. Quick Start (60 Seconds)

### Launch the 3D WebGL Connectome Showcase:
```bash
cd "showcase copy"
npm install
npm run dev
```
Open **`http://localhost:5174`** in Chrome, Edge, or Safari.

### Run an Autonomous Swarm Simulation (Zero API Key Needed):
```bash
# Return to repository root
cd ..
source .venv/bin/activate
octos run "Build a thread-safe sliding-window rate limiter with tests" --provider mock
```

---

## 2. System Prerequisites

| Component | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Node.js** | `v18.0.0+` | `v20 LTS` or `v22` | Powers Vite 5, Three.js, and TypeScript in `showcase copy/` |
| **npm** | `v9.0.0+` | `v10.0.0+` | Dependency management for WebGL frontend |
| **Python** | `3.10` | `3.12` or `3.14` | Powers the core OctoFlow engine and test harnesses |
| **Git** | `2.30+` | Latest | Required for pre-flight branch checkpoints and `octos undo` |
| **Ollama** | *(Optional)* | Latest | Required only for local private open-weight inference (`qwen2.5-coder:7b`) |

---

## 3. Repository Architecture

```text
Octoflow copy/
├── showcase copy/            # 3D WebGL Interactive Showcase (Port 5174)
│   ├── src/
│   │   ├── connectome/       # Three.js 3D models, shaders, particle systems
│   │   │   ├── ConsortiumSwarm3D.ts       # 8-octopus 64-arm 3D amphitheater
│   │   │   ├── OctopusConnectomeExperience.ts # Central 3D orchestrator
│   │   │   ├── SoundEngine.ts            # Web Audio API ocean waves & sparks
│   │   │   └── CephalopodConnectome3D.ts  # Single 10,480-neuron cephalopod model
│   │   ├── views/
│   │   │   └── ConsortiumConnectomeView.ts # Slides 19-27 overlay & HUD telemetry
│   │   └── main.ts           # 27-slide presentation lifecycle controller
│   └── package.json          # Vite 5 dev server & build scripts
│
├── octoflow/                 # Core Python Multi-Agent Swarm Engine
│   ├── conductor/            # Central Conductor (goal decomposition & routing)
│   ├── ganglia/              # 8 Specialist Arm implementations
│   ├── gates/                # Active inference surprise gating (Delta S)
│   ├── ledger/               # Truthful token accounting receipts
│   ├── safety/               # Secret scanning (12 rules) & git checkpoints
│   └── cli.py                # Command-line entrypoints (octos / octoflow)
│
├── tests/                    # Automated Test Harness
│   ├── test_glyph_policy.py  # Zero-emoji bio-glyph validation
│   ├── test_gate_properties.py # Mathematical gating property proofs
│   └── test_egress_guard.py  # Network quarantine & zero-telemetry tests
│
├── octos                     # Executable CLI shortcut in project root
└── Makefile                  # Build, test, and lockfile automation
```

---

## 4. Running the 3D WebGL Connectome Showcase

The showcase runs independently inside [`showcase copy/`](showcase%20copy/) and visualizes cephalopod active inference in real time.

### Development Server:
```bash
cd "showcase copy"
npm run dev
```
* **Local URL**: `http://localhost:5174`
* **Network URL**: displayed in terminal for multi-device testing.

### Key Interactive Features to Test:
1. **Always-On Ocean Ambience**:
   * The sound engine initializes automatically on the first user interaction (`click`, `keypress`, `wheel`, or `scroll`).
   * Produces an immersive, continuous deep-sea white noise profile generated via procedural Web Audio API synthesizers.
2. **Slide Navigation (27 Slides Total)**:
   * Use the **`Prev`** / **`Next`** buttons in the top-right HUD.
   * Or use keyboard keys: **`Left Arrow` (`←`)** / **`Right Arrow` (`→`)**.
   * Or click **`Auto-Tour`** in the top bar to run an automated, animated walk-through.
3. **Slides 19 through 26: Individual Octopuses 1 to 8**:
   * **`⚡ Spark Octo` Button**: Triggers a high-voltage golden synaptic burst down all 8 arms, accompanied by synchronized flashing status dots on the card.
   * **`SoftDev` / `AI/ML` Toggle**: Instantly reconfigures the octopus role between Software Architecture (APIs, schemas, tests) and AI/ML Research (tensors, training, quantization).
4. **Slide 27: The 8-Octopus Living Swarm**:
   * **Tiered Amphitheater View**: All 8 3D octopuses are positioned in an undulating biological depth formation with zero card occlusion.
   * **`↯ Synaptic Pulse`**: Fires synchronized golden stimulus pulses across all 64 arms and the inter-octopus 3D synaptic cables.
   * **`Free Orbit` Toggle**: Frees the camera controls, allowing complete 360-degree click-and-drag 3D rotation, panning, and zoom around the swarm.
   * **`Software Dev (64 Arms)` vs `AI/ML (64 Arms)`**: Switches global consortium mode across all 8 octopuses simultaneously.
   * **`Executive Dossier →`**: Formats and triggers the printer-ready 1-page PDF technical brief.

### Production Build & Preview:
```bash
cd "showcase copy"
npm run build
npm run preview
```

---

## 5. Running the Python Swarm Engine & CLI (`octos` / `octoflow`)

The Python engine operates either as an autonomous CLI orchestrator, an interactive flight cockpit, or an IDE/MCP companion.

### Environment Activation:
```bash
source .venv/bin/activate
```
*(If setting up a fresh environment, run: `make setup` or `pip install -e ".[dev]"`).*

### System Diagnostics (`octos doctor`):
Verify runtime environment, neural assets, git safety, and provider endpoints:
```bash
octos doctor
```

### 1. Free Autonomous Mission (Mock Provider):
Executes the full planning, sensory gating, and test verification cycle without making external API calls or spending tokens:
```bash
octos run "Build a thread-safe sliding-window rate limiter with tests" --provider mock
```

### 2. Local-First Autonomous Mission (Via Ollama):
Executes real LLM code generation locally with 100% data privacy and zero cloud egress:
```bash
# Pull the recommended coding model (requires Ollama running):
ollama pull qwen2.5-coder:7b

# Execute mission:
octos run "Build a rate limiter with unit tests" --model ollama
```

### 3. Cloud Provider Execution (Anthropic / OpenAI):
```bash
export ANTHROPIC_API_KEY="your-api-key"
octos run "Build a rate limiter with unit tests" --provider anthropic --model claude-3-5-sonnet-20241022
```

### 4. Interactive Terminal Flight Cockpit:
Launch the real-time terminal HUD:
```bash
octos
```
* **Keyboard Shortcuts in Cockpit**:
  * `F1` or `/manual`: Display interactive command manual.
  * `/help`: Display quick command reference.
  * `k` / `j`: Next / previous theme palette.
  * `q` or `/exit`: Clean exit.

### 5. Truthful Token Receipts & Audit:
Every run records exact measured tokens spent versus tokens avoided by sensory reflexes:
```bash
# View last run receipt:
octos receipt

# View calculation methodology:
octos receipt --method

# Inspect specific run ID:
octos receipt 1794049840-56720e
```

### 6. Safety, AST Scanning & Atomic Undo:
```bash
# Scan working tree for syntax errors and 12 secret leak patterns:
octos guard

# Instantly rollback changes to the pre-flight git checkpoint:
octos undo
```

---

## 6. Hands-On Demos: Building & Running Real Projects

### Demo 1: Autonomous Code Generation from Scratch (Sliding-Window Rate Limiter)

This tutorial walks through having OctoFlow autonomously design, implement, and test a thread-safe rate limiter.

#### Step 1: Create a Sandbox Directory & Activate Environment
```bash
source .venv/bin/activate
mkdir -p demo_sandbox && cd demo_sandbox
```

#### Step 2: Deploy OctoFlow Swarm
Run the mission using the built-in mock provider (free simulation) or local Ollama:
```bash
# Free simulation:
../octos run "Build a thread-safe sliding-window rate limiter with tests" --provider mock

# Or with local Ollama:
../octos run "Build a thread-safe sliding-window rate limiter with tests" --model ollama
```

#### Step 3: Understanding the Autonomous Execution Flow
As OctoFlow runs, you will observe the 8-Arm cephalopod coordination in your terminal:
```text
[SWARM] Launching OctoFlow Swarm in SOFTWARE_DEV mode...
[ARM 0] System Architect: defines RateLimiter interface & sliding window contract.
[ARM 2] Backend Core: writes limiter.py (timestamp deques, threading locks, acquire() / allow_request()).
[GATE]  Arm 2: Delta S = 0.78 > theta (Central Escalation: new code generated).
[ARM 5] QA & Invariants: writes test_limiter.py (concurrency stress tests, capacity limits).
[GATE]  Arm 5: Delta S = 0.65 > theta (Central Escalation: test suite registered).
[ARM 5] QA & Invariants: runs pytest test_limiter.py (all tests passing in 0.11s).
[GATE]  Arm 5: Delta S = 0.08 <= theta (Reflex Silenced: tests pass cleanly, 0 tokens wasted!).
[ARM 6] Security Guard: AST safety check and secret scan: 0 leaks, 0 syntax defects.
[SWARM] Quiescence reached: 2 files created, 100% tests passing.
```

#### Step 4: Verify the Generated Artifacts & Run Tests
Inspect the files created by the swarm and run the test suite:
```bash
ls -la
# Run the generated tests directly:
pytest test_limiter.py -v
```

#### Step 5: Audit Token Savings & Rollback
```bash
# Inspect the truthful token receipt:
../octos receipt

# Test atomic git rollback (cleanly restores your folder):
../octos undo
cd ..
```

---

### Demo 2: Running the Full Turnkey Application (AI Resume & ATS Match Analyzer)

The repository includes a complete production-grade web application built entirely across 6 incremental OctoFlow missions, located in [`examples/resume-analyzer/`](examples/resume-analyzer/).

#### What the Application Does:
* **In-Memory PDF Extraction**: Zero disk writes, extracting text and sections via `pypdf`.
* **Skills-Gap Taxonomy Analysis**: Canonical alias normalization (e.g. `k8s` → `kubernetes`, `postgres` → `postgresql`).
* **ATS Gauntlet Scoring**: Multi-factor scoring across keywords, experience alignment, and formatting.
* **FastAPI Backend + Dark-Mode SPA**: Asynchronous REST API and interactive web dashboard.

#### Step 1: Navigate to the Demo Directory
```bash
cd examples/resume-analyzer
```

#### Step 2: Install Runtime Dependencies
```bash
# Using your active virtual environment:
pip install -r requirements.txt
```

#### Step 3: Generate Synthetic Test Resumes
Generate 3 non-PII synthetic sample resumes for demonstration:
```bash
python scripts/generate_samples.py
```
This generates:
* `samples/sample_backend_senior.pdf` (Alex Mercer: Python, FastAPI, Docker, Kubernetes)
* `samples/sample_frontend_mid.pdf` (Jordan Lee: TypeScript, React, Tailwind CSS)
* `samples/sample_data_engineer.pdf` (Samira Khan: Spark, Kafka, AWS, Snowflake)

#### Step 4: Run the Automated Test Suite (26 Tests)
```bash
pytest tests/ -v
```
All 26 unit and integration tests execute in-memory with 0 disk persistence.

#### Step 5: Start the Live Web Application
```bash
uvicorn app:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser.

#### Step 6: Test the Interactive Web UI
1. Drag and drop `samples/sample_backend_senior.pdf` into the upload zone.
2. Paste a target job description (e.g. "Senior Python & FastAPI Engineer with Kubernetes experience").
3. Click **Analyze Resume**.
4. Observe the real-time ATS match score gauge, matched skills badges, missing skills recommendations, and structural breakdown.

#### Step 7: Inspect Real OctoFlow Provenance & Token Receipts
Inspect the immutable records showing how OctoFlow built this application:
```bash
# View the mission receipt showing measured vs avoided tokens:
cat provenance/mission-6-receipt.json
```
*(Total savings across the 6 missions: **41,265 tokens (22.4% reduction)** avoided via sensory gating reflexes).*

---

## 7. The 8 Neural Arm Ganglia Roster

| Arm ID | Title | Specialization & Responsibilities | Core Tools |
| :---: | :--- | :--- | :--- |
| **Arm 0** | **System Architect** | High-level topology, data contracts, schemas, DAG planning | `git_status`, `read_file`, `ast_plan` |
| **Arm 1** | **Database & Schemas** | Migrations, ORM models, SQL integrity, validation schemas | `write_file`, `lint_check`, `sql_validate` |
| **Arm 2** | **Backend Core** | High-throughput APIs, FastAPI/Node routes, business logic | `write_file`, `run_tests`, `typecheck` |
| **Arm 3** | **Frontend & UX** | UI components, design tokens, responsive layouts, WebGL | `write_file`, `vite_build`, `browser_eval` |
| **Arm 4** | **State & Bus** | WebSocket streaming, reactive cache, state machines | `bus_publish`, `cache_invalidate` |
| **Arm 5** | **QA & Invariants** | Pytest suites, test discovery, regression triage, self-heal | `run_pytest`, `ast_patch`, `self_heal` |
| **Arm 6** | **Security & Guard** | Zero-trust PII redaction, secret scanning, credential hygiene | `pii_sanitize`, `secret_scan`, `mtls_auth` |
| **Arm 7** | **DevOps & Docs** | CI/CD pipelines, Dockerfiles, README, telemetry | `docker_build`, `gen_docs`, `telemetry_emit` |

---

## 8. IDE & Agent Integration

### Claude Code CLI Integration (SPARC):
Inject OctoFlow's 8-arm discipline and sensory gating into Anthropic's Claude Code CLI:
```bash
# Auto-configure CLAUDE.md blueprint in target repo:
octos claude init

# Run Claude Code CLI with pre-injected 8-Arm SPARC directives:
octos claude run "Build a rate limiter with unit tests"

# Or generate and copy the SPARC prompt to your clipboard:
octos claude prompt "Build a rate limiter with unit tests" --copy
```

### Model Context Protocol (MCP) Server:
Serve OctoFlow as a local stdio MCP server for Cursor and Claude Code:
```bash
octoflow mcp-serve
```

---

## 9. Running Automated Test Suites

OctoFlow maintains rigorous automated test suites for continuous verification:

```bash
source .venv/bin/activate

# 1. Zero-Emoji Bio-Glyph Audit (Strict compliance with 9/9 passing tests):
pytest tests/test_glyph_policy.py

# 2. Mathematical Sensory Gate Properties (Active inference surprise bounds):
pytest tests/test_gate_properties.py

# 3. Privacy & Network Egress Quarantine (Zero telemetry proofs):
pytest tests/test_egress_guard.py

# 4. Fast Unit Test Suite:
pytest tests/ -m "unit and not pty and not live" -q

# 5. Full Non-Live Test Suite with Coverage:
pytest tests/ -m "not live" --cov=octoflow
```

---

## 10. Troubleshooting & Developer FAQ

### 1. Port 5174 Already in Use
* **Symptom**: `Port 5174 is in use, trying another one...`
* **Resolution**: Terminate any lingering Vite processes:
  ```bash
  lsof -ti:5174 | xargs kill -9
  ```

### 2. Browser Audio Blocked / Silent Ambience
* **Symptom**: Ocean wave audio doesn't play immediately upon page load.
* **Resolution**: Modern browsers require user interaction before activating the Web Audio context. Click anywhere on the page, tap an arrow key, or scroll to engage the sound engine.

### 3. Local Model Memory Exhaustion (Ollama)
* **Symptom**: Ollama responds slowly or aborts with OOM errors.
* **Resolution**: Ensure you are using the optimized 7B parameter quantized model:
  ```bash
  ollama pull qwen2.5-coder:7b
  ```
  For machines with limited VRAM (under 8GB), use the mock provider for algorithmic testing:
  ```bash
  octos run "<goal>" --provider mock
  ```

### 4. Git Lock Conflicts During Ephemeral Runs
* **Symptom**: `fatal: Unable to create '.git/index.lock': File exists.`
* **Resolution**: Check for concurrent git operations and remove stale locks:
  ```bash
  rm -f .git/index.lock
  octos doctor
  ```

