# OctoFlow Privacy Statement & Data Governance

OctoFlow is designed with a strict **local-first, zero-telemetry** privacy architecture. We believe you should always know and control exactly what data stays on your machine and what data leaves it.

---

## 1. Core Privacy Commitments

1. **Zero Phoning Home**: OctoFlow contains **no analytics, no crash reporters, and no telemetry services**. OctoFlow never phones home to any server.
2. **Local Telemetry Only**: Telemetry events for the 3D Visualizer and CLI HUD bind strictly to loopback (`127.0.0.1` / `localhost`). External origins and non-loopback connections are blocked.
3. **Automated Egress Testing**: Network egress isolation is enforced in CI through continuous egress testing (`tests/test_egress_guard.py`), verifying zero non-loopback network calls during mission runs, diagnostics, benchmarking, and reporting.
4. **Scrubbed Cloud Prompts**: When connecting to cloud LLMs, outbound prompts are scanned and sanitized for sensitive credentials before transmission.
5. **No Prompts in Logs**: Standard operational logs and run records store metadata only. Prompts are never persisted in log files or checkpoint metadata.

---

## 2. Local Storage Inventory & Permissions

All local configuration and state reside strictly on your file system with hardened access permissions:

| Artifact | Default Path | Permissions | Purpose & Content |
| :--- | :--- | :--- | :--- |
| **Global Config** | `~/.octoflow/config.json` | `0600` (User RW only) | Default provider, models, scale, themes. Stores API keys in plaintext if OS Keyring is unavailable. |
| **Operational Logs** | `~/.octoflow/logs/octoflow.log` | `0600` (User RW only) | Rotating diagnostic logs (1 MB x 3 backups). All credentials scrubbed via `RedactionFilter`. |
| **Run Metadata** | `~/.octoflow/runs/<run_id>/meta.json` | `0600` (User RW only) | High-level goal, branch tracking, files modified, token counts, timestamps. *No raw prompts or completions.* |
| **Vertical Lobe Memory** | `~/.octoflow/memory/` | `0600` (User RW only) | Hebbian synaptic weights and AST topology heuristics. No workspace code. |
| **Custom Guilds** | `~/.octoflow/guilds/` | `0700` (Dir) / `0600` (File) | User-defined 8-arm morphology definitions (YAML/JSON). |
| **Workspace Cache** | `<workspace>/.octoflow/` | `0700` (Dir) / `0600` (File) | Local session cache and lock files. |
| **Mission Checkpoints** | `<workspace>/.octoflow-mission/` | `0700` (Dir) / `0600` (File) | Git checkpoint branch metadata for atomic rollbacks (`octoflow undo`). |
| **Standalone Reports** | `<workspace>/octoflow-audit-*.html` | Standard file mode | Self-contained HTML audit reports generated upon explicit user request (`octoflow report`). |

---

## 3. API Key Resolution & Storage Hierarchy

When OctoFlow initializes, API credentials are resolved in strict order of precedence:

```mermaid
flowchart TD
    A["API Key Request (e.g. Anthropic, OpenAI)"] --> B{"1. Environment Variable?"}
    B -- Yes --> C["Use Environment Variable (Memory Only)"]
    B -- No --> D{"2. OS Keyring Available & Set?"}
    D -- Yes --> E["Read from OS Keyring (Secure Vault)"]
    D -- No --> F{"3. Config File (~/.octoflow/config.json)?"}
    F -- Yes --> G["Read from Config File (0600)"]
    F -- No --> H["Unset / Prompt Setup"]
```

### Key Storage Options

1. **Environment Variables (Recommended)**: Set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, etc. Keys reside solely in memory and are never written to disk.
2. **OS Keyring (`octoflow[keyring]`)**:
   - Securely stores credentials inside your operating system's native encrypted credential store:
     - **macOS**: Keychain
     - **Linux**: SecretService / DBus
     - **Windows**: Credential Vault
   - Install with: `pip install "octoflow[keyring]"`
   - Interactive configuration: `octoflow setup` detects keyring availability and stores keys safely.
3. **Plaintext File Fallback**:
   - If keyring is not installed or unavailable, `octoflow setup` stores keys in `~/.octoflow/config.json` with strict `0600` permissions.
   - A visible warning is emitted during setup informing you that keys are saved in plaintext format.

---

## 4. Provider Data Transmission

### Local Providers (100% On-Device)
- **Providers**: `ollama`, `mock`, `fake`, `replay`, `custom` (targeting localhost / 127.0.0.1).
- **Network Egress**: **Zero**. Requests communicate over loopback HTTP (`http://localhost:11434`).
- **Prompt Sanitization**: Bypassed for local providers to ensure developer workflows and offline unit tests can inspect raw unmodified prompt data.

