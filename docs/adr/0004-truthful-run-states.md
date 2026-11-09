# ADR 0004: Truthful Run States and Elimination of Silent Mock Fallback (D1)

## Status
Accepted

## Context
Early iterations of OctoFlow featured a fallback mechanism that silently switched execution to `MockLLMProvider` whenever real API keys were unset or exhausted. While this prevented command crashes, it created dangerous ambiguity: missions reported `[COMPLETE]` with simulated mock code changes, misleading users into believing real foundation models had completed their tasks.

## Decision
Eliminate all silent mock fallback in live environments (Decision D1):
1. In `LIVE` mode (the default), missing API credentials, rate limits, or provider timeouts immediately raise `ProviderExhaustedError`, log configuration guidance, and terminate with exit code `2` (`FAILED`).
2. A run only reports `COMPLETE` (exit code `0`) if at least 6 arms reached quiescence AND real file modifications were committed to the active workspace. Runs that generate zero filesystem changes report `FAILED` with exit code `2`.
3. Simulated execution requires explicit user intent via `--dry-run` or `--model mock`. Dry-run simulations are visually badged in plain text and redirect all filesystem operations to `.octoflow/dry-run/`, leaving the workspace untouched.
4. Exit codes are strictly standardized across the CLI contract:
   - `0`: Complete success (or clean `--dry-run` simulation).
   - `1`: Incomplete or interrupted execution.
   - `2`: Exhausted provider, missing API key, or 0 files modified in live mode.
   - `3`: Usage or syntax error.

## Alternatives Considered
- **Interactive Key Prompting on Failure:** Prompt the user for an API token when a provider fails. Rejected because it breaks headless CI/CD automation and scriptable pipelines.
- **Degrade to Mock with a Warning Banner:** Display a warning while continuing simulation. Rejected because users routinely ignore non-fatal warnings and mistake mock files for production code.

## Consequences
- **Positive:** Unambiguous trust; impossible to mistake mock stubs for real model generation; predictable exit codes for CI/CD scripting.
- **Negative:** Commands fail quickly if environment variables or local daemons are misconfigured.

## Evidence & References
- Implementation: [`octoflow/provider.py`](../../octoflow/provider.py) (`CascadePoolLLMProvider`, `execute_with_retry`)
- Verification: [`tests/test_run_outcome.py`](../../tests/test_run_outcome.py)
- Commit: `881518b` (P1.1 Truthful run states and mock elimination)

## What Would Change This Decision
Nothing. Truthful state reporting and unambiguous failure reporting are foundational invariants of the project.
