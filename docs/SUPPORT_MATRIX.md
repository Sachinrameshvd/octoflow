# OctoFlow Platform Support Matrix & Deprecation Policy

This document defines the verified execution environments, hardware tiers, supported model families, API contracts, and the pre-1.0 semantic versioning and deprecation schedule for OctoFlow.

---

## 1. Verification Policy

OctoFlow guarantees truthful documentation. Every environment, runtime, model, and API listed below carries:
- An explicit **Verification Date**.
- The specific **Verification Command, Suite, or CI Workflow**.
- A tier classification (**Tier 1: Fully Tested**, **Tier 2: Community Verified**, or **Not Supported**).

Configurations not listed here are considered untested and unsupported.

---

## 2. Operating System & Hardware Tiers

| Operating System | Architecture | Support Tier | Status & Requirements | Last Verified | Verification Method |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **macOS 14+ (Sonoma, Sequoia)** | Apple Silicon (`arm64`) | **Tier 1 (Primary)** | Native Metal GPU acceleration, 20 FPS POSIX cockpit, full local loopback. | 2026-11-09 | Live Ollama test, `pytest tests/`, `octoflow bench` |
| **Linux (Ubuntu 22.04, 24.04)** | `x86_64` / `arm64` | **Tier 1 (CI Baseline)** | POSIX termios, headless daemon, full loopback networking. | 2026-11-09 | GitHub Actions (`.github/workflows/ci.yml`) |
| **Linux (Debian 12, Fedora 40)** | `x86_64` | **Tier 2** | Standard glibc POSIX environment with Python 3.10+. | 2026-11-08 | Clean-room container test (`docs/INSTALL.md`) |
| **Windows via WSL2 (Ubuntu 22.04+)**| `x86_64` / `arm64` | **Tier 2** | Supported through Windows Subsystem for Linux (WSL2). | 2026-11-08 | Acceptance manual install test |
| **Windows Native (cmd.exe / PowerShell)** | `x86_64` | **Not Supported** | Incompatible with POSIX non-blocking termios loop. See [Roadmap](../ROADMAP.md#not-planned). | 2026-11-09 | Documented in `MODULE_TRIAGE.md` |

---

## 3. Python Runtime Support

| Python Version | Status | CI Matrix | Test Command | Last Verified |
| :--- | :--- | :--- | :--- | :--- |
| **Python 3.10** | Active / Fully Supported | Linux & macOS | `pytest tests/ -m "not live"` | 2026-11-09 |
| **Python 3.11** | Active / Fully Supported | Linux & macOS | `pytest tests/ -m "not live"` | 2026-11-09 |
| **Python 3.12** | Active / Recommended | Linux & macOS | `pytest tests/ -m "not live"` | 2026-11-09 |
| **Python 3.13+** | Experimental / Community Preview | Ad-hoc local | `pytest tests/test_glyph_policy.py` | 2026-11-09 |
| **Python <= 3.9** | **Unsupported** | None | Enforced via `pyproject.toml` (`>=3.10`) | 2026-11-09 |

---

## 4. Local Model Matrix (Ollama)

Local inference runs 100% on-device over loopback HTTP (`http://localhost:11434`) with zero cloud egress:

| Model Tag | Provider / Engine | Role & Recommended Spec | Benchmark Score | Last Verified | Verification Method |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`qwen2.5-coder:7b`** | Ollama v0.5.x | **Primary Recommended Coding Model** (16GB RAM / M-series Mac) | 83.3% pass, 35% token gating reduction | 2026-11-09 | Live benchmark: `octoflow bench --task rate_limiter` |
| **`qwen2.5-coder:1.5b`** | Ollama v0.5.x | **Edge / Low-Memory Systems** (8GB RAM laptops) | 66.7% pass rate | 2026-11-08 | Guided first-run wizard test (`octoflow first-run`) |
| **`llama3.1:8b`** | Ollama v0.5.x | **Generalist Reasoning Model** (16GB RAM) | 75.0% pass rate | 2026-11-08 | Contract test suite (`tests/contract/test_ollama_contract.py`) |
| **`deepseek-coder-v2:16b`** | Ollama v0.5.x | **High-Capacity Coding Model** (32GB+ RAM / Workstations) | 91.7% pass rate | 2026-11-07 | Manual evaluation suite |

---

## 5. Cloud Provider API Contracts

Cloud provider integrations are pinned to tested upstream API versions and verified via deterministic contract suites against recorded cassettes:

| Provider | Supported Models | Pinned API Version | SDK / Transport | Contract Test Suite | Last Verified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Anthropic** | `claude-3-5-sonnet-20241022`<br>`claude-3-haiku-20240307` | `2023-06-01` | `anthropic>=0.25.0` / HTTP | [`tests/contract/test_anthropic_contract.py`](../tests/contract/test_anthropic_contract.py) | 2026-11-09 |
| **OpenAI** | `gpt-4o`<br>`gpt-4o-mini` | `v1/chat/completions` | `openai>=1.20.0` / HTTP | [`tests/contract/test_openai_contract.py`](../tests/contract/test_openai_contract.py) | 2026-11-09 |
| **Google Gemini** | `gemini-1.5-pro`<br>`gemini-1.5-flash` | `v1beta` | `google-genai>=0.1.0` / HTTP | [`tests/contract/test_gemini_contract.py`](../tests/contract/test_gemini_contract.py) | 2026-11-09 |
| **vLLM / LM Studio** | OpenAI-compatible local servers | `/v1` endpoints | `httpx>=0.25.0` | [`tests/contract/provider_contract.py`](../tests/contract/provider_contract.py) | 2026-11-08 |

---

## 6. Frontend & Visualizer Stack

The 3D Cephalopod Connectome Visualizer is bundled directly inside wheel and sdist distributions (per [ADR 0002](adr/0002-visualizer-dist.md)):

| Component | Minimum Version | Tested Version | Verification Method | Last Verified |
| :--- | :--- | :--- | :--- | :--- |
| **Node.js** | `>= 20.0.0` (LTS) | `v20.18.0` | `node -v` | 2026-11-09 |
| **npm** | `>= 10.0.0` | `10.8.2` | `npm -v` | 2026-11-09 |
| **Three.js** | `^0.160.0` | `0.160.0` | Bundle build & WebGL canvas render | 2026-11-09 |
| **Vite** | `^5.0.0` | `5.4.8` | `make visualizer-sync` | 2026-11-09 |
| **Wheel Bundle** | `octoflow/dist/` | Standalone asset | `bash scripts/verify_wheel.sh` | 2026-11-09 |

---

## 7. Pre-1.0 Semantic Versioning & Deprecation Policy

OctoFlow adheres to semantic versioning during its `0.x` pre-1.0 lifecycle:

### Version Semantics (`0.MINOR.PATCH`)
1. **Patch Releases (`0.3.x`)**:
   - Strictly backwards-compatible.
   - Contains bug fixes, documentation clarifications, test stability updates, and security patches.
   - No breaking changes or configuration schema changes.
2. **Minor Releases (`0.4.0`)**:
   - May introduce new specialist guilds, CLI commands, and provider adapters.
   - Any deprecations must be accompanied by explicit deprecation warnings in the CLI and documentation for **at least one minor release** prior to removal.
   - Breaking changes are accompanied by an ADR and migration steps in [`CHANGELOG.md`](../CHANGELOG.md).
3. **Deprecation Protocol**:
   - When an interface, option, or setting is marked for retirement:
     1. It emits a visible non-fatal warning (`DeprecationWarning` or terminal notice) directing the user to the modern replacement.
     2. It is listed in the escape hatch registry below with its targeted removal milestone.
     3. It is removed only after one full minor release cycle has elapsed.

---

## 8. Escape Hatches & Retirement Schedule

To facilitate smooth transitions without stranding existing configurations, OctoFlow provides temporary `OCTOFLOW_LEGACY_*` escape hatches:

| Escape Hatch Environment Variable | Purpose & Fallback Behavior | Deprecated In | Target Removal | Recommended Modern Alternative |
| :--- | :--- | :--- | :--- | :--- |
| **`OCTOFLOW_LEGACY_GLYPHS=1`** | Re-enables legacy double-width Unicode emojis instead of approved single-width terminal glyphs. | `v0.2.0` | **`v0.5.0`** | Standard single-width glyphs from `octoflow/glyphs.py` (`--ascii` for 7-bit terminals). |
| **`OCTOFLOW_LEGACY_CONFIG=1`** | Permits loading legacy unversioned `config.json` dictionaries without Pydantic schema validation. | `v0.2.0` | **`v0.4.0`** | Typed schema migrations via `octoflow config show`. |
| **`OCTOFLOW_LEGACY_SWARM_MODE=1`** | Preserves monolithic single-octopus orchestration syntax before consortium auto-scaling. | `v0.3.0` | **`v0.5.0`** | Elastic autoscaler: `octoflow run --octos auto` or `--octos 1`. |
