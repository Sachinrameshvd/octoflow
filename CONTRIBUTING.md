# Contributing to OctoFlow

Thank you for contributing to OctoFlow! This document provides guidelines for contributors with specific emphasis on supply-chain security and dependency management.

---

## 1. Development Setup

Initialize your environment and install locked test dependencies:

```bash
make setup
```

This installs base and development dependencies from `requirements.lock` and links the project in editable mode without overriding locked versions.

To run tests:
```bash
make test-fast   # Run fast unit tests
make test        # Run full test suite with coverage
```

---

## 2. Dependency Management & Pinning Policy

OctoFlow adheres to a strict supply-chain policy (see [`docs/DEPENDENCY_POLICY.md`](file:///Users/sachinrk/Desktop/Octoflow%20copy/docs/DEPENDENCY_POLICY.md)):

1. **Minimal Dependencies:** Avoid external packages if the functionality can be implemented cleanly with Python's standard library (`importlib`, `pathlib`, `json`, `ast`, etc.).
2. **Library Version Ranges (`pyproject.toml`):**
   - Direct dependencies must specify lower bounds only (e.g. `numpy>=1.22.0`).
   - **Do NOT pin exact versions (`==`)** in `pyproject.toml`. Exact pinning belongs exclusively in `requirements.lock`.
   - Do NOT specify speculative upper bounds (`<3.0.0`) unless a breaking incompatibility has been verified.
3. **Lockfile Regeneration:**
   If you modify dependencies in `pyproject.toml`, regenerate the deterministic lockfile before opening a PR:
   ```bash
   make lock
   ```
4. **License Compatibility:**
   Every new dependency must use an OSI-approved permissive license (MIT, BSD-2/3-Clause, Apache-2.0, ISC, PSF). Copyleft licenses (GPL, AGPL, SSPL) are strictly prohibited. See [`docs/THIRD_PARTY_LICENSES.md`](file:///Users/sachinrk/Desktop/Octoflow%20copy/docs/THIRD_PARTY_LICENSES.md).
5. **Security Auditing:**
   Verify that your proposed changes do not introduce new vulnerabilities:
   ```bash
   pip-audit
   cd visualizer && npm audit
   ```
   If a high-severity finding cannot be avoided, an approved exception must be documented in [`docs/audit/dependency-exceptions.md`](file:///Users/sachinrk/Desktop/Octoflow%20copy/docs/audit/dependency-exceptions.md).

---

## 3. WebGL Visualizer

When working on the visualizer:
```bash
cd visualizer
npm ci
npm run lint
npm run test
npm run build
```
Synchronize the built distribution into the Python package using:
```bash
make visualizer-sync
```

---

## 4. Contributor Inner Loop & Debugging

For comprehensive debugging and inner-loop guides, see [`docs/debugging.md`](docs/debugging.md).

### Live Development Stack (`make dev` & `make dev-stop`)
Run both the Python telemetry bridge and the Vite 3D Visualizer dev server concurrently with Hot Module Replacement:
```bash
make dev
```
- Telemetry WebSocket server: `http://127.0.0.1:8088` (`ws://127.0.0.1:8088/ws/telemetry`)
- Vite 3D Visualizer: `http://localhost:5173` (cross-origin 5173 allowed)

To terminate both background servers:
```bash
make dev-stop
```

### Execution Tracing & Replay
- Run with `--trace` (or `OCTOFLOW_TRACE=1`) to record structured JSONL events to `~/.octoflow/runs/<id>/trace.jsonl` (mode 0600, zero prompt text by default).
- Replay a recorded run into the terminal and 3D visualizer:
  ```bash
  octoflow replay latest --speed 1.0
  ```

### Bug Reports & Environment Diagnostics
- Run `octoflow doctor --json` for machine-readable subsystem health diagnostics.
- Run `octoflow bugreport` to generate a redacted Markdown environment summary with all secrets masked for pasting into GitHub issues.

---

## 5. Architectural Reference & Design Records

Before making substantial structural changes, familiarize yourself with our system design docs:
- **System Architecture & Data Flow:** Detailed diagrams, module responsibilities, gate math, and threading models in [`docs/architecture.md`](docs/architecture.md).
- **Anatomy & Concepts Glossary:** Cross-reference cephalopod terms to code identifiers in [`docs/glossary.md`](docs/glossary.md).
- **Architectural Decision Records (ADRs):** Review foundational architectural decisions and trade-offs in [`docs/adr/`](docs/adr/).
- **Field Manual:** CLI commands and playbooks in [`docs/manual.md`](docs/manual.md).

