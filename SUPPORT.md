# Getting Support for OctoFlow

Thank you for using OctoFlow! Whether you have questions about decentralized 8-arm swarm planning, local LLM inference with Ollama, or custom specialist guilds, here is where to find answers.

---

## Where to Ask Questions

To ensure questions are answered quickly and maintainers are not overwhelmed with issue triage, we separate discussions from bugs:

| Channel | Purpose | Examples |
| :--- | :--- | :--- |
| **[GitHub Discussions](https://github.com/TODO_OWNER_OR_ORG/octoflow/discussions)** | Questions, Advice, Ideas, Showcase | • "How do I optimize local Ollama speed on Apple Silicon?"<br>• "Ideas for a custom data science guild"<br>• "Does the sensory gate work with small 3B models?" |
| **[GitHub Issues](https://github.com/TODO_OWNER_OR_ORG/octoflow/issues)** | Confirmed Bugs & Regressions | • "CLI crashes with traceback on Python 3.12.1"<br>• "E-TOOL-DENIED raised on valid workspace path"<br>• "Git checkpoint fails when stash is dirty" |
| **[Private Security](SECURITY.md)** | Vulnerabilities & Exploits | • Path traversal or sandbox escapes<br>• Outbound credential leakage |

---

## Self-Service Troubleshooting Checklist

Before opening an issue or discussion, check these quick resources:

1. **Run Diagnostics:**
   ```bash
   octoflow doctor
   ```
   Inspects your Python version (>= 3.10), Git repository state, local Ollama daemon reachability, and installed model weights.
2. **Consult the Field Guide:**
   - [Troubleshooting Field Guide](docs/TROUBLESHOOTING.md) covers terminal desync (`stty sane`), port 8088/5173 collisions, Apple Silicon Metal GPU flags, and all 14 `E-*` error codes.
   - [Frequently Asked Questions (FAQ)](docs/FAQ.md) answers common questions about biological metaphors, gating, token costs, and privacy.
   - [Error Code Reference](docs/reference/errors.md) lists actionable next steps for every error code.
3. **Generate a Redacted Bug Report:**
   ```bash
   octoflow bugreport
   ```
   Generates a sanitized environment summary (with all API keys and personal paths masked) ready to paste into an issue.

---

## Response Expectations (Solo Maintainer Reality)

OctoFlow is maintained by an open-source maintainer with community collaboration:
- **Discussions:** Community members often answer questions quickly. Maintainer participation occurs as time permits.
- **Bug Reports & Issues:** Verified bug reports with reproduction steps and `octoflow bugreport` output are prioritized. Expected initial response and triage is within **3 business days**.
- **Commercial / Enterprise SLAs:** OctoFlow does not currently offer commercial SLAs or guaranteed response times.
- **Maintainer Pause Protocol:** If the maintainer needs to step away for scheduled leave, illness, or focus blocks, an advisory banner will be posted on the repository README, and issue triage will be temporarily held without closing issues, per the [Maintainer Operations Manual](docs/MAINTAINING.md#the-maintainer-pause-protocol).
