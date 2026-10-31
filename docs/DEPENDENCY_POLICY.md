# OctoFlow Dependency & Supply-Chain Security Policy

**Version:** 1.0  
**Effective Date:** 2026-10-31  
**Owner:** Solo Maintainer & Supply-Chain Security  
**Scope:** Core Python package (`octoflow`), optional extras (`[ml]`), development tooling (`[dev]`), and WebGL visualizer (`visualizer/`).

---

## 1. Core Philosophy

OctoFlow adheres to a **minimalist, defense-in-depth dependency philosophy**:
- Every third-party dependency expands the attack surface, increases install footprint, and imposes ongoing maintenance overhead.
- We prefer standard library solutions (e.g., `importlib.metadata`, `json`, `pathlib`, `ast`, `shlex`) over introducing lightweight single-purpose packages.
- Heavy computational dependencies (such as `torch` and `onnxruntime`) are strictly isolated behind optional extras (`[ml]`) and imported lazily at runtime.

---

## 2. Version Pinning Strategy

### 2.1 Package Metadata (`pyproject.toml`)
- **Library Semantics (Ranges Only):** Dependencies in `pyproject.toml` specify only conservative lower bounds (`package>=min_version`) reflecting the earliest API version tested.
- **No Exact Pins in Library Spec:** Exact pinning (`==`) in `pyproject.toml` is prohibited because it artificially restricts downstream users from upgrading or integrating OctoFlow into larger applications.
- **No Speculative Upper Bounds:** Upper bounds (e.g., `<3.0.0`) are forbidden unless an active, verified breaking change has been identified in a major release.

### 2.2 Reproducible Build Artifacts (`requirements.lock` & `package-lock.json`)
- **Deterministic CI & Tests:** Exact versions of all direct and transitive dependencies are locked in `requirements.lock` and `visualizer/package-lock.json`.
- **CI Test Guarantees:** CI test pipelines install from `requirements.lock` (or use `constraints.txt`) to ensure deterministic test execution across runners.
- **Regeneration Command:** Whenever dependencies in `pyproject.toml` change, the lockfile must be regenerated via:
  ```bash
  make lock
  ```

---

## 3. Justification Criteria for New Dependencies

Before proposing any new dependency, the author must address the following checklist in the pull request description:

1. **Necessity Assessment:**  
   Can this capability be implemented in under 100 lines of standard library code or existing utility functions? If yes, inline the implementation rather than adding an external package.
2. **License Compatibility:**  
   The license must be strictly permissive (MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC, or PSF). Copyleft licenses (GPL v1/v2/v3, AGPL, SSPL) are strictly prohibited.
3. **Supply-Chain & Maintainer Health:**  
   - Maintained by a reputable team or foundation.
   - At least 2 active maintainers and commits within the last 6 months.
   - No history of account takeover or malicious release patterns.
4. **Architectural Tiering:**  
   If the package introduces native C/C++ extensions, GPU drivers, or heavy binaries (>10 MB), it **must** be placed in `[project.optional-dependencies]` (e.g., `ml`), not in base `dependencies`.

---

## 4. Maintenance & Security Audit Cadence

- **Weekly Automated Audits:** A GitHub Actions workflow runs every Monday at 04:00 UTC running `pip-audit --fail-on high` and `npm audit --audit-level=high`.
- **Monthly Dependency Bumps:** During the first week of every month, direct dependencies are reviewed for routine minor/patch updates. Bumps are merged only after the full 600+ test suite and visualizer test suite pass.
- **Emergency Zero-Day Protocol:** In the event of an active CVE with known remote exploitation affecting OctoFlow's operational path, an emergency hotfix release is cut within 24 hours.

---

## 5. Vulnerability Exception & Risk Acceptance Process

If `pip-audit` or `npm audit` detects a vulnerability that cannot be immediately remediated (e.g., a dev-only tool with breaking upstream changes):
1. The maintainer must document an accepted-risk entry in [`docs/audit/dependency-exceptions.md`](file:///Users/sachinrk/Desktop/Octoflow%20copy/docs/audit/dependency-exceptions.md).
2. The entry must specify:
   - Package name and affected version range.
   - CVE or GitHub Advisory ID.
   - Operational context explaining why the vulnerability is not exploitable in OctoFlow (e.g., build-time only, unreachable code path).
   - A strict expiry date (maximum 6 months).
3. Any High or Critical vulnerability without an active exception entry blocks release builds.

---

## 6. Audit & Compliance Commands

| Task | Command | Deliverable |
| :--- | :--- | :--- |
| **Regenerate Python Lockfile** | `make lock` | `requirements.lock`, `constraints.txt` |
| **Audit Python Dependencies** | `pip-audit` | Vulnerability list |
| **Audit Frontend Dependencies** | `cd visualizer && npm audit` | NPM advisory list |
| **Generate Third-Party License Report** | `python scripts/generate_licenses.py` | `docs/THIRD_PARTY_LICENSES.md` |
| **Generate CycloneDX v1.5 SBOMs** | `bash scripts/make_sbom.sh` | `dist-artifacts/bom-python.json`, `dist-artifacts/bom-npm.json` |
