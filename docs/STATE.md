# OctoFlow Repository State & Ground Truth (Phase 1 Handoff)

> **Document Type:** Ground Truth State Synchronization & Handoff  
> **Phase Just Completed:** Phase 1 (Prompts P1.1, P1.2, P1.3, P1.4, P1.5)  
> **Branch:** `octos/state-sync-phase-1`  
> **Verification Standard:** Every factual assertion is marked `[VERIFIED: command or file]` or `[UNVERIFIED]`.

---

## 1. Directory Structure (Two Levels Deep, Annotated)

```text
.
├── CHANGELOG.md               # Keep-a-Changelog log documenting D1 and P1.1–P1.5 [VERIFIED: file]
├── CITATION.cff               # Citation metadata [VERIFIED: file]
├── Dockerfile                 # Root container build definition [VERIFIED: file]
├── LICENSE                    # MIT License file [VERIFIED: file]
├── Makefile                   # Make orchestration (setup, test, visualizer-build, clean) [VERIFIED: file]
├── PROJECT_CONTEXT.md         # Historical Master Context Block [VERIFIED: file]
├── PROJECT_CONTEXT.pdf        # PDF version of initial briefing [VERIFIED: file]
├── README.md                  # Project overview, architecture diagrams, and run matrices [VERIFIED: file]
├── infer.py                   # Root inference entrypoint [VERIFIED: file]
├── octo                       # Shell wrapper launching python -m octoflow.cli [VERIFIED: file]
├── octos                      # Shell wrapper launching python -m octoflow.cli (octos_main) [VERIFIED: file]
├── pyproject.toml             # Pinned dependencies, entry points, and pytest configuration [VERIFIED: file]
├── requirements-dev.txt       # Development dependencies [VERIFIED: file]
├── requirements.txt           # Base package requirements [VERIFIED: file]
├── start.sh                   # Startup wrapper script [VERIFIED: file]
├── test_output.py             # Temporary sandbox sample artifact [VERIFIED: file]
├── train.py                   # Root model training script [VERIFIED: file]
├── api/                       # Lightweight mock REST endpoints [VERIFIED: dir]
│   └── auth.py                # Authentication helper [VERIFIED: file]
├── architecture/              # Architecture diagrams and technical specs [VERIFIED: dir]
│   └── README.md              # 14-component architecture map [VERIFIED: file]
├── backend/                   # Sample FastAPI backend deliverable [VERIFIED: dir]
│   └── main.py                # Deliverable application entrypoint [VERIFIED: file]
├── checkpoints/               # Trained PyTorch weights and neural connectome maps [VERIFIED: dir]
│   ├── best_octopus_brain.pt  # Best evaluation weights [VERIFIED: file]
│   ├── cephalopod_connectome.json # Serialized connectome topology [VERIFIED: file]
│   ├── octopus_brain.onnx     # Quantized ONNX neural weights [VERIFIED: file]
│   ├── smoke_test_model.pt    # Smoke testing temporary weights [VERIFIED: file]
│   ├── test_top1_model.pt     # Evaluation weights [VERIFIED: file]
│   └── top1_octopus_brain.pt  # Production neural weights [VERIFIED: file]
├── deploy/                    # Deployment configurations [VERIFIED: dir]
│   └── Dockerfile             # Production container recipe [VERIFIED: file]
├── docs/                      # Repository documentation and security policies [VERIFIED: dir]
│   ├── BASELINE.md            # P0.1 environment and baseline measurements [VERIFIED: file]
│   ├── MANUAL.md              # In-depth Cephalopod Swarm manual [VERIFIED: file]
│   ├── SECURITY.md            # Tool sandbox security and execution policy [VERIFIED: file]
│   ├── SECURITY_MODEL.md      # Telemetry server & secrets hardening specification [VERIFIED: file]
│   ├── STATE.md               # Phase 1 ground truth handoff document [VERIFIED: file]
│   └── TROUBLESHOOTING.md     # Error taxonomy & provider recovery guide [VERIFIED: file]
├── envs/                      # RL and soft-body simulation environments [VERIFIED: dir]
│   ├── curriculum.py          # Staged learning curriculum [VERIFIED: file]
│   ├── hunting_env.py         # 2D benthic foraging environment [VERIFIED: file]
│   ├── reach_and_avoid.py     # Kinematic obstacle task [VERIFIED: file]
│   ├── render_env.py          # Visual environment renderer [VERIFIED: file]
│   └── soft_body_tentacle.py  # Continuum arm mechanics [VERIFIED: file]
├── experiments/               # Empirical benchmarks and ablation scripts [VERIFIED: dir]
│   ├── baselines.py           # Standard baseline models [VERIFIED: file]
│   ├── export_onnx.py         # ONNX exporter [VERIFIED: file]
│   ├── run_benchmark_suite.py # Benchmark suite runner [VERIFIED: file]
│   └── train.py               # Experiment training loop [VERIFIED: file]
├── frontend/                  # Sample web application deliverable [VERIFIED: dir]
│   ├── index.html             # Web client UI root [VERIFIED: file]
│   └── vite.config.js         # Vite configuration [VERIFIED: file]
├── models/                    # Domain data models [VERIFIED: dir]
│   └── resume_analyzer.py     # Resume analyzer model schema [VERIFIED: file]
├── notebooks/                 # Interactive Jupyter notebooks [VERIFIED: dir]
│   └── octopus_brain_quickstart.ipynb # Interactive tutorial [VERIFIED: file]
├── octoflow/                  # Core OctoFlow framework implementation (33 modules) [VERIFIED: dir]
│   ├── arm.py                 # 8-arm specialist agent implementation [VERIFIED: file]
│   ├── conductor.py           # Central supraesophageal conductor [VERIFIED: file]
│   ├── config.py              # Configuration models & permission hardening [VERIFIED: file]
│   ├── provider.py            # LLM provider cascade & error taxonomy [VERIFIED: file]
│   ├── router.py              # Cockpit input classifier & shell safety [VERIFIED: file]
│   ├── server.py              # Hardened telemetry WebSocket & HTTP server [VERIFIED: file]
│   ├── tools.py               # Sandboxed workspace tools & execution policies [VERIFIED: file]
│   └── dist/                  # Built 3D visualizer web assets [VERIFIED: dir]
├── octopus_brain/             # Biological neural connectome & active inference [VERIFIED: dir]
│   ├── brain.py               # Dual-system neural controller [VERIFIED: file]
│   ├── central.py             # Central ganglion and attention coordinator [VERIFIED: file]
│   ├── connectome.py          # Connectome matrix and synaptic weights [VERIFIED: file]
│   └── trainer.py             # PPO and active-inference trainer [VERIFIED: file]
├── schemas/                   # Data transfer schemas [VERIFIED: dir]
│   └── user.py                # Schema model definitions [VERIFIED: file]
├── task_manager/              # Generated fullstack deliverable demonstration [VERIFIED: dir]
│   ├── docker-compose.yml     # Multi-container service definition [VERIFIED: file]
│   └── requirements.txt       # Service dependencies [VERIFIED: file]
├── tests/                     # Comprehensive test suite (39 test suites) [VERIFIED: dir]
│   ├── test_provider_errors.py# Provider error taxonomy and backoff tests [VERIFIED: file]
│   ├── test_router.py         # Cockpit shell router safety tests [VERIFIED: file]
│   ├── test_run_outcome.py    # Truthful run state tests (Decision D1) [VERIFIED: file]
│   ├── test_server_security.py# Telemetry server & secrets hardening tests [VERIFIED: file]
│   ├── test_tools_security.py # Tool sandbox path confinement tests [VERIFIED: file]
│   └── e2e/                   # End-to-end integration tests [VERIFIED: dir]
└── visualizer/                # 3D WebGL neural connectome visualizer source [VERIFIED: dir]
    ├── index.html             # Visualizer HTML canvas [VERIFIED: file]
    ├── package.json           # Visualizer frontend dependencies [VERIFIED: file]
    ├── tsconfig.json          # TypeScript config [VERIFIED: file]
    └── src/                   # Three.js / WebGL visualization source [VERIFIED: dir]
```
`[VERIFIED: python3 tree walk & ls]`

