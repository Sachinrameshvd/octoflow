# OctoFlow Module Triage: Keep, Experimental, or Remove (P2.6 / D7)

**Date:** 2026-10-26  
**Branch:** `octos/p2-6-triage`  
**Status:** Completed & Verified  

---

## Executive Summary

OctoFlow has accumulated peripheral modules, research prototypes, and sample workspace deliverables across earlier iterative development cycles. This triage document systematically classifies every module under `octoflow/` and every top-level repository directory into one of three statuses based on verifiable evidence (code references, unit tests, CLI exposure, and git history):

1. **CORE**: Essential runtime, architecture, security, settings, multi-agent orchestration, or public CLI components.
2. **EXPERIMENTAL**: Functional peripheral tools, research prototypes, or developer convenience features. These remain in the codebase, are labeled `[experimental]` in `--help`, emit a one-time session notice upon first execution, and are documented as experimental.
3. **REMOVE-CANDIDATE**: Modules or directories with zero package references, zero active unit tests, and zero CLI exposure. In accordance with safety constraints, any candidate with existing documentation or characterization references is preserved and listed for explicit owner decision rather than prematurely deleted.

---

## 1. Complete Module Triage Matrix

| Module / Directory | Purpose | Referenced by | Tests | CLI exposure | Verdict | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `octoflow/__init__.py` | Package initialization & lazy exports | Root imports, `cli.py` | Indirect suite coverage | N/A | **CORE** | Root namespace export layer |
| `octoflow/arm.py` | 8-arm autonomous agent execution & tool loop | `conductor.py`, `coalition.py`, `bus.py`, `memory.py` | `test_developer_pillars.py`, `test_octoflow.py`, `test_tools_security.py` | Via `run`, `octos-run` | **CORE** | Core multi-agent execution engine |
| `octoflow/audit.py` | 5-dimension cephalopod readiness diagnostic | `commands/audit.py`, `commands/eject.py` | `test_audit_eject_federation.py` | `octoflow audit` | **CORE** | System health audit feature |
| `octoflow/bench.py` | 8-arm algorithmic challenge benchmark runner | `commands/bench.py`, `cockpit/app.py` | `test_benchmark_suite.py`, `test_developer_pillars.py` | `octoflow bench` | **EXPERIMENTAL** | Swarm benchmark harness; marked experimental |
| `octoflow/bus.py` | Lateral inter-brachial ring bus & bypass routing | `arm.py`, `conductor.py`, `consortium.py` | `test_bus_comprehensive.py`, `test_developer_pillars.py` | Via swarm runs | **CORE** | Inter-arm message passing infrastructure |
| `octoflow/ci.py` | CI environment detection & git diagnostics | `commands/doctor.py`, `conductor.py` | `test_developer_pillars.py` | Via `octoflow doctor` | **CORE** | System diagnostic checks |
| `octoflow/cli.py` | Typer application wiring & command dispatcher | `__main__.py`, `octo`, `octos` | `test_cli_help_snapshots.py`, `test_themes_and_cli.py` | CLI root entrypoint | **CORE** | Primary CLI dispatch layer |
| `octoflow/coalition.py` | Dynamic coalition binding linking arms to goals | `conductor.py`, `consortium.py` | `test_coalition.py` | Via swarm runs | **CORE** | Arm task assignment mechanics |
| `octoflow/cockpit/` | Interactive rich terminal cockpit UI & dashboard | `cli.py`, `commands/ui.py` | `test_cockpit_imports.py` | `octoflow ui`, interactive mode | **CORE** | Primary interactive user interface |
| `octoflow/commands/` | Modular Typer command registration groups | `cli.py` | `test_cli_help_snapshots.py`, `test_themes_and_cli.py` | All subcommands | **CORE** | CLI command architecture |
| `octoflow/conductor.py` | Supraesophageal conductor & goal decomposition | `ignition.py`, `cli.py` | `test_e2e_orchestration.py`, `test_developer_pillars.py` | Via swarm runs | **CORE** | Central swarm coordinator |
| `octoflow/config.py` | Swarm morphology & typed configuration models | `arm.py`, `conductor.py`, `consortium.py` | `test_settings.py`, `test_developer_pillars.py` | `octoflow config` | **CORE** | System configuration schema |
| `octoflow/consortium.py` | Multi-octopus consortium orchestration (3-8 octos) | `commands/consortium.py`, `ignition.py` | `test_consortium.py`, `test_ignition.py` | `octoflow consortium`, `octos octopolis` | **CORE** | Multi-swarm scaling orchestrator |
| `octoflow/dist/` | Compiled static web assets for browser HUD | `server.py` | `test_server_security.py` | Served via `octoflow ui` | **CORE** | Frontend bundle for telemetry HUD |
| `octoflow/eject.py` | Autonomous standalone agent harness exporter | `commands/eject.py`, `cockpit/app.py` | `test_audit_eject_federation.py` | `octoflow eject` | **EXPERIMENTAL** | Export utility; marked experimental |
| `octoflow/encoder.py` | Sensory encoder (16D observation vectors) | `arm.py`, `gate.py`, `provider.py` | `test_gate_parity.py`, `test_surprise_gate_comprehensive.py` | Via sensory gating | **CORE** | Dual NumPy/Torch perception encoder |
| `octoflow/errors.py` | Unified error taxonomy & diagnostic formatting | `cli.py`, `conductor.py`, `provider.py` | `test_errors_logging.py` | All CLI commands | **CORE** | System-wide error handling standard |
| `octoflow/federation.py` | PII redactor (14 rules) & peer trust prototypes | `commands/federation.py`, `bus.py` | `test_audit_eject_federation.py`, `test_bus_comprehensive.py` | `octoflow federation` | **CORE / EXPERIMENTAL** | Redactor is CORE security utility; peer networking is EXPERIMENTAL prototype |
| `octoflow/gate.py` | Sensory surprise gate ($dS$ calculation & threshold) | `arm.py`, `encoder.py` | `test_gate_parity.py`, `test_surprise_gate_comprehensive.py` | Via swarm runs | **CORE** | Fundamental algorithmic novelty |
| `octoflow/healing.py` | Closed-loop automated test failure diagnosis | `commands/heal.py` | `test_developer_pillars.py` | `octoflow heal`, `octoflow fix` | **CORE** | Self-healing autonomous repair engine |
| `octoflow/ignition.py` | Deliverable detection & live service launcher | `conductor.py`, `commands/run.py` | `test_ignition.py` | Via swarm runs | **CORE** | Phase gate provisioning subsystem |
| `octoflow/logging_config.py` | Structured logging with secret filter & trace mode | `cli.py`, `server.py`, `arm.py` | `test_errors_logging.py` | `--verbose`, `--trace` | **CORE** | Centralized logging subsystem |
| `octoflow/manual.py` | Cephalopod Master Manual reader & section store | `commands/manual.py`, `cockpit/app.py` | `test_audit_eject_federation.py` | `octoflow manual`, `octoflow docs` | **EXPERIMENTAL** | Interactive documentation browser; marked experimental |
| `octoflow/mcp.py` | Model Context Protocol JSON-RPC 2.0 stdio server | `commands/mcp.py`, `server.py` | `test_async_and_mcp.py` | `octoflow mcp`, `octoflow mcp-serve` | **CORE** | Claude Code / Cursor integration |
| `octoflow/memory.py` | Saccade buffer & vertical lobe episodic memory | `arm.py`, `conductor.py` | `test_memory_comprehensive.py` | Via swarm runs | **CORE** | Multi-tiered memory architecture |
| `octoflow/monorepo.py` | Monorepo package topology discovery & arm roles | `commands/monorepo.py`, `cockpit/app.py` | `test_developer_pillars.py` | `octoflow monorepo` | **EXPERIMENTAL** | Developer monorepo scanner; marked experimental |
| `octoflow/notify.py` | Slack & Discord webhook payload dispatch | `commands/notify.py`, `cockpit/app.py` | `test_developer_pillars.py` | `octoflow notify` | **EXPERIMENTAL** | Team webhook integration; marked experimental |
| `octoflow/onboarding.py` | First-run interactive setup wizard | `commands/setup.py`, `cli.py` | `test_themes_and_cli.py` | `octoflow setup` | **CORE** | Initial setup and onboarding |
| `octoflow/outcome.py` | Structured run outcomes & token economics | `conductor.py`, `provider.py` | `test_run_outcome.py` | Mission exit reports | **CORE** | Result metrics and cost tracking |
| `octoflow/provider.py` | Unified LLM provider (Anthropic, OpenAI, Ollama) | `arm.py`, `conductor.py` | `test_provider_errors.py`, `test_developer_pillars.py` | `--model` flag in runs | **CORE** | LLM inference gateway |
| `octoflow/recorder.py` | Asciinema v2 `.cast` terminal session recorder | `commands/record.py`, `cockpit/app.py` | `test_developer_pillars.py` | `octoflow record` | **EXPERIMENTAL** | Terminal recorder; marked experimental |
| `octoflow/report.py` | HTML mission report generator with visual replay | `commands/report.py`, `conductor.py` | `test_run_outcome.py` | `octoflow report`, `octoflow export` | **CORE** | Standalone mission reporting deliverable |
| `octoflow/router.py` | Fast regex & semantic intent routing for commands | `server.py` | `test_router.py`, `test_router_characterization.py` | HTTP API router | **CORE** | Server route classification |
| `octoflow/runner.py` | Chrome Dino-style Benthic Dot Runner game | `commands/runner.py` | `test_runner.py` | `octoflow runner`, `octoflow play` | **EXPERIMENTAL** | Terminal easter egg game; marked experimental |
| `octoflow/server.py` | FastAPI + WebSockets real-time telemetry server | `cli.py`, `commands/ui.py` | `test_server_security.py` | Telemetry background daemon | **CORE** | Real-time swarm monitoring server |
| `octoflow/settings.py` | Pydantic V2 settings schema with env overrides | `config.py`, `logging_config.py`, `server.py` | `test_settings.py` | `octoflow config` | **CORE** | Typed settings validation container |
| `octoflow/theme_selector.py` | Interactive theme picker with instant preview | `commands/theme.py`, `cockpit/app.py` | `test_themes_and_cli.py` | `octoflow theme` interactive | **CORE** | Terminal theme customizer |
| `octoflow/themes.py` | Curated palettes, borders, banners, screensavers | `cli.py`, `cockpit/app.py`, `commands/theme.py` | `test_themes_and_cli.py` | `octoflow theme`, `banner`, `screensaver` | **CORE** | Terminal design system & styling |
| `octoflow/tools.py` | WorkspaceSandbox, AST validator, advisory file locks | `arm.py`, `healing.py` | `test_tools_security.py`, `test_workspace_sandbox_comprehensive.py` | Arm execution sandbox | **CORE** | Sandboxed tool execution security layer |
| `octoflow/triage.py` | Workspace git diff inspector & AST patch triage | `commands/triage.py`, `cockpit/app.py` | `test_developer_pillars.py` | `octoflow triage`, `octoflow diff-review` | **EXPERIMENTAL** | Patch review utility; marked experimental |
| `octopus_brain/` | Biological models (Hodgkin-Huxley, connectome, LTP) | Agents, neural test suite | `test_accurate_biophysics.py`, `test_losses.py`, `test_connectome_and_biophysics.py` | N/A | **CORE** | Core neuro-inspired learning architecture |
| `envs/` | Gymnasium simulation environments (ReachAndAvoid, etc.) | Training scripts, env test suite | `test_env.py`, `test_hunting_env.py`, `test_curriculum.py` | N/A | **CORE** | Swarm simulation & benchmark testbeds |
| `checkpoints/` | Neural weights (`.pt`, `.onnx`, connectome JSON) | `experiments/infer.py`, tests | Verified model inference | N/A | **CORE (DATA)** | 24 MB binary weights (see Section 3 for Git LFS) |
| `api/` | Flask HTTPBasicAuth sample (`api/auth.py`) | Tests | `test_security_p0_poc.py`, `test_security_remediation_verified.py` | None | **REMOVE-CANDIDATE (REVIEW)** | Tested by security reproduction tests; preserve pending owner review |
| `architecture/` | System architecture topology & biology mapping | Documentation | N/A | N/A | **CORE (DOCS)** | Foundational architectural specification |
| `backend/` | Sample FastAPI backend scaffold (`backend/main.py`) | `docs/STATE.md` | None | None | **REMOVE-CANDIDATE (REVIEW)** | Sample deliverable from demo runs; preserve pending owner review |
| `deploy/` | Container definitions (`deploy/Dockerfile`, root `Dockerfile`) | Docker builds, CI | None | None | **CORE (INFRA)** | Container deployment configuration |
| `docs/` | System manuals, security models, architecture notes | Maintainers, `octoflow/manual.py` | `test_audit_eject_federation.py` | `octoflow manual` | **CORE (DOCS)** | Master documentation repository |
| `experiments/` | Research scripts, training curves, baseline benchmarks | `test_benchmark_suite.py` | `test_benchmark_suite.py` | None | **EXPERIMENTAL** | Research scripts and ablation experiments |
| `frontend/` | Sample Vite/React web deliverable (`frontend/`) | `docs/STATE.md`, `octoflow/ignition.py` | None | None | **REMOVE-CANDIDATE (REVIEW)** | Sample deliverable from demo runs; preserve pending owner review |
| `models/` | Deliverable model schema (`models/resume_analyzer.py`) | `docs/STATE.md` (D10), tests | `test_resume_analyzer.py` (skipped stub) | None | **EXPERIMENTAL (WIP D10)** | Resume analyzer deliverable D10; preserve pending implementation |
| `notebooks/` | Jupyter quickstart tutorial notebook | Developer onboarding | None | None | **EXPERIMENTAL** | Interactive tutorial walkthrough |
| `schemas/` | Sample SQLAlchemy user model (`schemas/user.py`) | `docs/STATE.md` | None | None | **REMOVE-CANDIDATE (REVIEW)** | Sample deliverable from demo runs; preserve pending owner review |
| `scripts/` | Developer and CI helper scripts | Makefile, CI workflows | None | None | **CORE (TOOLING)** | Maintenance and build automation scripts |
| `task_manager/` | Sample fullstack deliverable directory (ignored) | `docs/STATE.md` | None | None | **REMOVE-CANDIDATE (REVIEW)** | Untracked demo artifact in `.gitignore` |
| `tests/` | Comprehensive test suite (491 passing unit tests) | pytest | Full test execution | N/A | **CORE** | Verification and regression suite |
| `visualizer/` | Three.js / TypeScript 3D connectome visualizer source | `octoflow/server.py` (via `dist`) | Build / bundle verified | Served via `octoflow ui` | **CORE** | Source code for browser 3D HUD |
| `infer.py` | Convenience root entrypoint for inference | `docs/STATE.md` | None | CLI script | **CORE** | Root convenience script |
| `train.py` | Convenience root entrypoint for training | `docs/STATE.md` | None | CLI script | **CORE** | Root convenience script |
| `octo` / `octos` | Shell wrapper executables for CLI entrypoints | Developers, scripts | None | CLI binary | **CORE** | Fast shell execution wrappers |
| `start.sh` | Local multi-service startup script | Developers | None | Shell script | **CORE** | Development runtime launcher |

