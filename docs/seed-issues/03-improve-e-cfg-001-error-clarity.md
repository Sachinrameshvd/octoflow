# Enhance Error Diagnostics and Remediation Hint for E-CFG-001

**Difficulty:** Good First Issue  
**Labels:** `enhancement`, `good first issue`, `docs`  
**Mentoring Pointer:** Inspect [`octoflow/errors.py`](../../octoflow/errors.py) and [`octoflow/messages.py`](../../octoflow/messages.py) to see how typed errors format CLI output with hints.

---

## Context
When an invalid or corrupt configuration file (`octoflow.json`) is loaded, OctoFlow raises `OctoFlowConfigError` with code `E-CFG-001`.

Currently, the error message indicates that the configuration is invalid, but it can be ambiguous about:
1. The exact filesystem path that failed parsing (workspace `.octoflow/config.json` vs global `~/.octoflow/config.json`).
2. The specific syntax or validation error (e.g. JSON decode error vs Pydantic schema validation error).
3. The next step to fix it (e.g. running `octoflow doctor --fix` or `octoflow config validate`).

---

## Objectives & Requirements
1. Update `OctoFlowConfigError` instantiation in [`octoflow/settings.py`](../../octoflow/settings.py) to capture the absolute path of the configuration file.
2. In [`octoflow/messages.py`](../../octoflow/messages.py) or [`octoflow/errors.py`](../../octoflow/errors.py), enhance the formatted error diagnostic for `E-CFG-001`:
   - Show the file path in a formatted box.
   - Display the specific line and column number if it was a JSON syntax error.
   - Suggest running `octoflow config validate` or `octoflow doctor --fix`.
3. Ensure no API keys or secrets in the file are leaked in the error output.

---

## Files to Touch
- [`octoflow/settings.py`](../../octoflow/settings.py): Pass path and parsing error context when raising `OctoFlowConfigError`.
- [`octoflow/errors.py`](../../octoflow/errors.py): Format detailed remediation hints for `E-CFG-001`.
- [`tests/test_errors_logging.py`](../../tests/test_errors_logging.py): Add test asserting that corrupt JSON prints the file path and remediation hint.

---

## Acceptance Criteria
- [ ] Feeding malformed JSON to `octoflow config validate` outputs `E-CFG-001` with the file path and line number.
- [ ] Error hint contains `octoflow doctor --fix` and `octoflow config validate`.
- [ ] All tests in `tests/test_errors_logging.py` pass.
- [ ] Zero emoji characters in error output (`wcwidth <= 1`).
