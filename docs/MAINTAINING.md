# OctoFlow Maintainer Field Guide & Operations Manual

This guide defines the weekly operations routine, triage workflows, burnout guardrails, and release day runbooks for the maintainers of OctoFlow.

---

## 1. The 30-Minute Weekly Maintenance Budget

As a solo maintainer (or small core team), maintenance must be sustainable. Do not keep GitHub notifications open constantly. Batch your maintenance into a single **30-minute weekly block** (e.g. Monday mornings or Friday afternoons):

```text
┌─────────────────────────────────────────────────────────────┐
│ Weekly 30-Minute Triage Allocation                         │
├─────────────────────────────────────────────────────────────┤
│ • 10 minutes: Issue Triage & Routing                       │
│   - Check new issues.                                       │
│   - Ask for missing info using saved replies (needs-repro). │
│   - Label and milestone appropriately.                      │
│                                                             │
│ • 15 minutes: Pull Request Reviews                          │
│   - Review green PRs in priority order.                     │
│   - Merge ready PRs or leave actionable, kind feedback.     │
│                                                             │
│ • 5 minutes: Stale Queue & Discussions Sweep               │
│   - Confirm stale closures are friendly.                   │
│   - Answer quick architectural questions in Discussions.   │
└─────────────────────────────────────────────────────────────┘
```

### First-Response Target
- **Target**: Initial response within **3 business days**.
- **Scope of First Response**: Acknowledgment, appropriate labeling, or requesting reproduction recipes using saved replies. It does *not* mean immediate bug fixes or same-day feature merges.

---

## 2. Issue Triage Routine

When an issue arrives, follow this decision tree:

```text
Is it a Security Report?
 ├── YES -> Apply SECURITY PROTOCOL immediately (never triage in public).
 └── NO  -> Is it a Question / Discussion?
             ├── YES -> Convert to GitHub Discussion using Saved Reply #3.
             └── NO  -> Is it a Bug Report?
                         ├── Missing `octoflow bugreport` or repro? -> Label 'needs-repro', use Saved Reply #1.
                         ├── Duplicate of existing issue? -> Link original, label 'duplicate', use Saved Reply #2.
                         └── Verified Bug -> Label 'bug', assign milestone or 'help wanted'.
```

### PR Review Priority Order
When reviewing open pull requests during your 15-minute review block:
1. **Documentation & Typo Fixes**: Fast merges that immediately help users.
2. **Good First Issues & Seed PRs**: Fast turnaround keeps first-time contributors engaged.
3. **Provider & Specialist Guild Extensions**: Modular additions isolated from core engine.
4. **Core Engine & Architecture Changes**: Require deep review against the 3 Core Moats (Local-first, Truthful receipts, Single-width glyphs).

---

## 3. Stale Issue & PR Policy

OctoFlow adopts a **generous, contributor-friendly stale policy**:

- **Needs-Repro Issues**: If an issue labeled `needs-repro` has had zero activity for **60 days**, the automated stale workflow marks it stale with a friendly notice.
- **Grace Period**: Contributors are given **7 additional days** to reply or provide reproduction details.
- **Closure**: If no response occurs, the issue is closed cleanly.
- **Reopen Guarantee**: All closure notes explicitly state: *"If you can reproduce this later with `octoflow bugreport`, simply leave a comment and we will happily reopen."*
- **Strict Exemptions**: The following are **NEVER** marked stale:
  - Issues labeled `security`
  - Issues labeled `good first issue`
  - Issues labeled `enhancement` on the active roadmap
  - Pinned issues

---

## 4. Release Cadence

- **Patch Releases (`0.3.x`)**: Shipped as needed for bug fixes, test stability, or packaging updates.
- **Minor Releases (`0.4.0`)**: Shipped approximately monthly, aligned with [`ROADMAP.md`](../ROADMAP.md).
- **Pre-Release Verification**: Every release must execute `bash scripts/verify_wheel.sh` and pass `make check-docs`.

---

## 5. Security Vulnerability Handling