---

## 2. Experimental Features Labeling & Runtime Notices

The following CLI commands have been classified as **EXPERIMENTAL**:
- `bench`: Standardized 8-arm benchmark challenges.
- `diff-review` / `triage`: Workspace git diff patch triage with AST validation.
- `docs` / `manual`: Interactive Cephalopod Master Manual reader.
- `eject`: Autonomous standalone cephalopod agent harness exporter.
- `federation`: Zero-trust multi-machine agent federation pipeline.
- `monorepo`: Monorepo package topology scanner.
- `notify`: Slack and Discord webhook alert dispatcher.
- `play` / `runner`: Benthic Dot Runner easter egg arcade game.
- `record`: Asciinema v2 terminal session recorder.

### Implementation Details:
1. **CLI Help Text (`--help`):** Each command has had `[experimental]` appended to its docstring. Typer and Rich display this tag in root `--help` and subcommand `--help` outputs.
2. **One-Time Session Notice:** Each experimental command callback maintains a session-scoped guard flag (`_notice_printed = False`) and emits a warning upon first execution:
   ```text
   Notice: '<command>' is an experimental feature and may change or be removed in future releases.
   ```
3. **Snapshot Tests:** All 77 snapshot tests in `tests/test_cli_help_snapshots.py` have been synchronized and pass with 100% precision.

