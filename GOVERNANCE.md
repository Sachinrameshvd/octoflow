# Project Governance & Maintainership Model

This document outlines how technical decisions are made, how releases are planned and shipped, and how community members can become maintainers of OctoFlow.

---

## 1. Governance Model: Lead Maintainer (BDFL)

OctoFlow operates under a **Lead Maintainer (BDFL)** governance model.

A project like OctoFlow—combining multi-agent planning, biophysical sensory gating, real-time TUI cockpits, and WebGL telemetry—requires clear technical vision, high architectural cohesion, and uncompromising standards for security and truthfulness.

The Lead Maintainer holds final authority and responsibility for:
- Core architecture, design records (ADRs), and breaking changes.
- Preserving the **3 Core Moats**:
  1. **Local-First & Zero-Network Egress:** User code stays on-device; telemetry is confined to loopback (`127.0.0.1`).
  2. **Truthful Gating & Accounting:** Exact token receipts without synthetic inflation; honest `FAILED` run outcomes.
  3. **Terminal Accessibility & Single-Width Glyphs:** Verified `wcwidth <= 1` presentation characters; zero wide emojis.
- Managing releases, versioning, and package distribution.

---

## 2. Community Roles

### Users & Community Members
Anyone who installs OctoFlow, experiments with local swarms, runs benchmarks, or participates in GitHub Discussions.

### Contributors
Anyone who submits a bug report, documentation improvement, tutorial, new specialist guild, or code pull request. Every contributor who follows our [Code of Conduct](CODE_OF_CONDUCT.md) and [Contributing Guidelines](CONTRIBUTING.md) is welcomed and appreciated.

### Core Maintainers
Trusted contributors granted issue triage permissions and commit/merge rights. Maintainers assist with PR reviews, dependency policy enforcement, and community guidance.

---

## 3. Decision-Making Process

### Routine Improvements & Bug Fixes
- Bug fixes, typo corrections, tutorial updates, and minor performance enhancements are reviewed, approved, and merged as soon as automated CI checks pass.

### Feature Proposals & Architectural Changes
- For substantial features (new LLM providers, altered arm morphology, new tools, or CLI restructuring), contributors should open a **GitHub Issue** or **Discussion** first.
- Significant technical decisions must be documented as an **Architectural Decision Record (ADR)** in [`docs/adr/`](docs/adr/) explaining the context, alternatives considered, and consequences.

### Consensus & Resolution
We strive for consensus through open, reasoned technical discussions. When consensus cannot be reached, the Lead Maintainer makes the final determination to maintain conceptual integrity and keep maintenance burdens manageable.

---

## 4. Release Process

OctoFlow strictly adheres to **Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH`):
- **PATCH** (`0.3.1`): Backward-compatible bug fixes and security patches.
- **MINOR** (`0.4.0`): New features, new specialist guilds, or non-breaking provider additions.
- **MAJOR** (`1.0.0`): Breaking public API or CLI contract changes.

Every release requires:
1. All automated CI jobs green: Lint (Ruff), Typecheck (mypy), Unit Tests, Docs Integrity (`make check-docs`), and Reference Staleness (`make check-docs-ref`).
2. Generated reference documentation regenerated and committed (`make docs-ref`).
3. Release notes documented in [`CHANGELOG.md`](CHANGELOG.md) under a tagged section following Keep a Changelog.
4. Supply chain verification: Clean lockfile (`requirements.lock`), CycloneDX SBOM, and license audit.

---

## 5. Becoming a Maintainer

We welcome contributors who wish to step into maintainership!

### Criteria for Nomination
- **Track Record:** Multiple high-quality pull requests merged across core modules, provider integrations, or test suites.
- **Standards Alignment:** Demonstrated understanding of the zero-emoji policy, non-blocking cockpit loops, secret redaction, and dependency policy.
- **Community Citizenship:** Constructive, polite communication in issues, code reviews, and discussions adhering to the [Code of Conduct](CODE_OF_CONDUCT.md).

Nomination is proposed by the Lead Maintainer or an existing maintainer and confirmed upon mutual agreement.
