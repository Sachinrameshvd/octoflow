# Changelog

All notable changes to OctoFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.3.0] - 2026-11-09

### Breaking Changes
- **Mock Fallback Elimination (Decision D1)**: Eliminated silent fallback to `MockLLMProvider` in live mode when real API providers fail or credentials are missing. Live runs with misconfigured or exhausted providers now raise `ProviderExhaustedError`, report `[FAILED]` with actionable configuration hints, sanitize all credentials, and exit with code 2.
- **Python 3.9 EOL Support Dropped (P2.7)**: Raised minimum Python requirement to `>=3.10` in `pyproject.toml` following Python 3.9 end-of-life. Removed Python 3.9 classifier and updated CI matrix to Python 3.10, 3.11, and 3.12 (with 3.13 experimental allowed-failure).
- **PyTorch & ML Extras Made Optional (P2.5)**: Decoupled mandatory `torch` dependency in favor of a pure NumPy baseline sensory encoder. Installing torch is now optional via `pip install "octoflow[ml]"`. Systems without torch run with identical gate sensitivity and 8-arm active inference using NumPy.
- **Zero-Emoji Typography Contract (P6.3)**: Audited and removed all ambiguous, wide emoji characters (`[lightning]`, `[octo]`, `[fire]`, etc.) across all CLI ribbons, visualizer badges, terminal outputs, and MCP responses. Strictly enforced semantic single-width glyphs (`•`, `·`, `○`, `◈`, `✔`, `✖`) with verified display width (`wcwidth <= 1`) and strict 7-bit ASCII fallbacks (`--ascii`).
- **Truthful Run Outcomes Contract (P1.1)**: Runs that produce 0 filesystem modifications or fail to converge honestly report outcome `FAILED` (`model produced no file changes`) with exit code 2. Only runs that write valid code and pass verification report `COMPLETE`.
- **Standardized Exit Code Taxonomy (P2.4)**: Enforced strict exit codes: `0` for success, `1` for tool/workspace/budget error, `2` for LLM provider family errors, `3` for configuration and CLI usage errors, and `70` for unexpected internal runtime errors.

### Added
- **Automated Reference Documentation Generator (P9.4)**: Created `scripts/gen_reference.py` to deterministically generate CLI reference (`docs/reference/cli.md`), configuration schema (`docs/reference/config.md`), error catalog (`docs/reference/errors.md`), and exit codes (`docs/reference/exit-codes.md`).
- **Task-Oriented Tutorials (P9.3)**: Added 8 bite-sized tutorials under `docs/tutorials/` (<10 mins each) with verified execution outputs and timestamps:
  - `01-first-project-with-ollama.md`: First project using local Ollama model (`qwen2.5-coder:7b`).
  - `02-reading-the-token-receipt.md`: Understanding token receipts, measured vs estimated usage, local avoided tokens, and JSON exports.
  - `03-undoing-a-run.md`: Rolling back filesystem mutations with checkpoint snapshots and `octoflow undo`.
  - `04-building-with-a-custom-guild.md`: Defining, validating, and executing missions with custom 8-arm specialist guilds.
  - `05-adding-a-custom-provider.md`: Subclassing `BaseLLMProvider`, provider registration, and verifying contracts with `ProviderContractSuite`.
  - `06-using-octoflow-from-mcp.md`: Configuring OctoFlow stdio MCP server for Claude Code and Cursor.
  - `07-watching-in-the-visualizer.md`: Live 3D connectome visualization, 8088 bridge, Three.js camera controls, and offline trace replay.
  - `08-running-benchmarks.md`: Benchmarking local vs cloud providers, measuring token savings against ungated baselines.
  - `docs/tutorials/README.md`: Index of all 8 tutorials with duration and summaries.
