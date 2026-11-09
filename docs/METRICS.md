# OctoFlow Privacy-Preserving Metrics Guide & Dashboard

This document outlines the metrics philosophy, targets, automated reporting tooling, and qualitative feedback loops for OctoFlow.

---

## 1. Zero-Telemetry Analytics Philosophy

OctoFlow adheres to a strict **privacy-first, zero-telemetry** architecture:
- **No In-App Analytics:** OctoFlow contains zero analytics libraries, zero tracking cookies, zero user fingerprinting, and zero telemetry ping endpoints.
- **Local Loopback Only:** Local UI and telemetry servers bind strictly to `127.0.0.1` and are continuously verified via automated egress isolation tests (`tests/test_egress_guard.py`).
- **Public Metadata Only:** All project health metrics are collected solely from public package registries (PyPI) and public repository activity (GitHub).
- **Voluntary Feedback:** Qualitative user feedback is collected exclusively when a user intentionally runs `octoflow feedback` or participates in GitHub Discussions.

---

## 2. Metrics That Matter & Maintainer Targets

To ensure maintainer sustainability (Assumption A1: solo maintainer or small core team) and high community responsiveness, we focus on four primary operational targets:

| Focus Area | Operational Metric | Target SLA | Why It Matters |
| :--- | :--- | :--- | :--- |
| **Responsiveness** | Median First-Response Time | **$\le 72$ hours (3 days)** | Prevents contributors and bug reporters from stalling without overloading maintainers. |
| **Contributor Retention** | Repeat Contributors ($\ge 2$ Merged PRs) | **$\ge 2$ contributors** | Measures whether newcomers find the codebase welcoming enough to return for a second contribution. |
| **Project Velocity** | Release Cadence | **Monthly ($\le 35$ days)** | Consistent, predictable cadence for shipping bug fixes, new specialist guilds, and provider integrations. |
| **Build Stability** | CI Workflow Pass Rate | **$\ge 95.0\%$** | Keeps `main` pristine, ensuring clean-room installs and verifiable releases. |

---

## 3. The Vanity Metric Traps

Maintainers must not confuse popularity with utility. We explicitly reject treating the following as success criteria:

### A. The GitHub Stars Trap
- **The Trap:** Counting GitHub stars as a measure of user adoption or product quality.
- **Why It Misleads:** Stars measure social curiosity, Hacker News spikes, and bookmarking intent. A repository can accumulate thousands of stars while having zero active daily users, or have 200 stars while running critical production pipelines.
- **Policy:** Stars are noted as informational metadata only. They are never used as OKRs, release gates, or roadmap priorities.

### B. The PyPI Download Count Trap
- **The Trap:** Celebrating large raw PyPI download spikes.
- **Why It Misleads:** Up to 60-80% of raw PyPI downloads stem from automated Docker container image rebuilds, cloud CI/CD pipelines (e.g. GitHub Actions, GitLab CI), package index scrapers, and global mirrors (Bandersnatch).
- **Policy:** Track the `without_mirrors` download category via the `pypistats.org` API to observe genuine weekly installation trends, rather than aggregate download totals.

---

## 4. The Qualitative Feedback Loop

Because OctoFlow does not phone home, qualitative user feedback is solicited through voluntary, user-initiated channels:

### 1. `octoflow feedback` Command
Users can provide feedback directly from their terminal:
```bash
# Open a prefilled general feedback issue in default browser
octoflow feedback

# Report a bug with optional sanitized environment diagnostics
octoflow feedback --category bug --diagnostics

# Propose an idea or feature request
octoflow feedback --category idea

# Print the prefilled issue URL without launching browser (useful over SSH)
octoflow feedback --no-browser
```

**Privacy Guarantees for `octoflow feedback`:**
- **Zero Background Calls:** The command performs zero HTTP requests or socket connections.
- **Diagnostics Preview:** If environment diagnostics are attached, they are rendered in the console first for explicit user inspection and confirmation.
- **Automatic Scrubbing:** All API keys, passwords, bearer tokens, and private paths are masked before URL generation.

### 2. One-Time Post-Run Hint
After a live mission or guided onboarding completes, OctoFlow displays a polite one-line hint at most once:
```text
• Did this work? Run 'octoflow feedback' to share feedback or report issues (voluntary, zero telemetry).
```
- **Shown at most once:** Once displayed, `feedback_prompted` is recorded as `true` in `~/.octoflow/config.json`.
- **Suppressible via config:**
  ```bash
  octoflow config set ui.show_feedback_prompt false
  ```