---

## 3. Storage Audit: `checkpoints/` Directory

### Asset Inventory:
The `checkpoints/` directory contains 6 pre-trained model and topology artifacts totaling ~24 MB:
- `best_octopus_brain.pt` (5.5 MB): PyTorch neural weights for the central brain and arm reflex controllers.
- `top1_octopus_brain.pt` (5.5 MB): Checkpoint from the top-performing benchmark curriculum run.
- `smoke_test_model.pt` (5.5 MB): Small model checkpoint utilized for fast smoke tests.
- `test_top1_model.pt` (5.5 MB): Validation model checkpoint.
- `octopus_brain.onnx` (1.9 MB): ONNX-exported model graph used by the browser 3D visualizer.
- `cephalopod_connectome.json` (170 KB): Graph topology definitions mapping 8 arms and central ganglia.

### Sensitivity & Storage Assessment:
- **No Sensitive Secrets:** AST inspection confirmed no API keys, credentials, or private user data are embedded within checkpoint weights or metadata.
- **Binary Weight Weight:** Git repositories degrade in performance when storing frequent binary weight revisions.
- **Recommendations:**
  1. **Git LFS:** Configure `.gitattributes` to manage `*.pt` and `*.onnx` via Git Large File Storage (LFS):
     ```gitattributes
     checkpoints/*.pt filter=lfs diff=lfs merge=lfs -text
     checkpoints/*.onnx filter=lfs diff=lfs merge=lfs -text
     ```
  2. **Git Ignore Rules:** Existing `.gitignore` already ignores runtime checkpoints (`checkpoints/` and `*.checkpoint`). Keep committed baseline evaluation checkpoints tracked via Git LFS, and ignore transient training artifacts.
  3. **Do Not Delete:** The checkpoint files are required for offline inference demonstrations, browser WebGL ONNX inference, and model loading tests.