### Cloud Providers
- **Providers**: `anthropic`, `openai`, `gemini`, `grok`, `deepseek`.
- **Transmission**: Prompts and system prompts are sent via TLS/HTTPS directly to the provider's official API endpoint.
- **Outbound Redaction Guard**:
  - Before any payload is transmitted to a cloud provider, OctoFlow runs its **Outbound Redactor** over the prompt text.
  - Matches are replaced with stable placeholders (e.g. `[REDACTED:OPENAI_API_KEY]`, `[REDACTED:AWS_ACCESS_KEY]`, `[REDACTED:PRIVATE_KEY]`).
  - Redaction counts are tracked and reported in the CLI run summary and MCP output.
  - Setting: `privacy.redact_outbound` in `~/.octoflow/config.json` (defaults to `true`).
  - Override via environment: `export OCTOFLOW_REDACT_OUTBOUND=0` to disable redaction if desired.

### Supported Outbound Redaction Categories
1. Anthropic API Keys (`sk-ant-...`)
2. OpenAI API Keys (`sk-...`, `sk-proj-...`)
3. GitHub Personal Access & OAuth Tokens (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)
4. AWS Access Key IDs (`AKIA...`, `ASIA...`)
5. AWS Secret Access Keys (`aws_secret_access_key='...'`)
6. Google AI & Maps Keys (`AIza...`)
7. Stripe Live & Test Keys (`sk_live_...`, `rk_live_...`)
8. Slack Bot & User Tokens (`xoxb-...`, `xoxp-...`)
9. PEM Private Key Blocks (`-----BEGIN RSA PRIVATE KEY-----`)
10. Authorization & Bearer Tokens (`Authorization: Bearer <token>`)
11. JSON Web Tokens (`eyJ...`)
12. Credit Card Numbers (Luhn-compliant 13-16 digits)

---

## 5. Redaction Guarantees & Limitations

### What Outbound Redaction Guarantees
- Common high-risk credentials, secrets, API tokens, and private keys found in workspace files, environment files, or prompt templates will not be transmitted in plaintext to remote LLM providers.
- Normal programming constructs, variable names, regex expressions, and loopback IP addresses (`127.0.0.1`) are preserved without false-positive corruption.

### What Outbound Redaction Does Not Guarantee
- Bespoke internal identifiers, custom token formats, proprietary business algorithms, or confidential project domain logic that does not match standard secret patterns cannot be automatically detected by regex.
- For complete confidentiality of sensitive workspace code, use **Ollama** (`--provider ollama`) to keep all inference completely on-device.

---

## 6. How to Delete All Stored Data

You have complete control over local data. You can delete all OctoFlow state at any time.

### Automated Purge Command

OctoFlow provides an interactive `purge` command:

```bash
# Preview all stored OctoFlow files and reclaimable space without deleting anything
octos purge --dry-run

# Interactively review and confirm deletion of global and workspace data
octos purge

# Skip confirmation prompt (useful in CI or scripted environments)
octos purge --yes

# Purge only workspace artifacts (.octoflow, .octoflow-mission, reports)
octos purge --workspace-only

# Purge only global user data (~/.octoflow)
octos purge --global-only
```

### Manual Command-Line Deletion

If you prefer to delete everything manually using standard shell commands:

```bash
# 1. Remove all global configuration, logs, runs, and Hebbian memory
rm -rf ~/.octoflow

# 2. Remove workspace cache and mission checkpoints in current project
rm -rf .octoflow .octoflow-mission

# 3. Remove generated standalone HTML reports and benchmark summaries
rm -f octoflow-audit-*.html octoflow-report-*.html octoflow-bench-*.json octoflow-bench-*.md
```

---

## 7. Public Metrics & Voluntary Feedback

OctoFlow tracks project health and community responsiveness without sacrificing user privacy:

1. **Still Zero Telemetry**: OctoFlow has no telemetry in current or future releases. There is no phone-home mechanism, no unique machine identifier, and no background reporting.
2. **Public Registry & Repository Metrics**: Project adoption is estimated exclusively through public, non-identifying aggregate data:
   - PyPI download counts (via `pypistats.org`, analyzing clean installs without automated mirror traffic).
   - GitHub API statistics (issues, pull requests, release intervals, and CI pass rates).
   - Full methodology: [`docs/METRICS.md`](METRICS.md).
3. **Voluntary Feedback (`octoflow feedback`)**:
   - Feedback submission is 100% voluntary and user-initiated.
   - The CLI command performs **zero network requests**; it constructs a prefilled URL and opens it in your local browser (or prints it to stdout).
   - If you opt in to attaching diagnostic output (`--diagnostics`), the sanitized report is displayed for your inspection before URL generation.
4. **Post-Run Feedback Hint**:
   - A single-line hint (`Did this work? Run 'octoflow feedback'`) appears at most once on interactive runs.
   - You can permanently disable this hint by running:
     ```bash
     octoflow config set ui.show_feedback_prompt false
     ```
   - Or by setting the environment variable: `export OCTOFLOW_NO_FEEDBACK_PROMPT=1`.

