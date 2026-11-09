# OctoFlow Dependency Vulnerability Exceptions & Risk Acceptance

**Audit Date:** 2026-10-31  
**Reviewer:** Supply-Chain Security Engineer  
**Policy Reference:** [`docs/DEPENDENCY_POLICY.md`](../DEPENDENCY_POLICY.md)  
**Standard:** Every High/Critical vulnerability detected by `pip-audit` or `npm audit` that cannot be immediately bumped without breaking changes must have an approved exception with a concrete justification, compensating controls, and a strict expiry date.

---

## 1. Active Vulnerability Exceptions Table

| Exception ID | Package | Ecosystem | Affected Version | Fixed In | Severity | Advisory / CVE | Reasoning & Compensating Controls | Expiry Date | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-DEP-01** | `certifi` | PyPI | `2026.7.22` | `2026.10.18` | **High** | `PYSEC-2026-4320` | Root certificate authority trust store update. Used by `httpx` for TLS verification. In OctoFlow, all external LLM provider connections are encrypted via TLS and restricted to Anthropic/OpenAI endpoints; no custom/rogue CAs are loaded. Locked to `>=2026.10.18` in constraints when updating upstream wheels. | 2027-04-30 | **Accepted Risk** |
| **SEC-DEP-02** | `filelock` | PyPI | `4.0.4` | `4.2.1` | **High** | `CVE-2026-112940`, `CVE-2026-112913`, `CVE-2026-112907`, `CVE-2026-112938` | Local lock file race condition and symlink manipulation vulnerabilities. In OctoFlow, `filelock` is pulled transitively by `setuptools` and `huggingface/torch` caches. Lock files are placed in user-owned `~/.cache` with strict `0700` directories. No multi-tenant shared temp directory (`/tmp`) locks are evaluated. | 2027-04-30 | **Accepted Risk** |
| **SEC-DEP-03** | `pillow` | PyPI | `12.3.0` | `13.0.0` | **High** | `CVE-2026-112895`, `CVE-2026-112400`, `CVE-2026-112395`, `CVE-2026-112404` | Memory corruption and buffer over-read in image format decoders (TIFF, BMP, WebP). In OctoFlow, `pillow` is a dev-only dependency pulled by `matplotlib` for offline benchmark chart generation. It is never exposed to untrusted user-uploaded images, web request payloads, or WebSocket streams. | 2027-04-30 | **Accepted Risk** |
| **SEC-DEP-04** | `minimatch` | npm | `<11.0.1` | `11.0.1` | **Moderate** | `GHSA-g3hv-75wg-m249` | ReDoS (Denial of Service) via globparts amplification in path matching. `minimatch` is a devDependency used exclusively by `eslint` during local build/lint time (`npm run lint`). It is not bundled into the production visualizer distribution artifacts (`octoflow/dist/`). Running `npm audit fix --force` would downgrade ESLint to v4 (breaking change). | 2027-04-30 | **Accepted Risk** |

---

## 2. Review and Expiry Protocol

1. **Monthly Review:** At the first sprint of every month, run `pip-audit` and `cd visualizer && npm audit` to evaluate whether upstream patches have resolved any of the above items without breaking changes.
2. **Hard Expiry:** If an exception reaches its **Expiry Date** without being resolved or renewed with updated reasoning, CI builds will fail the audit gate until bumped or reassessed.
3. **Emergency Revocation:** If an active in-the-wild remote exploit is published affecting a component in OctoFlow's operational path, the exception is immediately revoked and an emergency bump is released.