- **Suppressible via environment:**
  ```bash
  export OCTOFLOW_NO_FEEDBACK_PROMPT=1
  ```
- **Silent in automated environments:** Automatically suppressed in non-interactive sessions (`OCTOFLOW_NONINTERACTIVE=1`), piped output, or non-TTY terminals.

### 3. GitHub Discussions ("Show and tell")
Community members are invited to share custom specialist rosters (`GuildSpec`), benchmark results, and production workflows in the **Show and tell** category of GitHub Discussions.

---

## 5. Generating Metrics

### Local Execution
Maintainers can generate updated metrics at any time using [`scripts/metrics.py`](../scripts/metrics.py):
```bash
# Run with optional GitHub token for higher rate limits
export GITHUB_TOKEN="ghp_..."
python scripts/metrics.py --repo TODO_OWNER_OR_ORG/octoflow --package octoflow

# Offline execution with test fixtures
python scripts/metrics.py --fixture tests/fixtures/metrics_sample.json
```
This produces:
- `METRICS.md`: Formatted Markdown dashboard.
- `metrics.json`: Raw machine-readable JSON metrics.

### Automated CI Scheduling
Metrics collection can be automated via a weekly GitHub Actions workflow that writes an artifact (never auto-committing directly to git history):
```yaml
name: Weekly Public Metrics

on:
  schedule:
    - cron: '0 4 * * 1' # Every Monday at 04:00 UTC
  workflow_dispatch:

permissions:
  contents: read

jobs:
  collect-metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Generate Public Metrics Dashboard
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/metrics.py --repo ${{ github.repository }} --package octoflow
      - name: Upload Metrics Artifact
        uses: actions/upload-artifact@v4
        with:
          name: public-metrics
          path: |
            METRICS.md
            metrics.json
```

---

## 6. Sample Metrics Dashboard (Sample Demonstration)

Below is a representative sample output generated by `scripts/metrics.py` from standardized benchmark fixtures:

```markdown
<!-- SAMPLE OUTPUT: DO NOT USE FOR PRODUCTION COMPLIANCE AUDITING -->

# OctoFlow Privacy-Preserving Metrics Dashboard (Sample)

> [!NOTE]
> Zero Telemetry Commitment: OctoFlow contains no phoning home, no analytics code, and no user tracking.
> All metrics in this report are computed strictly from public package registries (PyPI) and public repository activity (GitHub).

Report Generated: 2026-11-09T18:00:00+00:00 | Target Repository: octoflow/octoflow

---

## 1. Executive Summary & Maintainer Targets

| Focus Area | Metric | Current Value | Target SLA | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Responsiveness** | Median First Response | `18.5 hours` | <= 72 hours (3 days) | Target Met |
| **Retention** | Contributors with 2+ PRs | `4` | >= 2 contributors | Target Met |
| **Cadence** | Median Release Interval | `28.0 days` | Monthly (<= 35 days) | Target Met |
| **Quality** | CI Build Pass Rate | `98.2%` | >= 95.0% | Target Met |

---

## 2. Adoption & Package Downloads

- **PyPI Package:** [`octoflow`](https://pypi.org/project/octoflow/)
- **Downloads (Last 30 Days):** `1,842`
- **Downloads (Last 7 Days):** `486`
- **Downloads (Last 24 Hours):** `74`
- **Clean Installs (Without Automated Mirrors):** `1,290`
- **Organic / Mirror Ratio:** `0.70`

---

## 3. Community Responsiveness & Triage

- **Open Issues:** `6`
- **Closed Issues:** `42`
- **Median First Response Time:** `18.5 hours` (Target: <= 72 hours)
- **Median Bug Time-to-Close:** `4.2 days`
- **Median PR Merge Time:** `22.4 hours`

---

## 4. Contributor Health & Velocity

- **Repeat Contributors (>= 2 Merged PRs):** `4`
- **New Contributors (Last 90 Days):** `7`
- **Open Pull Requests:** `3`
- **Merged Pull Requests:** `31`
- **Total Public Releases:** `3`
- **Median Days Between Releases:** `28.0 days`
- **CI Suite Pass Rate:** `98.2%` (across `56` completed runs)

---

## 5. Vanity Metrics (Informational Only)

- **GitHub Stars:** `312`
- **GitHub Forks:** `28`
```

