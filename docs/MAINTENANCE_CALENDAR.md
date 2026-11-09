# OctoFlow Post-Launch Maintenance Cadence & 90-Day Plan

This document establishes the structured maintenance routines, operational calendars, and strategic decision gates for the first 90 days following public release.

---

## 1. Time Budget Alignment

To ensure long-term maintainer sustainability (Assumption A1: solo maintainer or small team), all maintenance tasks are scheduled in batched blocks adhering to the budget defined in [`docs/MAINTAINING.md`](MAINTAINING.md):

```text
┌─────────────────────────────────────────────────────────────┐
│ Maintenance Cadence Time Allocation                        │
├─────────────────────────────────────────────────────────────┤
│ • Weekly Routine:    30 minutes / week                      │
│ • Monthly Routine:   60 minutes / month                     │
│ • Quarterly Routine: 120 minutes / quarter                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Weekly Maintenance Routine (30 Minutes / Week)

**Recommended Window:** Monday mornings (09:00 - 09:30) or Friday afternoons.

```text
┌─────────────────────────────────────────────────────────────┐
│ Weekly 30-Minute Maintenance Breakdown                      │
├─────────────────────────────────────────────────────────────┤
│ 1. 10 mins — Issue Triage & Routing                         │
│    • Check new issues.                                      │
│    • Apply Saved Reply #1 for missing `octoflow bugreport`. │
│    • Route questions to GitHub Discussions.                 │
│                                                             │
│ 2. 15 mins — Pull Request Reviews                           │
│    • Review Dependabot / security dependency updates.       │
│    • Review green contributor PRs (docs -> seed -> core).   │
│    • Merge passing PRs adhering to the zero-emoji policy.   │
│                                                             │
│ 3. 5 mins — Stale Queue & Discussion Sweep                  │
│    • Review issues flagged by `.github/workflows/stale.yml`.│
│    • Answer quick technical questions in Discussions.       │
└─────────────────────────────────────────────────────────────┘
```

### Automated Weekly Workflows
- **Dependency Vulnerability Scan**: [`.github/workflows/audit.yml`](../.github/workflows/audit.yml) (Runs Mondays at 04:00 UTC via `pip-audit` and `npm audit`).
- **Stale Issue Sweep**: [`.github/workflows/stale.yml`](../.github/workflows/stale.yml) (Runs Mondays at 00:00 UTC).

---

## 3. Monthly Maintenance Routine (60 Minutes / Month)

**Recommended Window:** First Monday of each month.

### 1. Provider Drift & Benchmark Sanity (15 Mins)
- Upstream LLM provider APIs (Anthropic, OpenAI, Gemini) and local Ollama model weights change frequently.
- Run the automated provider contract suite against recorded fixtures:
  ```bash
  pytest tests/contract/ -v
  ```
- Run the monthly benchmark harness sanity run:
  ```bash
  python -m octoflow.cli bench --fake --task all -n 1 --out /tmp/monthly_bench
  ```
- Automated via: [`.github/workflows/monthly-cadence.yml`](../.github/workflows/monthly-cadence.yml) (Runs 1st of every month at 02:00 UTC).

### 2. Public Metrics & SLA Review (15 Mins)
- Run [`scripts/metrics.py`](../scripts/metrics.py) to generate the monthly health report:
  ```bash
  python scripts/metrics.py --repo TODO_OWNER_OR_ORG/octoflow --package octoflow
  ```
- Review the four maintainer SLA targets:
  - First-response time $\le 72$ hours (3 days).
  - Contributor retention: $\ge 2$ contributors with 2+ merged PRs.
  - Release cadence: $\le 35$ days between releases.
  - CI build pass rate: $\ge 95.0\%$.

### 3. Local Model Benchmark Verification (15 Mins)
- Rerun a live benchmark against the primary local coding model (`qwen2.5-coder:7b` via local Ollama):
  ```bash
  octoflow bench --task rate_limiter --model ollama --out benchmarks/results/monthly/
  ```
- Verify token gating efficiency ($\ge 30\%$ token reduction in gated vs. ungated mode).
- Append updated benchmark receipts to [`docs/BENCHMARKING.md`](BENCHMARKING.md).

### 4. Release Cadence (15 Mins)
- If bug fixes or new features have accumulated, cut a release following [`docs/RELEASING.md`](RELEASING.md):
  ```bash
  python scripts/release.py bump <patch|minor>
  git push origin --tags
  ```

---

## 4. Quarterly Maintenance Routine (120 Minutes / Quarter)

**Recommended Window:** End of Q1, Q2, Q3, and Q4.

### 1. Threat Model & Security Audit Review (30 Mins)
- Review [`docs/THREAT_MODEL.md`](THREAT_MODEL.md) against newly added tools, commands, or server endpoints.
- Confirm loopback bind guarantees (`127.0.0.1`), WebSocket Origin validation, and path confinement sandbox checks.
- Verify security test suite:
  ```bash
  pytest -m security
  ```

### 2. Dependency Policy & Lockfile Refresh (30 Mins)
- Audit third-party packages against [`docs/DEPENDENCY_POLICY.md`](DEPENDENCY_POLICY.md).
- Verify license compliance (only OSI-approved permissive licenses; no GPL/copyleft).
- Update lockfiles with minimal churn:
  ```bash
  make lock
  ```

### 3. Roadmap & "Do Not Do Yet" Re-evaluation (60 Mins)
- Review [`ROADMAP.md`](../ROADMAP.md) progress for the current release horizon.
- Re-evaluate the **Not Planned** list against concrete, empirical community evidence (see Day 60 Decision Gate below).

---

## 5. The 90-Day Post-Launch Plan

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ The First 90 Days Post-Launch Timeline                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Days 1–7:   Launch Stabilization & Hotfixes (v0.3.1)                        │
│ Days 8–30:  Contributor Onboarding & Seed Issues                           │
│ Days 31–60: Mid-Quarter Cadence & Day 60 Decision Gate                      │
│ Days 61–90: Minor Release v0.4.0 & Scope Realignment                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Days 1–7 — Launch Stabilization & Hotfixes
- **Objective:** Fix early onboarding friction and edge-case environment crashes without introducing architectural changes.
- **Actions:**
  - Execute 72-hour launch monitoring schedule (check-ins at $T+2\text{h}$, $T+12\text{h}$, $T+24\text{h}$, $T+48\text{h}$, $T+72\text{h}$).
  - Triage early bug reports from Show HN, Reddit, or social announcements.
  - Ship patch release `v0.3.1` if installation blockers, PTY desync, or packaging issues are identified.

### Phase 2: Days 8–30 — Contributor Onboarding & Seed Issues
- **Objective:** Empower the first wave of outside contributors and maintain fast review turnaround.
- **Actions:**
  - Guide first-time contributors toward [`docs/seed-issues/`](seed-issues/) (e.g. adding custom specialist guilds, LM Studio provider adapters).
  - Enforce the zero-emoji policy and truthful token receipt standards in PR reviews.
  - Conduct Month 1 metrics sweep (`python scripts/metrics.py`).

### Phase 3: Days 31–60 — Mid-Quarter Cadence & Day 60 Decision Gate
- **Objective:** Maintain steady cadence and critically evaluate deferred features using empirical user data.
- **Actions:**
  - Run Month 2 provider drift and benchmark sanity check.
  - **Day 60 Decision Gate:** Evaluate the "Do Not Do Yet" list against real evidence:
    - *Decision Gate A: Windows Native Console*:
      - *Question:* Did $\ge 15\%$ of all filed bug reports and discussions request native Windows Console (non-WSL)?
      - *Verdict:* If yes, initiate an ADR to explore a Windows termios emulation layer (e.g. `ctypes` Win32 Console API); if no, reaffirm WSL2 as the supported path and keep native Windows out of scope.
    - *Decision Gate B: 64-Arm Swarm Default*:
      - *Question:* Did users or benchmark suites demonstrate $> 15\%$ higher code quality or speed with 64 arms on single-repository tasks?
      - *Verdict:* If no, keep the elastic autoscaler (`--octos auto`) provisioned at 8 to 24 arms to prevent wasteful token burn.
    - *Decision Gate C: WAN Multi-Machine Federation*:
      - *Question:* Did users demand cross-network swarm clustering with cryptographic trust boundaries?
      - *Verdict:* If no, maintain strict loopback isolation (`127.0.0.1`) and defer WAN federation until v1.0.

### Phase 4: Days 61–90 — Minor Release v0.4.0 & Scope Realignment
- **Objective:** Deliver the first scheduled feature release and retire deprecated options.
- **Actions:**
  - Finalize `v0.4.0` features (e.g. LM Studio local provider, data science specialist guild).
  - Execute scheduled deprecation removals per [`docs/SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md) (e.g. `OCTOFLOW_LEGACY_CONFIG`).
  - Conduct quarterly threat model and dependency review.
  - Ship `v0.4.0` with categorized changelog notes and truthful benchmark receipts.