- **Comprehensive FAQ (P9.3)**: Created `docs/FAQ.md` answering top architectural and operational questions: biological metaphors, gate mathematics, zero-network privacy guarantees, model recommendations, costs, Windows support, and bug reporting.
- **Troubleshooting Additions (P9.3)**: Updated `docs/TROUBLESHOOTING.md` with guidance for PTY/terminal desync, Apple Silicon Metal acceleration, port conflicts on 8088/5173, and anchors for all 14 `E-*` error codes.
- **Automated Documentation Integrity Checker (P9.3)**: Created `scripts/check_docs.py` and test suite `tests/test_docs_checker.py` enforcing relative links, anchor fragments, CLI subcommand accuracy, error catalog consistency, zero-emoji policy, and path confinement.
- **Master Cephalopod Architecture & ADRs (P9.2)**: Authored `docs/architecture.md` with Mermaid diagrams, 23-module responsibility matrix, run lifecycle sequence, gate math proofs (`scripts/worked_example_gate.py`), `docs/glossary.md`, and 7 foundational ADRs (`docs/adr/0001` - `0007`).
- **README Rewrite & Manual Decoupling (P9.1)**: Streamlined `README.md` to under 170 lines with transparent positioning, an Alpha maturity matrix, truthful live receipts, and decoupled field manual to `docs/MANUAL.md`.
- **Developer Debug Aids & Replay Engine (P8.4)**: Added `--trace` for writing granular JSONL execution events (`trace.jsonl`), `octoflow replay` for replaying traces offline in visualizer and terminal, `doctor --json` diagnostics, and `make dev` local development stack.
- **Model Context Protocol (MCP) Server Conformance (P8.3)**: Implemented conformant stdio JSON-RPC 2.0 server (`octoflow mcp`) exposing 8 standardized tools for Claude Code and Cursor, with complete protocol handshake and input schemas.
- **Custom 8-Arm Specialist Guilds (P8.2)**: Implemented declarative JSON guild specification schema (`GuildSpec`), guild loader, validator (`octoflow guild validate`), and CLI exploration (`octoflow guild list|show`).
- **Provider Extension Contract & Template (P8.1)**: Defined `BaseLLMProvider` contract specification, reusable `ProviderContractSuite` test harness, dynamic provider registry, and example custom provider template.
- **AI Resume Analyzer Showcase (P7.2)**: Delivered complete real-world demo project built by OctoFlow in `examples/resume-analyzer/`: FastAPI backend, ATS scoring, skills-gap analysis, dark-mode dashboard, with complete provenance receipts.
- **Truthful Token Receipts & Gate Accounting (P7.1)**: Implemented token ledger (`octoflow receipt [run_id]`) tracking measured input/output tokens, avoided prompt tokens from sensory gating, per-arm spending breakdowns, and machine-readable JSON exports (`--json`).
- **Visualizer WCAG 2.2 AA Accessibility & WebGL Fallback (P6.4)**: Implemented WebGL context loss handling, `#webgl-fallback-banner`, text telemetry fallback, audio opt-in controls, and reduced-motion policy.
- **Terminal Accessibility & Single-Width Glyph Policy (P6.3)**: Created `octoflow/glyphs.py` defining single-width characters (`wcwidth == 1`) with 7-bit ASCII fallbacks (`--ascii`), `NO_COLOR` standard compliance, and non-TTY plain mode (`--plain`, `--json`).
- **Central Message Catalog & Plain-Language Help (P6.2)**: Created `octoflow/messages.py` centralizing user-facing banners, error diagnostics, and empty-state guidance.
- **Guided First-Run Setup Wizard (P6.1)**: Implemented automatic first-run onboarding (`octoflow first-run`), pre-flight checks, 3-question setup, and isolated 60-second sandbox demo.
- **Supply Chain Security & Dependency Policy (P5.2)**: Established dependency tiers, reproducible lockfiles (`requirements.lock`), CycloneDX SBOM generation, license compatibility auditing, and security audit checklists (`docs/SECURITY.md`, `docs/THREAT_MODEL.md`).
- **Process Isolation & Ignition Engine (P3.4)**: Implemented supervised background service launching with readiness detection, automatic browser preview (`--open`), and registry management (`octoflow ps`, `octoflow stop`).
- **Git Checkpoint Snapshots & Safe Undo (P3.3)**: Implemented automatic run branch creation (`octoflow/run-<id>`), dirty working tree stashing, and safe one-command rollbacks (`octoflow undo [run_id]`).
- **Benchmark Cassette Recording & Replay Harness (P2.8, P3.2)**: Implemented reproducible benchmark harness, cassette recording, and offline replay verification suite.
- **Typed Pydantic v2 Settings Schema & Atomic Writes (P2.3)**: Implemented versioned configuration schema (`Settings`), crash-safe atomic writes, secret masking, and `octoflow config` CLI command group.
- **Command Router & Destructive Command Interceptor (P1.3)**: Implemented cockpit command router with destructive command interceptors (`rm`, `mv`, `dd`, `git reset --hard`), confirmation prompts, and bracketed paste protection.
- **Workspace Sandbox & Tool Confinement (P1.4)**: Hardened workspace sandbox with path confinement, allowlist execution policy, and subprocess timeouts.
- **Telemetry Server Hardening (P1.5)**: Hardened telemetry server with loopback binding (`127.0.0.1`), WebSocket Origin validation, and Host header check.

