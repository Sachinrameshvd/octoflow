# OctoFlow Maintainer Saved Replies

Use these pre-drafted responses in GitHub issues, pull requests, and discussions to maintain polite, consistent, and time-efficient community communication.

---

## 1. Needs Reproduction (`needs-repro`)

**When to use:** A bug report lacks reproducible steps, code examples, or diagnostic doctor output.

```markdown
Thank you for reporting this issue!

To help us diagnose and resolve this quickly, could you please provide a minimal reproduction recipe?

Specifically:
1. Run `octoflow bugreport` in your terminal and paste the sanitized diagnostic output here (all API keys and personal paths are automatically masked).
2. Share a minimal terminal command or workspace snippet that reproduces the issue.
3. If using local models, specify the exact model tag (e.g. `ollama list`).

We have labeled this issue `needs-repro`. Once you provide these details, we will gladly investigate!
```

---

## 2. Duplicate (`duplicate`)

**When to use:** An issue reports a problem or feature already tracked in an existing issue.

```markdown
Thank you for opening this!

This appears to be a duplicate of #{ISSUE_NUMBER}, where we are already tracking this behavior and discussing solutions.

I am going to close this issue to keep discussion and updates consolidated in one place. Please feel free to subscribe or add any additional context to #{ISSUE_NUMBER}!
```

---

## 3. Out of Scope / Not Planned (`wontfix`)

**When to use:** A feature proposal conflicts with core moats (e.g., asking for cloud-hosted central tracking, GUI bloat, or wide emoji icons) or is listed in the "Not Planned" section of `ROADMAP.md`.

```markdown
Thank you for the proposal and for sharing your ideas with the community!

After careful consideration against our project scope and architecture principles, we have decided not to accept this proposal.

As outlined in our [Roadmap (Not Planned)](../ROADMAP.md#not-planned), OctoFlow is strictly focused on:
- Local-first execution with zero non-loopback network egress
- Truthful token receipts and deterministic event-triggered gating
- Single-width terminal accessibility

Adding this feature would introduce external service dependencies or expand the maintenance scope beyond what a small core team can sustainably support.

Thank you again for your interest in OctoFlow!
```

---

## 4. First Pull Request Welcome

**When to use:** A contributor submits their first PR to the repository.

```markdown
Welcome to the OctoFlow community, and thank you for your pull request!

Automated CI checks (Ruff linting, mypy typechecking, unit tests, and documentation link verification) are currently running.

While we review your changes:
- Please ensure your branch follows the `octos/<feature>` convention.
- Verify that terminal text and documentation adhere to our zero-emoji policy (`wcwidth <= 1`).
- Check that any new tests run cleanly via `make test-fast`.

A maintainer will review your pull request during our scheduled weekly review block. Thank you for helping build OctoFlow!
```

---

## 5. Security Vulnerability Redirect

**When to use:** A user posts potential security vulnerabilities, path traversal proofs, or credential leakage in a public GitHub issue.

```markdown
Thank you for bringing this to our attention.

To protect users and adhere to responsible disclosure practices, we do not discuss or triage potential security vulnerabilities in public issues.

I have masked the sensitive details in your comment. Please submit the full report privately via:
- GitHub Private Advisory: https://github.com/TODO_OWNER_OR_ORG/octoflow/security/advisories/new
- Security Policy: https://github.com/TODO_OWNER_OR_ORG/octoflow/blob/main/SECURITY.md

We will review your submission promptly in a private advisory workspace. Thank you for keeping OctoFlow safe!
```

---

## 6. DRY-RUN Simulation Confusion Explanation

**When to use:** A user reports that running `octoflow run --dry-run` or `--model mock` did not write any files to disk or spent 0 provider tokens.

```markdown
Hello! This behavior is expected and working as designed.

When running with `--dry-run`:
1. **Simulation Mode**: The swarm executes the planning and decomposition phases against simulated mock models.
2. **Zero File Modification**: Dry-run mode never writes, modifies, or deletes files in your workspace (`files_written = 0`).
3. **Truthful Zero-Token Receipt**: Because mock providers do not incur live API or inference token consumption, the receipt truthfully reports `Spent: 0 provider tokens (dry-run: simulation)`.

To perform a live autonomous mission that creates real files and executes real commands:
- With local Ollama:
  ```bash
  octoflow run "Your engineering goal" --model ollama
  ```
- With Anthropic Claude:
  ```bash
  export ANTHROPIC_API_KEY="your-key"
  octoflow run "Your engineering goal" --model anthropic
  ```

For more details on truthful receipts and execution modes, see our [Truthful Token Receipt Guide](receipt.md).
```
