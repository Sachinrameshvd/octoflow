# OctoFlow Public Development Roadmap

**Status:** Living Document  
**Current Version:** v0.3.0 (Public Preview)  
**Maintained By:** OctoFlow Open Source Maintainers  

---

## 1. Vision & Guiding Principles

OctoFlow is designed as a **local-first coding swarm that spends tokens only when something changes, and shows you where every token went.**

All roadmap decisions are guided by three non-negotiable principles:
1. **Biological Realism:** Division of labor mirroring the cephalopod nervous system (autonomous brachial sensory loops with central supraesophageal coordination).
2. **Economic Honesty:** Exact ledger accounting (`measured` vs `avoided` tokens) and zero silent fallbacks.
3. **Local Sovereignty:** Total code privacy, zero telemetry, and robust operation on local open-weight models without cloud lock-in.

---

## 2. Release Horizon

### Now (Next 2 Releases: v0.3.1 & v0.4.0)

Focused on stability, developer ergonomics, and community extension points:

- **v0.3.1 (Quality & Diagnostic Refinement):**
  - **Diagnostic Error Enhancements:** Clear, actionable remediation hints and configuration file paths for all `E-CFG-*` and `E-PRV-*` codes.
  - **Local Telemetry Server Reliability:** Auto-retry port allocation when `8088` is blocked, with automatic fallback to standard library `http.server`.
  - **Receipt CSV Export:** Add `--csv` export flag to `octoflow receipt` for spreadsheet analysis alongside existing JSON output.
  - **Documentation & Seed Issues:** Public roadmap, good first issues, and issue syncing scripts.

- **v0.4.0 (Community Extension & Local Model Polish):**
  - **Built-in LM Studio Provider:** Dedicated provider connector for LM Studio local OpenAI-compatible endpoint (`http://localhost:1234/v1`).
  - **Domain-Specific Guild Presets:** Add first-party specialist rosters for Data Science & ML (`data_science.json`) and Systems/Embedded (`systems_c.json`).
  - **Interactive Visualizer Cheat Sheet:** On-screen keyboard shortcuts modal (`?` or `h`) in the 3D connectome visualizer.
  - **Benchmark Suite Expansion:** Add 2 new real-world benchmark challenges (database migration script generation and OpenAPI client generator) with automated verification suites.

---

### Next (v0.5.0 - v0.6.0)

Focused on Active Inference optimization and persistent knowledge accumulation:

- **Hebbian Learning & Vertical Lobe Refinement:**
  - Persist associative memory across runs using lightweight sqlite-vector embeddings without external heavy C++ dependencies.
  - Track successful arm repair patterns to reduce initial sensory surprise ($\Delta S$) on recurring refactoring tasks.
- **Enhanced Gate Parity Analytics:**
  - Visualize live gate sensory surprise curves ($\Delta S$ vs $\theta$) directly inside the 3D WebGL connectome HUD.
  - Automated threshold ($\theta$) auto-calibration based on model parameter count (tighter thresholds for 7B models, looser for 70B+).
- **Sub-Process Tool Sandboxing:**
  - Enforce process-level isolation and timeout enforcement on shell command execution via OS-level sandbox primitives (macOS `sandbox-exec` / Linux namespaces).

---

### Later (v1.0.0+)

Focused on enterprise multi-repo orchestration and production resilience:

- **Multi-Cephalopod Monorepo Orchestration:**
  - Graduate `octoflow consortium` from experimental to stable core, enabling multiple 8-arm swarms to coordinate across independent packages in a monorepo.
- **Bi-Directional IDE Sync:**
  - Real-time file change watching and bi-directional AST patch streaming with Cursor and Claude Code via Model Context Protocol (MCP) server events.
- **Formal Verification of Tool Contracts:**
  - Symbolic execution checks preventing arms from creating cyclic directory structures or modifying root system directories.

---

## 3. Not Planned (With Reasons & What Would Change Our Mind)

To maintain focus and supply-chain discipline, several popular feature requests are intentionally **not planned**:

### 1. Remote WAN / Internet Swarm Networking
- **Status:** Not Planned.
- **Rationale:** OctoFlow is fundamentally local-first. Exposing peer-to-peer inter-arm messaging across the public internet introduces severe attack surfaces, latency spikes, and potential codebase leakage.
- **What would change our mind:** A rigorously audited, end-to-end encrypted wire protocol with mutual TLS and signed cryptographic identities, backed by enterprise organizations requiring distributed remote compute.

### 2. Native Windows Console (Non-WSL) Support
- **Status:** Not Planned (WSL2 supported and recommended).
- **Rationale:** OctoFlow's terminal cockpit requires POSIX PTY semantics, `termios`, and ANSI VT100 control sequences for its 20 FPS non-blocking render loop. Re-implementing these atop the legacy Win32 Console API is error-prone and imposes ongoing maintenance overhead.
- **What would change our mind:** A robust, zero-dependency Windows Console abstraction PR that passes the full test suite with 100% parity and zero regressions on Linux/macOS.

### 3. Internationalization (i18n) of Prompts & CLI Diagnostics
- **Status:** Not Planned.
- **Rationale:** OctoFlow is maintained by a solo maintainer and small open-source team. Translating multi-agent system prompts, technical AST errors, and architectural concepts across dozens of languages creates severe translation drift and maintenance debt.
- **What would change our mind:** A committed internationalization working group prepared to maintain and verify translations across major releases with automated validation tooling.

### 4. Dynamic Remote Plugin Marketplace
- **Status:** Not Planned.
- **Rationale:** Downloading and executing untrusted third-party agent code at runtime presents critical supply-chain security risks (malicious tool execution, prompt injection, and credential theft). OctoFlow uses explicit declarative JSON specs for guilds and audited Python classes for providers.
- **What would change our mind:** A formal WebAssembly (Wasm) or eBPF sandboxed runtime providing cryptographic capability isolation for user-submitted plugins.

### 5. 64-Arm Default Scaling for Single Repositories
- **Status:** Not Planned (8 arms remains the default).
- **Rationale:** Two-thirds of octopus neurons reside in 8 arms. In real-world software engineering benchmarks, deploying 64 agents on a single project creates severe token contention, context dilution, and merge conflicts. 8 arms represents the optimal balance of concurrency and focus.
- **What would change our mind:** Empirical benchmark evidence demonstrating >50% throughput gain without runaway token costs on standard single-repository challenges.

---

## 4. How to Contribute to the Roadmap

Want to pick up a roadmap item?
1. Check the [Good First Issues](docs/seed-issues/) directory for self-contained starter tasks.
2. Review [`CONTRIBUTING.md`](CONTRIBUTING.md) for development setup and testing guidelines.
3. Open a GitHub Discussion or Issue referencing the roadmap item to align on design before writing code.