If a security issue is reported:
1. **Never triage in public issues**: If a user accidentally reports an exploit, credential leak, or sandbox escape in a public issue, immediately mask the sensitive content and convert the issue into a **GitHub Private Security Advisory**.
2. **Private Advisory Workflow**:
   - Open advisory at `https://github.com/TODO_OWNER_OR_ORG/octoflow/security/advisories/new`.
   - Collaborate on the fix in a private fork branch.
   - Run `pytest -m security` to verify containment.
   - Request CVE through GitHub if applicable.
   - Release coordinated patch release with security advisories credit.

---

## 6. Burnout Guardrails & The Maintainer Pause Protocol

Maintaining open source should never come at the cost of personal well-being.

### Guardrails
- **No Response Guarantees**: `SUPPORT.md` explicitly states that response times may vary.
- **Automated First Interactions**: First-time contributors receive automated welcoming notes so they know their contribution is queued.
- **Zero Notification Push**: Maintainers are encouraged to disable mobile push notifications for repository activity.

### The Maintainer Pause Protocol
If you need to step away for more than two weeks (vacation, family, focus periods, or burnout recovery):
1. **Add README Pause Banner**: Place this alert banner at the very top of `README.md`:
   ```markdown
   > [!NOTE]
   > **Maintainer Notice:** OctoFlow is currently on planned maintenance pause until <DATE>. Issue triage and PR reviews will resume upon return. Automated CI and releases remain accessible.
   ```
2. **Pause Stale Automation**: Temporarily disable `.github/workflows/stale.yml` so issues are not closed while you are away.
3. **Commit the banner**:
   ```bash
   git commit -am "chore: activate maintenance pause banner until <DATE>"
   git push origin main
   ```
4. **Upon Return**: Remove the banner, review the backlog during your normal scheduled block, and thank the community for their patience.

---

## 7. Contributor Ladder & Recognition

OctoFlow encourages community members to take on formal leadership roles:

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Contributor   │ ----> │     Triager     │ ----> │ Core Maintainer │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

1. **Contributor**: Submits documentation fixes, bug reports, custom guilds, or seed issue PRs. Recognized in release notes.
2. **Triager (Triage Role)**:
   - *Requirement*: 3+ merged contributions and consistent, constructive issue interaction.
   - *Privileges*: Issue labeling, assigning milestones, closing duplicates, requesting repros.
3. **Core Maintainer (Write Access)**:
   - *Requirement*: Demonstrated adherence to the zero-emoji policy, security sandbox boundaries, and architecture standards.
   - *Privileges*: Commit access, pull request review & merge rights, release co-signing.
   - Detailed governance principles: [`GOVERNANCE.md`](../GOVERNANCE.md).

---

## 8. Release-Day Checklist & First 72 Hours Plan

### Release Day Checklist
- [ ] Working tree is clean on `main`.
- [ ] `make test-fast` and `pytest -m "not live"` pass.
- [ ] `bash scripts/verify_wheel.sh` passes 100% in an isolated clean-room venv.
- [ ] Version string bumped via `python scripts/release.py bump <patch|minor>`.
- [ ] [`CHANGELOG.md`](../CHANGELOG.md) updated with release date and categorized notes.
- [ ] Commit tagged: `git tag -s v0.3.0 -m "Release v0.3.0"`.
- [ ] Git tag pushed: `git push origin v0.3.0`.
- [ ] Release workflow completes in GitHub Actions.

### First 72 Hours Monitoring Schedule
To avoid refreshing notifications constantly post-launch, monitor feedback at fixed intervals:

| Milestone | When | Action |
| :--- | :--- | :--- |
| **T + 2 Hours** | Launch +2h | Verify PyPI wheel downloads cleanly in a fresh venv. Check Show HN / initial social posts for early installation blockers. |
| **T + 12 Hours**| Launch +12h| Quick sweep of GitHub Issues. Apply `needs-repro` or triage critical blockers. |
| **T + 24 Hours**| Day 1 Close | Check GitHub Discussions Q&A. Triage newcomer PRs. |
| **T + 48 Hours**| Day 2 Close | Review bug reports. If a release blocker is identified, prepare hotfix `v0.3.1`. |
| **T + 72 Hours**| Day 3 Close | Final launch retrospective. Resume standard 30-minute weekly triage cadence. |
