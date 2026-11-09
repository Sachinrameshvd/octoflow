# Security Policy

OctoFlow treats developer workstation security and privacy as non-negotiable core principles. Because OctoFlow executes autonomous multi-agent code generation and spawns child processes locally, we employ rigorous defense-in-depth confinement.

---

## Supported Versions

Security updates are actively provided for the current and immediately preceding minor release:

| Version | Supported | Security Policy |
| :--- | :---: | :--- |
| `0.3.x` | Yes | Active development and high-priority security patches |
| `0.2.x` | Critical Only | Critical security fixes until 0.4.0 release |
| `< 0.2.0` | No | Unsupported; please upgrade to the latest stable release |

---

## Reporting a Vulnerability

**Please do NOT file public GitHub issues for security vulnerabilities.**

If you discover a security issue or potential vulnerability in OctoFlow, please report it through one of the following confidential channels:

1. **GitHub Security Advisory (Preferred):**
   Navigate to the repository on GitHub, open the **Security** tab, select **Advisories**, and click **Report a vulnerability**. This creates a private draft advisory where we can discuss the issue and collaborate on a fix confidentially.
2. **Encrypted / Private Email (Fallback):**
   Send an email with subject line `[SECURITY] OctoFlow Vulnerability Report` to:  
   `[TODO: INSERT SECURITY EMAIL HERE, e.g. security@octoflow.dev]`

### What to Include in Your Report
To help us investigate and remediate the issue quickly, please include:
- A clear description of the vulnerability and potential impact.
- Step-by-step reproduction instructions or a minimal, self-contained Proof of Concept (PoC).
- The operating system, architecture (e.g. macOS Apple Silicon, Linux x86_64, Windows), Python runtime version, and OctoFlow version (`octoflow --version`).
- Any configuration options, execution mode (`LIVE` vs `DRY-RUN`), or provider settings relevant to the bug.
- (Optional) Suggested remediation or patch.

---

## Response Targets (Solo Maintainer Reality)

OctoFlow is maintained by an open-source maintainer with active community support. We hold ourselves to realistic, transparent response targets:

- **Initial Acknowledgment:** Within **7 business days** of receiving your report.
- **Triage & Validation:** Within **14 business days** confirming vulnerability reproduction and assigning severity.
- **Fix & Coordinated Release:** Target within **30 to 90 days** depending on remediation complexity.

We will keep you informed of our progress as we prepare and verify the security patch.

---

## Coordinated Disclosure Policy

We follow standard coordinated vulnerability disclosure:
1. We ask reporters to maintain confidentiality and refrain from public disclosure until an official patched release is available or the agreed-upon disclosure window has elapsed (standard 90-day window).
2. Once a fix is released, we publish a GitHub Security Advisory detailing the issue, CVE (if assigned), affected versions, and give full public credit to the reporter (unless anonymity is requested).

---

## Technical Security Architecture Documentation

For details on OctoFlow's underlying security architecture, consult:
- **Tool Sandbox Confinement:** [`docs/SECURITY.md`](docs/SECURITY.md) (canonical path resolution, symlink hierarchy traversal defenses, subprocess execution policies).
- **Telemetry Server Security:** [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md) (loopback binding, WebSocket origin validation, DNS-rebinding defenses).
- **STRIDE Threat Model:** [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) (comprehensive threat analysis across all 6 STRIDE dimensions).
- **Privacy & Egress Isolation:** [`docs/PRIVACY.md`](docs/PRIVACY.md) (zero phoning home, credential redaction patterns, loopback verification).
