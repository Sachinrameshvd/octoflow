# Author Tutorial: "Adding a Custom Tool to an Arm"

**Difficulty:** Good First Issue  
**Labels:** `docs`, `good first issue`  
**Mentoring Pointer:** Look at existing tutorials in [`docs/tutorials/`](../tutorials/) (e.g., [`04-building-with-a-custom-guild.md`](../tutorials/04-building-with-a-custom-guild.md) and [`05-adding-a-custom-provider.md`](../tutorials/05-adding-a-custom-provider.md)).

---

## Context
OctoFlow's 8 arms execute tasks using sandboxed tools defined in [`octoflow/tools.py`](../../octoflow/tools.py) (e.g. `write_file`, `read_file`, `execute_command`, `git_commit`).

Community developers frequently ask how to expose domain-specific tools to their swarms (such as an SQLite inspector, an HTTP client, or an OpenAPI linter). Writing a focused, under-10-minute tutorial will empower developers to extend OctoFlow's tool capabilities safely.

---

## Objectives & Requirements
1. Create a new markdown tutorial file: `docs/tutorials/09-adding-a-custom-tool.md`.
2. Follow the established tutorial format:
   - Header metadata (Time: <10 minutes, Goal, Prerequisites).
   - Real, copy-pasteable Python code example subclassing or adding a tool to `WorkspaceSandbox`.
   - Tool definition with typed arguments and JSON schema.
   - AST validation and path confinement security checks.
   - Assigning the custom tool to an arm role in a guild spec.
   - Verifying the tool execution with simulated output block.
3. Link the new tutorial in [`docs/tutorials/README.md`](../tutorials/README.md).
4. Verify all links pass [`scripts/check_docs.py`](../../scripts/check_docs.py).

---

## Files to Touch
- `docs/tutorials/09-adding-a-custom-tool.md`: New tutorial document.
- [`docs/tutorials/README.md`](../tutorials/README.md): Add entry to tutorial directory index.
- [`docs/extending/tools.md`](../extending/): Link to the new tutorial if referenced.

---

## Acceptance Criteria
- [ ] Tutorial can be read and completed in under 10 minutes.
- [ ] Code examples use realistic tools (e.g. an SQLite query runner or format checker).
- [ ] Emphasizes security sandbox rules (preventing path traversal).
- [ ] `python scripts/check_docs.py` passes with 0 errors.
- [ ] Zero emoji characters in the tutorial text.