### Changed
- **Cockpit Modularization (P2.1 & P2.2)**: Split monolithic `octoflow/cli.py` (3,499 lines) into modular command handlers in `octoflow/commands/` and dedicated TUI engine in `octoflow.cockpit`.
- **Modernized HTTP & WebSocket Transports (P2.7)**: Replaced blocking `requests` and legacy websockets with `httpx` and `websockets-sansio` async client.
- **Centralized Error Hierarchy (P2.4)**: Re-parented all provider, tool, workspace, and config exceptions to `OctoFlowError`.
- **Standardized Telemetry Binding (P1.5)**: Hardened telemetry server bind host to loopback `127.0.0.1` by default with Origin and Host header validation.

### Deprecated
- **Legacy Shell Router Mode (P1.3)**: Marked `OCTOFLOW_LEGACY_ROUTER=1` as deprecated; legacy router bypasses destructive command confirmation.
- **Legacy Glyph Support (P6.3)**: Marked `--legacy-glyphs` transition flag as deprecated; will be removed in future major release in favor of clean bio-glyphs.

### Removed
- **Silent Mock Fallback (P1.1)**: Removed silent fallback to `MockLLMProvider` in live mode when real API providers fail or credentials are missing.
- **Python 3.9 Runtime Support (P2.7)**: Removed Python 3.9 classifier and CI runners following upstream end-of-life.
- **Mandatory PyTorch Dependency (P2.5)**: Removed `torch` from mandatory requirements, replacing with NumPy sensory encoder.
- **Silent Exception Swallowing (P2.4)**: Removed broad `except Exception: pass` clauses across all core modules in favor of structured debug logging.

### Fixed
- **Destructive Command Safety Gating (P1.3)**: Prevented accidental file deletion and destructive git resets during interactive cockpit sessions.
- **Workspace Directory Traversal (P1.4)**: Fixed symlink escapes and `..` directory traversal in tool operations (`read_file`, `write_file`, `list_dir`).
- **Telemetry Origin Hijacking (P1.5)**: Fixed WebSocket DNS-rebinding vulnerability on port 8088 by strictly validating Host and Origin headers.
- **Tool Call Parsing Failures (P3.2)**: Fixed JSON parsing errors on trailing commas and hallucinated tool formats from small local models.
- **Provider Retries & Exponential Backoff (P1.2)**: Added jittered backoff retry loop honoring `Retry-After` headers on 429 rate limits.

### Security
- **Credential Storage Hierarchy (P5.4)**: Enforced strict key resolution order: Environment Variables > OS Keyring > 0600 Config File (`~/.octoflow/config.json`).
- **Outbound Redaction & Egress Isolation (P1.5, P5.4)**: Automatically scrubbed credentials, API keys, and bearer tokens from outbound requests and logs via `redact_secrets()`.
- **Safe Subprocess Execution (P1.4)**: Enforced argument vector execution (`argv`, `shell=False`) by default, restricting commands to approved allowlist.
