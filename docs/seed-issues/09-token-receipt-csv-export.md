# Add CSV Export Option to octoflow receipt

**Difficulty:** Good First Issue  
**Labels:** `enhancement`, `good first issue`  
**Mentoring Pointer:** Check out [`octoflow/commands/receipt.py`](../../octoflow/commands/receipt.py) and [`octoflow/receipt.py`](../../octoflow/receipt.py) to see how receipt data and `--json` exports are serialized.

---

## Context
OctoFlow generates detailed token accounting receipts for every run. Users can inspect receipts in the terminal with `octoflow receipt [run_id]` or export them in JSON format with `octoflow receipt --json`.

Many data teams, engineering managers, and financial analysts prefer importing CSV tabular data directly into Google Sheets, Excel, or internal business intelligence pipelines for longitudinal token cost analysis. Adding a `--csv` flag provides this functionality cleanly using Python's standard library `csv` module.

---

## Objectives & Requirements
1. Add a `--csv` boolean option to `octoflow receipt` in [`octoflow/commands/receipt.py`](../../octoflow/commands/receipt.py).
2. Implement CSV serialization in [`octoflow/receipt.py`](../../octoflow/receipt.py) using Python standard library `csv.DictWriter`.
3. Standard CSV columns to export:
   - `run_id`: Mission identifier string
   - `timestamp`: ISO 8601 creation timestamp
   - `mode`: Run morphology (e.g. `SOFTWARE_DEV`, `AIML_RESEARCH`)
   - `model`: Configured LLM model name
   - `outcome`: Mission completion status (`complete` / `failed`)
   - `prompt_tokens`: Measured input tokens
   - `completion_tokens`: Measured output tokens
   - `avoided_tokens`: Estimated avoided tokens via sensory gating
   - `total_cost`: Estimated USD cost
   - `files_written`: Count of filesystem mutations
4. Output cleanly to stdout (allowing redirection: `octoflow receipt --csv > runs.csv`).

---

## Files to Touch
- [`octoflow/commands/receipt.py`](../../octoflow/commands/receipt.py): Add `--csv` option and CLI handling.
- [`octoflow/receipt.py`](../../octoflow/receipt.py): Implement `to_csv()` export function.
- [`tests/test_run_outcome.py`](../../tests/test_run_outcome.py): Add unit test asserting valid RFC 4180 CSV output format and headers.

---

## Acceptance Criteria
- [ ] Running `octoflow receipt --csv` produces RFC 4180 compliant CSV output.
- [ ] Headers match the specified column taxonomy.
- [ ] Passing both `--json` and `--csv` emits a clear validation error.
- [ ] All unit tests pass cleanly: `pytest tests/test_run_outcome.py`.