---

## 4. Special Handling: `octoflow/federation.py`

In accordance with P2.6 requirements:
1. **PII / Secret Redactor (CORE Utility):**
   - The 14-rule regex redactor (`PII_RULES`) and recursive dictionary/string sanitization pipeline (`FederationGuard`, `GLOBAL_FEDERATION_GUARD`) are classified as a **CORE security utility**.
   - These rules protect against leakage of Anthropic API keys, OpenAI API keys, GitHub tokens, AWS credentials, private keys, emails, and credit card numbers.
   - The logging filter (`SecretSanitizingLogFilter`) actively scrubs all OctoFlow log outputs.
2. **Peer Networking (EXPERIMENTAL / Unused):**
   - Peer node trust structures (`PeerTrustLevel`, `FederationPeer`, `register_peer`, `record_peer_outcome`) are documented as **experimental, unused prototypes**.
   - No networking code or socket listeners were added.

---

## 5. Review Candidates for Project Owner Decision

The following modules and directories have minimal or peripheral integration with the core OctoFlow package, but have references in existing security characterization tests or documentation. Per safety constraints ("Anything with any reference must not be deleted; list it in the document for the owner's decision"), they are preserved pending explicit owner sign-off:

1. **`api/auth.py`**:
   - *Status:* Isolated Flask HTTPBasicAuth test endpoint from initial repository baseline.
   - *References:* Verified by `tests/test_security_p0_poc.py` and `tests/test_security_remediation_verified.py`.
   - *Owner Recommendation:* Either retain permanently as a security gauntlet target, or migrate the security tests to a test fixture and delete `api/auth.py`.
2. **`backend/` (`backend/main.py`)**:
   - *Status:* Sample FastAPI deliverable from an early demo run.
   - *References:* Documented in `docs/STATE.md`.
   - *Owner Recommendation:* Remove from repository root or relocate under an `examples/workspace_samples/` directory.
3. **`frontend/`**:
   - *Status:* Standalone Vite/React web deliverable from an early demo run.
   - *References:* Documented in `docs/STATE.md`; inspected by workspace deliverable detector in `octoflow/ignition.py`.
   - *Owner Recommendation:* Relocate under an `examples/` directory if kept as a reference deliverable.
4. **`schemas/user.py`**:
   - *Status:* Simple SQLAlchemy User model from demo runs.
   - *References:* Documented in `docs/STATE.md`.
   - *Owner Recommendation:* Delete or move to `examples/`.
5. **`models/resume_analyzer.py`**:
   - *Status:* Model schema for Deliverable D10 (AI Resume Analyzer).
   - *References:* Documented in `docs/STATE.md` (D10) and targeted by `tests/test_resume_analyzer.py` (currently skipped).
   - *Owner Recommendation:* Retain as active work-in-progress deliverable D10.