---

## 2. Module Map (`octoflow/`)

All 33 Python modules under `octoflow/`, ordered by line count:

1. [`octoflow/cli.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/cli.py) (3,499 lines): Typer CLI entrypoint, animated 20 FPS cockpit REPL, doctor diagnostics, and setup wizard. `[VERIFIED: wc -l octoflow/cli.py]`
2. [`octoflow/provider.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/provider.py) (1,523 lines): Multi-LLM provider client, error taxonomy, exponential backoff with jitter, secrets redaction, and cascade pool. `[VERIFIED: wc -l octoflow/provider.py]`
3. [`octoflow/report.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/report.py) (903 lines): Generates standalone self-contained HTML mission audit reports with embedded connectome replay. `[VERIFIED: wc -l octoflow/report.py]`
4. [`octoflow/conductor.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/conductor.py) (780 lines): Central supraesophageal conductor managing task decomposition, 8-arm coordination, and active inference cycles. `[VERIFIED: wc -l octoflow/conductor.py]`
5. [`octoflow/tools.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/tools.py) (733 lines): Hardened `WorkspaceSandbox` enforcing path confinement, command execution allowlist, and timeouts. `[VERIFIED: wc -l octoflow/tools.py]`
6. [`octoflow/router.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/router.py) (645 lines): Cockpit input classifier and safety router for shell commands, swarm goals, and destructive confirmations. `[VERIFIED: wc -l octoflow/router.py]`
7. [`octoflow/themes.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/themes.py) (617 lines): Terminal color palettes, rich styling tokens, and 3D banner animation frame generators. `[VERIFIED: wc -l octoflow/themes.py]`
8. [`octoflow/consortium.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/consortium.py) (612 lines): Multi-cephalopod consortium orchestrating 1 to 8 octopuses (8 to 64 neural arms). `[VERIFIED: wc -l octoflow/consortium.py]`
9. [`octoflow/config.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/config.py) (562 lines): Pydantic configuration models, custom guilds, POSIX file permission hardening, and credential masking. `[VERIFIED: wc -l octoflow/config.py]`
10. [`octoflow/audit.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/audit.py) (522 lines): 100-point 5-dimensional cephalopod architecture readiness and security auditing engine. `[VERIFIED: wc -l octoflow/audit.py]`
11. [`octoflow/arm.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/arm.py) (518 lines): 8-arm specialist agent implementation, tool execution loops, and step outcome evaluation. `[VERIFIED: wc -l octoflow/arm.py]`
12. [`octoflow/ignition.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/ignition.py) (490 lines): Phase 4 Live Ignition auto-detecting deliverables and booting local background services. `[VERIFIED: wc -l octoflow/ignition.py]`
13. [`octoflow/memory.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/memory.py) (385 lines): Vertical lobe long-term synaptic memory with Hebbian learning, LTD decay, and disk persistence. `[VERIFIED: wc -l octoflow/memory.py]`
14. [`octoflow/runner.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/runner.py) (363 lines): Retro 20 FPS Benthic Dot Runner ASCII terminal animation and mini-game. `[VERIFIED: wc -l octoflow/runner.py]`
15. [`octoflow/server.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/server.py) (354 lines): Hardened FastAPI/WebSocket telemetry server with 127.0.0.1 default bind, Origin validation, and Host filtering. `[VERIFIED: wc -l octoflow/server.py]`
16. [`octoflow/eject.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/eject.py) (327 lines): Standalone agent harness ejection generating self-contained scripts for any target repository. `[VERIFIED: wc -l octoflow/eject.py]`
17. [`octoflow/ci.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/ci.py) (305 lines): Automated 3-arm CI/CD GitHub PR review and pre-commit workflow generation. `[VERIFIED: wc -l octoflow/ci.py]`
18. [`octoflow/bench.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/bench.py) (289 lines): Standardized algorithmic challenge benchmark suite for comparing active inference vs baselines. `[VERIFIED: wc -l octoflow/bench.py]`
19. [`octoflow/triage.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/triage.py) (286 lines): Interactive file-by-file git diff triage and patch inspection with AST validation. `[VERIFIED: wc -l octoflow/triage.py]`
20. [`octoflow/federation.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/federation.py) (274 lines): Zero-trust multi-machine agent federation and PII scrub pipeline. `[VERIFIED: wc -l octoflow/federation.py]`
21. [`octoflow/monorepo.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/monorepo.py) (257 lines): Monorepo topology analyzer partitioning packages to 8-arm specialists. `[VERIFIED: wc -l octoflow/monorepo.py]`
22. [`octoflow/healing.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/healing.py) (250 lines): Autonomous closed-loop test repair engine coupling QA (Arm 5) and Backend (Arm 2). `[VERIFIED: wc -l octoflow/healing.py]`
23. [`octoflow/onboarding.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/onboarding.py) (234 lines): 1-command Omni-IDE onboarding injecting `.cursorrules`, `.mcp.json`, and VS Code tasks. `[VERIFIED: wc -l octoflow/onboarding.py]`
24. [`octoflow/gate.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/gate.py) (218 lines): Active inference sensory surprise gating ($\Delta S > \theta$) minimizing LLM invocations. `[VERIFIED: wc -l octoflow/gate.py]`
25. [`octoflow/bus.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/bus.py) (204 lines): Inter-brachial ring communication bus with dynamic clockwise/counter-clockwise fault tolerance. `[VERIFIED: wc -l octoflow/bus.py]`
26. [`octoflow/manual.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/manual.py) (197 lines): Interactive developer terminal manual and chapter browser. `[VERIFIED: wc -l octoflow/manual.py]`
27. [`octoflow/mcp.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/mcp.py) (185 lines): Model Context Protocol (MCP) JSON-RPC 2.0 stdio server for Claude Code and Cursor. `[VERIFIED: wc -l octoflow/mcp.py]`
28. [`octoflow/recorder.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/recorder.py) (179 lines): Terminal session recorder producing standardized Asciinema v2 `.cast` streams. `[VERIFIED: wc -l octoflow/recorder.py]`
29. [`octoflow/theme_selector.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/theme_selector.py) (178 lines): Interactive live theme picker for developer terminal palettes. `[VERIFIED: wc -l octoflow/theme_selector.py]`
30. [`octoflow/outcome.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/outcome.py) (155 lines): Structured execution outcomes (`RunOutcome`, `RunMode`, `RunResult`) and error taxonomy root (`OctoFlowError`). `[VERIFIED: wc -l octoflow/outcome.py]`
31. [`octoflow/encoder.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/encoder.py) (148 lines): Biophysical sensory encoder mapping AST nodes and files into neural embeddings. `[VERIFIED: wc -l octoflow/encoder.py]`
32. [`octoflow/notify.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/notify.py) (125 lines): Webhook notification dispatcher sending formatted mission summary cards to Slack/Discord. `[VERIFIED: wc -l octoflow/notify.py]`
33. [`octoflow/__init__.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/__init__.py) (22 lines): Package metadata, version string (`__version__ = "0.2.0"`), and top-level exports. `[VERIFIED: wc -l octoflow/__init__.py]`

---

## 3. Public CLI Commands & Options

Captured directly from `./octo --help` and `./octo run --help` `[VERIFIED: ./octo --help]`:

### Global Options
- `--host <str>`: Telemetry server bind host (default: `127.0.0.1`).
- `--install-completion`: Install shell completion.
- `--show-completion`: Show shell completion script.
- `--help`: Show CLI help and exit.

### Available Commands
- `run`: Deploy the cephalopod swarm (1 to 8 octopuses • 8 to 64 arms) to execute an objective.
- `consortium`: Deploy the multi-cephalopod consortium (3 to 8 octopuses • 24 to 64 arms) on a project.
- `octopolis`: Deploy the flagship 8-Octopus Octopolis (64 Neural Arms) on an objective (via `./octos`).
- `train`: Shortcut command to run swarm in `aiml_research` morphology.
- `ui`: Launch the 3D Cephalopod Connectome Visualizer bridge on `localhost:8088`.
- `setup`: Launch the interactive OctoFlow Setup Wizard with non-echoing credential input.
- `doctor`: Run OctoFlow environment, port, and provider diagnostics.
- `mcp`: Start OctoFlow as a Model Context Protocol (MCP) JSON-RPC 2.0 stdio server.
- `mcp-serve`: Run OctoFlow as an MCP server for Claude Code and Cursor.
- `guard`: Run pre-commit secret leak and AST syntax verification on staged git files.
- `install-hooks`: Install automated OctoFlow pre-commit hook into `.git/hooks/pre-commit`.
- `init-ide` / `init`: Auto-configure Cursor (`.cursorrules`), Claude (`.claude.json`), VS Code (`tasks.json`), and Git (`hooks`).
- `init-action`: Generate automated OctoFlow Swarm Guard GitHub Action workflow.
- `review-pr`: Execute automated 3-Arm CI/CD PR Review over git diffs.
- `report` / `export`: Generate standalone self-contained HTML mission audit report with interactive replay.
- `heal` / `fix`: Execute autonomous closed-loop test repair with Arm 5 (QA) and Arm 2 (Backend).
- `diff-review` / `triage`: Interactive file-by-file patch inspector and diff triage with AST validation.
- `notify`: Dispatch mission status card to team Slack or Discord webhook.
- `guild`: Manage 8-arm specialist guilds (custom community rosters).
- `bench`: Run standardized 8-arm algorithmic & architectural challenge benchmarks.
- `monorepo`: Scan and partition monorepo packages to specialist 8-arm roles.
- `record`: Launch recorded terminal session producing standard Asciinema v2 `.cast`.
- `audit`: Run 1-100 system readiness and security diagnostic across 5 cephalopod dimensions.
- `eject`: Eject autonomous standalone cephalopod agent harness into any repository.
- `install-claude`: Install and register OctoFlow native Claude Code plugin and slash commands.
- `federation`: Zero-trust multi-machine agent federation and PII redaction pipeline.
- `manual` / `docs`: Display interactive Cephalopod Master Manual and Developer Field Guide.
- `theme`: View or switch the OctoFlow terminal & visualizer theme.
- `banner`: Play the 3D animated OCTOFLOW banner (single replay or continuous loop).
- `screensaver`: Launch continuous ambient 3D banner screensaver until keypress.
- `runner` / `play`: Launch the Chrome Dino-style Benthic Dot Runner game.

### `run` Command Options `[VERIFIED: ./octo run --help]`
- `objective` (Required argument): High-level engineering or research goal for the swarm.
- `--mode, -m <str>`: Swarm mode: `software_dev`, `aiml_research`, `fullstack_ai` (default: `software_dev`).
- `--guild, -g <str>`: Specialist roster/guild name from `~/.octoflow/guilds/`.
- `--model <str>`: LLM backend: `mock`, `anthropic`, `openai`, `ollama` (default: `mock`).
- `--budget, -b <float>`: Hard spending limit in dollars (default: `5.0`).
- `--dir, -d <str>`: Target project workspace folder (default: `.`).
- `--port, -p <int>`: 3D Visualizer telemetry port (default: `8088`).
- `--host <str>`: Telemetry server bind host (default: `127.0.0.1`).
- `--open-ui, --ui`: Auto-open 3D Connectome Visualizer in default browser.
- `--octos, -o <str>`: Count of octopuses: `auto`, `1` (Solo), `3` (Triad), or `8` (Octopolis) (default: `1`).
- `--theme, -t <str>`: Theme palette (`abyssal`, `catppuccin`, `tokyo-night`, `dracula`, etc.).
- `--sandbox, -s <str>`: Execution isolation: `local` (host) or `docker` (containerized) (default: `local`).
- `--dry-run`: Run with mock provider, write no project files (exits 0).

---

## 4. Configuration Schema & Storage

- **Schema Location:** `octoflow.config.OctoFlowConfig` in [`octoflow/config.py:L370-424`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/config.py#L370-L424). `[VERIFIED: file]`
- **Persistent User Configuration Path:** `~/.octoflow/config.json`. `[VERIFIED: octoflow/config.py:L316]`
- **Directory Permissions:** `0700` (`rwx------`), auto-hardened on load. `[VERIFIED: octoflow/config.py:L305, test_server_security.py]`
- **File Permissions:** `0600` (`rw-------`), auto-hardened on load. `[VERIFIED: octoflow/config.py:L320, test_server_security.py]`
- **Current Version:** `0.2.0` in [`pyproject.toml:L7`](file:///Users/sachinrk/Desktop/Octoflow%20copy/pyproject.toml#L7) and [`octoflow/__init__.py:L14`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/__init__.py#L14). `[VERIFIED: file]`

---

## 5. Test Inventory & Execution Results

- **Test Execution Command:** `.venv/bin/pytest tests/ -rs -q` `[VERIFIED: command run]`
- **Test Results:** `365 passed, 4 skipped in 55.92s` `[VERIFIED: command output]`
- **Total Test Cases:** `369` executed test cases across `39` test suites. `[VERIFIED: pytest summary]`
- **Skipped Test Rationale:**
  1. `tests/e2e/test_llm_engine.py:2`: Skipped (LLMEngine not implemented in e2e stub).
  2. `tests/e2e/test_resume_analyzer.py:2`: Skipped (octoflow.api not implemented in e2e stub).
  3. `tests/test_resume_analyzer.py:4`: Skipped (AI Resume Analyzer app not in local pythonpath).
  4. `tests/test_e2e_orchestration.py:353`: Skipped (E2E-REAL: Untested because no live Anthropic API key is exported in local shell).

### Test Inventory by Module `[VERIFIED: pytest --collect-only]`
| Test Module | Test Count | Domain / Subsystem Verified |
|---|---|---|
| `tests/test_router.py` | 95 | Cockpit shell router, classification, confirmations, bracketed paste |
| `tests/test_developer_pillars.py` | 30 | Developer pillars, report export, triage, monorepo, audit |
| `tests/test_tools_security.py` | 18 | Tool sandbox path confinement, allowed commands, timeouts (P1.4) |
| `tests/test_phase6_robustness_concurrency.py` | 18 | Concurrency, disk-full, missing credentials, read-only FS |
| `tests/test_server_security.py` | 16 | Telemetry bind address, Origin validation, Host validation, permissions (P1.5) |
| `tests/test_themes_and_cli.py` | 16 | Color themes, banner animation frames, screensaver, CLI direct calls |
| `tests/test_provider_errors.py` | 12 | Provider error taxonomy, backoff, Retry-After, secret redaction (P1.2) |
| `tests/test_audit_eject_federation.py` | 10 | 100-pt audit score, autonomous harness eject, federation PII |
| `tests/test_connectome_and_biophysics.py` | 9 | Connectome matrix, Hodgkin-Huxley conductance, biophysics |
| `tests/test_run_outcome.py` | 8 | Truthful run states, mock fallback removal, exit codes (P1.1, D1) |
| `tests/test_octoflow.py` | 8 | Core active-inference swarm orchestration |
| `tests/test_bus_comprehensive.py` | 8 | Inter-brachial synaptic ring bus broadcast and bypass |
| `tests/test_workspace_sandbox_comprehensive.py` | 8 | Workspace sandbox prefix collisions, advisory file locking |
| `tests/test_shapes_and_grads.py` | 8 | PyTorch tensor shapes, forward/backward gradient flow |
| `tests/test_consortium.py` | 7 | Triad and Octopolis multi-octopus scaling |
| `tests/test_memory_comprehensive.py` | 7 | Vertical lobe memory, LTP/LTD decay, Hebbian weights |
| `tests/test_accurate_biophysics.py` | 6 | Accurate biophysical Hodgkin-Huxley simulation |
| `tests/test_adapter.py` | 6 | LLM sensory adapter layer |
| `tests/test_async_and_mcp.py` | 6 | Async conductor calls and MCP server endpoints |
| `tests/test_blue_brain.py` | 6 | Blue Brain biological connectome comparison |
| `tests/test_lexicon_and_softbody.py` | 6 | Chemical sensation lexicon and soft-body tentacle physics |
| `tests/test_router_characterization.py` | 6 | Characterization tests for prompt prefixes and commands |
| `tests/test_e2e_orchestration.py` | 5 | Deterministic end-to-end task generation with mock LLM |
| `tests/test_hunting_env.py` | 5 | 2D benthic hunting environment dynamics |
| `tests/test_ignition.py` | 5 | Phase 4 Live Ignition auto-booting services |
| `tests/test_losses.py` | 5 | Active inference free energy and surprise loss functions |
| `tests/test_surprise_gate_comprehensive.py` | 5 | Sensory surprise gating monotonicity and nan/inf handling |
| `tests/test_training.py` | 5 | PPO training epochs, GAE estimation, and checkpoints |
| `tests/test_runner.py` | 4 | Retro benthic dot runner frame generation and sprites |
| `tests/test_security_p0_poc.py` | 4 | P0 vulnerability proof-of-concept tests |
| `tests/test_security_remediation_verified.py` | 3 | Verification of P0 security remediations |
| `tests/test_env.py` | 3 | Environment step and reset contracts |
| `tests/test_benchmark_suite.py` | 2 | Benchmark challenge execution |
| `tests/test_coalition.py` | 2 | Dynamic neural coalition extraction |
| `tests/test_curriculum.py` | 2 | Staged learning curriculum steps |
| `tests/test_fault_tolerance.py` | 2 | Ring bus fault tolerance under arm failures |
| `tests/test_resume_analyzer.py` | 1 | Resume analyzer unit verification |
| `tests/e2e/test_resume_analyzer.py` | 1 | E2E resume analyzer verification |
| `tests/e2e/test_llm_engine.py` | 1 | E2E LLM engine stub |
| **Total** | **366 collected (369 test cases)** | **365 Passed, 4 Skipped (0 Failed)** |

- **Test Coverage:** Configured via `pytest-cov` (installed in `.venv`). `[VERIFIED: Makefile:L38, .venv/bin/pytest --version]`

---

## 6. Architectural Decisions Status (D1–D14)

| Decision ID | Description | Status | Evidence (Commit / File) |
|---|---|---|---|
| **D1** | Remove silent fallback to `MockLLMProvider` in live mode; enforce truthful `RunOutcome` (`COMPLETE`/`FAILED`) and exit code 2 on missing/exhausted keys. | **DONE** | Commit `31b1da0`, [`octoflow/conductor.py:L236`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/conductor.py#L236), [`tests/test_run_outcome.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/tests/test_run_outcome.py) `[VERIFIED]` |
| **D2** | Provider error taxonomy (`ProviderAuthError`, `ProviderRateLimitError`, etc.), exponential backoff with `Retry-After`, and zero credential leaks in logs/exceptions. | **DONE** | Commits `b9c0416`, `2730ddd`, `6970512`, [`octoflow/provider.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/provider.py), [`tests/test_provider_errors.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/tests/test_provider_errors.py) `[VERIFIED]` |
| **D3** | Cockpit shell-router safety, pure input classification in `router.py`, confirmation for destructive commands, and paste protection. | **DONE** | Commits `65784ff`, `9115b22`, [`octoflow/router.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/router.py), [`tests/test_router.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/tests/test_router.py) `[VERIFIED]` |
| **D4** | Tool sandbox path confinement (`Path.is_relative_to`), symlink traversal prevention, command allowlist, timeouts (60s/300s), and 64 KB capture truncation. | **DONE** | Commit `f04ad91`, [`octoflow/tools.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/tools.py), [`tests/test_tools_security.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/tests/test_tools_security.py), [`docs/SECURITY.md`](file:///Users/sachinrk/Desktop/Octoflow%20copy/docs/SECURITY.md) `[VERIFIED]` |
| **D5** | Localhost telemetry server security: bind strictly to `127.0.0.1`, WebSocket Origin validation (code 1008), HTTP Host validation (400), payload sanitization, `0700`/`0600` permissions. | **DONE** | Commit `2d192dd`, [`octoflow/server.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/server.py), [`octoflow/config.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/config.py), [`tests/test_server_security.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/tests/test_server_security.py), [`docs/SECURITY_MODEL.md`](file:///Users/sachinrk/Desktop/Octoflow%20copy/docs/SECURITY_MODEL.md) `[VERIFIED]` |
| **D6** | Modularize cockpit TUI: Extract terminal rendering, banner sparkles, and live loop out of `octoflow/cli.py` into dedicated package (P2.1). | **NOT STARTED** | `octoflow/cli.py` is currently 3,499 lines and houses `interactive_cockpit`. `[VERIFIED: wc -l octoflow/cli.py]` |
| **D7** | Typed configuration refactor: strict Pydantic v2 validation without ambient cascade pool pollution (P2.3). | **PARTIALLY STARTED** | `OctoFlowConfig` in `octoflow/config.py` uses Pydantic v2 with `model_post_init` and permission checks, full typed refactor deferred to P2.3. `[VERIFIED: octoflow/config.py]` |
| **D8** | Upgrade `websockets.legacy` to `websockets.asyncio.server` API (P2.7). | **NOT STARTED** | Deferred to P2.7. `[VERIFIED: server.py]` |
| **D9** | Multi-Cephalopod Consortium autoscaling (Solo, Triad, Octopolis). | **DONE** | [`octoflow/consortium.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/consortium.py), tested in [`tests/test_consortium.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/tests/test_consortium.py). `[VERIFIED]` |
| **D10** | AI Resume Analyzer end-to-end deliverable application. | **PARTIALLY STARTED** | Model schema in `models/resume_analyzer.py`; tests in `tests/test_resume_analyzer.py`. `[VERIFIED]` |
| **D11** | Automated PR review & CI/CD workflow generation. | **DONE** | [`octoflow/ci.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/octoflow/ci.py), tested in [`tests/test_developer_pillars.py`](file:///Users/sachinrk/Desktop/Octoflow%20copy/tests/test_developer_pillars.py). `[VERIFIED]` |
| **D12** | Keyring-backed OS secure credential storage (P5.4). | **NOT STARTED** | Deferred to P5.4; currently secured via `~/.octoflow/config.json` with `0600` permissions. `[VERIFIED: octoflow/config.py]` |
| **D13** | Cross-platform POSIX/Windows raw-mode console parity. | **DONE** | Fallback in `octoflow/cli.py` and `octoflow/router.py`. `[VERIFIED]` |
| **D14** | Zero-Emoji typography contract: clean bio-glyphs across all UI and reports. | **DONE** | Standardized across `octoflow/runner.py`, `octoflow/cli.py`, `octoflow/server.py`, `octoflow/report.py`. `[VERIFIED]` |

---

## 7. Open Issues and Code Annotations

- **TODO / FIXME / XXX Search in Python Code:**
  - Ran `grep -rnE "(TODO|FIXME|XXX)" --include="*.py" octoflow/ octopus_brain/ tests/`
  - **Result: 0 occurrences found.** Python source code contains zero `TODO`, `FIXME`, or `XXX` tags. `[VERIFIED: grep command exit code 1]`
- **Bundled Web Assets:**
  - `octoflow/dist/assets/*.js`: Contains `// TODO: implement vectorized pow` inside upstream bundled ONNX-Wasm runtime math routines. `[VERIFIED: grep]`

---

## 8. Discrepancies from Master Context Block (`PROJECT_CONTEXT.md`)

1. **Test Suite Execution & Count:**
   - *MCB Claim:* 153 tests passing across 33 test suites (153 passed, 1 skipped).
   - *Current Reality:* **369 test cases** (`365 passed, 4 skipped in 55.92s`) across 39 test suites. `[VERIFIED: pytest tests/ -rs -q]`
2. **Provider Failover vs Truthful Run Outcomes (Decision D1):**
   - *MCB Claim:* "When all models in `CascadePoolLLMProvider` fail (or throw 401/400 due to bad keys), log a single advisory and fall back to `MockLLMProvider` rather than raising a fatal `RuntimeError`."
   - *Current Reality:* Silent mock fallback in live mode is eliminated. Misconfigured or exhausted providers raise `ProviderExhaustedError`, log configuration hints, sanitize credentials, and exit with code 2. Mock mode is strictly opt-in via `--dry-run`. `[VERIFIED: octoflow/conductor.py:L236, tests/test_run_outcome.py]`
3. **Provider Error Taxonomy (P1.2):**
   - *MCB Claim:* 401/400/429 treated roughly as one class of failure ("hot-swap to next").
   - *Current Reality:* Structured taxonomy (`ProviderAuthError`, `ProviderRateLimitError`, `ProviderTransientError`, `ProviderRequestError`, `ProviderUnavailableError`) with backoff honoring `Retry-After`. Auth errors are never retried. Ollama failures report actionable restart instructions. `[VERIFIED: octoflow/provider.py]`
4. **Cockpit Shell Routing (P1.3):**
   - *MCB Claim:* Router directly passes shell commands to system shell; naive length check on paste.
   - *Current Reality:* Pure input router in `octoflow/router.py`. Destructive shell commands (`rm`, `mv`, `dd`, `sudo`, destructive git, path escapes) trigger interactive non-blocking confirmation. Bracketed-paste blocks auto-execution. `cd` mutates internal workspace state without global `os.chdir()`. Output is truncated at 64 KB. `[VERIFIED: octoflow/router.py, tests/test_router.py]`
5. **Tool Sandbox Enforcement (P1.4):**
   - *MCB Claim:* Basic prefix string check in `_resolve_safe`.
   - *Current Reality:* Strict path resolution preventing `..` traversal, sibling collisions, and symlink escapes (direct and ancestor). Commands run with `shell=False` via parsed argument vectors against `DEFAULT_ALLOWED_COMMANDS`. Configurable timeouts (60s default, 300s max). Controlled environment scrubs API keys. Outputs passed through `redact_secrets()`. `[VERIFIED: octoflow/tools.py, tests/test_tools_security.py]`
6. **Telemetry Server Security (P1.5):**
   - *MCB Claim:* Server binds to `0.0.0.0` or open socket without Origin checks.
   - *Current Reality:* Server binds to `127.0.0.1` by default; WebSocket Origin validation rejects untrusted web origins with close code `1008`; HTTP Host validation blocks DNS-rebinding attacks with status `400`; structural payload sanitization strips prompts, file contents, command outputs, and keys; `~/.octoflow` and `config.json` enforced to `0700` and `0600`. `[VERIFIED: octoflow/server.py, octoflow/config.py, tests/test_server_security.py]`
7. **Package Version:**
   - *MCB Claim:* `version = "1.0.0"`.
   - *Current Reality:* `version = "0.2.0"` in both `pyproject.toml:L7` and `octoflow/__init__.py:L14`. `[VERIFIED: file]`

---

## 9. Standard Commands (Build, Test, Run, Benchmark)

### Build Commands
```bash
# Set up Python virtual environment and install in editable mode
python3 -m venv .venv
.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install -e ".[dev]"
# Or via Makefile:
make setup

# Build 3D visualizer web bundle and copy to package dist
cd visualizer && npm ci && npm run build
cp -R visualizer/dist/* octoflow/dist/
# Or via Makefile:
make visualizer-build
```
`[VERIFIED: Makefile, pyproject.toml]`

### Test Commands
```bash
# Run complete test suite (all 369 test cases)
.venv/bin/pytest tests/ -q

# Run specific Phase 1 security and robustness suites
.venv/bin/pytest tests/test_server_security.py -v
.venv/bin/pytest tests/test_tools_security.py -v
.venv/bin/pytest tests/test_provider_errors.py -v
.venv/bin/pytest tests/test_router.py -v
.venv/bin/pytest tests/test_run_outcome.py -v

# Run pre-commit secret leak and AST syntax guard
./octos guard
```
`[VERIFIED: pytest execution, ./octos guard]`

### Run Commands
```bash
# Launch interactive 20 FPS Cephalopod Cockpit REPL
./octo
# or
./octos

# Deploy headless swarm on an objective in simulation mode (dry-run)
./octo run "Build an AI Resume Analyzer" --model mock --dry-run

# Deploy swarm on an objective using local Ollama (zero cloud cost)
./octo run "Refactor database migrations" --model ollama --dir .

# Launch 3D Connectome Visualizer bridge on localhost:8088
./octo ui

# Run system and provider diagnostics
./octo doctor
```
`[VERIFIED: ./octo --help]`

### Benchmark Commands
```bash
# Run algorithmic 8-arm challenge benchmarks
./octo bench

# Run multi-trial benchmark suite
.venv/bin/python experiments/run_benchmark_suite.py
```
`[VERIFIED: ./octo --help, experiments/run_benchmark_suite.py]`

---

## 10. Master Context Block (MCB) Patch

Exact replacement lines for the designated sections of `PROJECT_CONTEXT.md`:

```markdown
<!-- REPLACEMENT START: SECTION 0 (ACCESS & CONFIDENCE REPORT) -->
- **Command Execution & Verification [VERIFIED IN CODE]:**
  - Pytest test execution: `pytest tests/` executed across 369 test cases (365 passed, 4 skipped in 55.92s).
  - Shell diagnostics: `./octo doctor`, `./octo audit`, and `./octos guard` executed live on Darwin ARM64.
  - Model verification: Local Ollama daemon queried live via `http://localhost:11434/api/tags` confirming `qwen2.5-coder:7b`.
  - Frontend build: `make visualizer-build` executed inside `visualizer/` verifying TypeScript typechecking and Vite bundle generation copied to `octoflow/dist/`.
<!-- REPLACEMENT END: SECTION 0 -->

<!-- REPLACEMENT START: SECTION 1 (PROJECT IDENTITY) -->
- **Current Version:** `0.2.0` [VERIFIED IN CODE: pyproject.toml:L7, octoflow/__init__.py:L14]
<!-- REPLACEMENT END: SECTION 1 -->

<!-- REPLACEMENT START: SECTION 9 (DESIGN DECISIONS & RATIONALE - ITEM 4) -->
4. **Truthful Run States & Mock Fallback Removal (Decision D1):**
   - *Decision:* Removed silent fallback to `MockLLMProvider` in live mode. When API keys fail or are exhausted, the swarm raises `ProviderExhaustedError`, displays actionable hints, sanitizes credentials, and exits with code 2. Mock mode is strictly opt-in via `--dry-run`.
   - *Rationale:* Silent mock fallback created deceptive runs where users believed live code was written when in reality it was simulated. Truthful reporting guarantees fidelity.
5. **Provider Error Taxonomy & Backoff (P1.2 / Decision D2):**
   - *Decision:* Structured hierarchy (`ProviderAuthError`, `ProviderRateLimitError`, `ProviderTransientError`, `ProviderRequestError`, `ProviderUnavailableError`) with backoff honoring `Retry-After`. Bad credentials are never retried.
   - *Rationale:* Prevents hammering endpoints on permanent 401/403 errors while gracefully recovering from transient 429 rate limits.
6. **Cockpit Shell-Router Safety (P1.3 / Decision D3):**
   - *Decision:* Pure input routing in `octoflow/router.py`. Destructive commands (`rm`, `mv`, `dd`, `sudo`, destructive git) trigger interactive non-blocking confirmation. Output truncated at 64 KB.
   - *Rationale:* Protects user systems against accidental execution of pasted destructive scripts while keeping 20 FPS live loop responsiveness.
7. **Tool Sandbox Path Confinement & Timeouts (P1.4 / Decision D4):**
   - *Decision:* `WorkspaceSandbox` validates canonical paths and symlink ancestors against workspace root. Subprocesses execute with `shell=False` against `DEFAULT_ALLOWED_COMMANDS` with 60s default timeout (300s max) and 64 KB capture limits. Environment purges sensitive API keys.
   - *Rationale:* Defense-in-depth isolation preventing filesystem traversal, command injection, and credential inheritance.
8. **Telemetry Server & Secrets Hardening (P1.5 / Decision D5):**
   - *Decision:* Server binds to `127.0.0.1` by default; WebSocket Origin validation rejects untrusted web origins with code 1008; HTTP Host validation blocks DNS-rebinding (400); telemetry payloads strip prompts, files, outputs, and keys; `~/.octoflow` is `0700` and `config.json` is `0600`; setup wizard uses `getpass.getpass()`.
   - *Rationale:* Prevents cross-site WebSocket hijacking from visited websites, eliminates secret leakage over telemetry streams, and protects local credential storage.
<!-- REPLACEMENT END: SECTION 9 -->
```
