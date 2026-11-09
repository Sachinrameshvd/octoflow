## Description
<!-- Provide a clear, concise summary of the changes introduced in this pull request and the problem they solve. -->

## Related Issues
<!-- Link to any relevant issues or discussions (e.g. Closes #123, Ref #456). -->

## Type of Change
<!-- Mark the relevant options with an 'x'. -->
- [ ] `fix`: Bug fix (non-breaking change which fixes an issue)
- [ ] `feat`: New feature or specialist capability (non-breaking change)
- [ ] `perf`: Performance improvement (reduced token usage or faster wall time)
- [ ] `docs`: Documentation updates, tutorials, or reference guides
- [ ] `refactor`: Code reorganization with no change in observable behavior
- [ ] `test`: New tests or test infrastructure improvements
- [ ] `breaking`: Breaking change (alters public CLI contracts, exit codes, or configuration schema)

---

## Contributor Quality Checklist
<!-- Please ensure all checks pass before requesting review. -->
- [ ] **Branch Naming:** My branch follows the `octos/<feature-name>` convention.
- [ ] **Unit Tests:** All new and existing tests pass locally (`make test` or `make test-fast`).
- [ ] **Lint & Format:** Code conforms to Ruff standards (`ruff check .` and `ruff format --check .`).
- [ ] **Type Safety:** Core modules pass gradual typechecking (`mypy`).
- [ ] **Documentation & References:**
  - [ ] Generated references are synchronized (`make docs-ref` and `make check-docs-ref`).
  - [ ] Documentation integrity checker reports zero broken links or anchors (`make check-docs`).
- [ ] **The Hard Rules:**
  - [ ] **Cockpit Non-Blocking:** No blocking `input()`, `sys.stdin.read()`, or sleeping loops inside cockpit / TUI code.
  - [ ] **Zero Emoji & Single-Width Glyphs:** Terminal characters are looked up via `octoflow/glyphs.py` (`wcwidth <= 1`). Zero wide emoji characters in terminal output or documentation.
  - [ ] **Truthful Outcomes:** No silent mock fallbacks during live execution; runs with zero changes report `FAILED` with exit code 2.
  - [ ] **Secrets & Privacy:** No real API keys, bearer tokens, or personal paths in code, logs, or test fixtures. All outputs pass through `redact_secrets()`.
  - [ ] **Dependency Policy:** Any new dependency adheres to [`docs/DEPENDENCY_POLICY.md`](../docs/DEPENDENCY_POLICY.md) (permissive license, lower bound only, lockfile updated via `make lock`).
- [ ] **Changelog:** Added an entry to [`CHANGELOG.md`](../CHANGELOG.md) under `[Unreleased]` following Keep a Changelog.
