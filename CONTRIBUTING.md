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
