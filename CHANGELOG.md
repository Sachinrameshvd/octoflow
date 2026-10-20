# Changelog

All notable changes to OctoFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (breaking)
- **Mock Fallback Removed (Decision D1)**: Eliminated silent fallback to `MockLLMProvider` in live mode when real API providers fail or credentials are missing. Live runs with misconfigured or exhausted providers now raise `ProviderExhaustedError`, report `[FAILED]` with actionable configuration hints, sanitize all credentials, and exit with code 2.
- **Truthful Run Outcomes**: Live mode runs that produce 0 filesystem modifications now report outcome `FAILED` (`model produced no file changes`) with exit code 2. Only runs that successfully commit changes report `COMPLETE`.
- **Exit Code Contract**: Standardized exit codes across CLI:
  - `0`: Complete success (live run with files written, or dry-run simulation finished cleanly).
  - `1`: Partial completion (fewer than 6 arms quiescent or incomplete cycle).
  - `2`: Failure (provider exhaustion, missing credentials, zero files written in live mode).
  - `3`: Usage or argument syntax errors.
- **Zero-Emoji Terminal UI**: Cleaned CLI ribbons, visualizer badges, and MCP responses to strictly enforce semantic ASCII/Unicode glyphs (`•`, `·`, `○`, `◈`, `✔`, `✖`).

### Added
- **Explicit Dry-Run Mode (`--dry-run`)**: Added `--dry-run` flag to `octoflow run` and `octos run`. Runs against `MockLLMProvider`, displays prominent `DRY-RUN` status ribbon and visualizer badge, redirects all file operations to `.octoflow/dry-run/` without touching the target workspace, and exits with code 0.
- **Structured Outcome Models (`octoflow.outcome`)**: Added `RunMode`, `RunOutcome`, `OctoFlowError`, `ProviderExhaustedError`, and `RunResult` dataclass with backwards-compatible dictionary subscripting.
- **Outcome Metadata in Telemetry and MCP**: Added `mode` and `outcome` fields to `SwarmTelemetryEvent`, mission audit reports, and `octoflow_run_swarm` MCP tool results.
- **Provider Error Taxonomy and Backoff (P1.2)**:
  - Added structured exception taxonomy inheriting from `ProviderError(OctoFlowError)`: `ProviderAuthError`, `ProviderRateLimitError`, `ProviderTransientError`, `ProviderRequestError`, and `ProviderUnavailableError`.
  - Added centralized error classifier `classify_http_error` mapping status codes, network exceptions, and error payload signatures into concrete exception types with actionable user hints.
  - Implemented backoff retry loop:
    - Auth errors: 0 retries; provider marked disabled for session; immediate failover.
    - Rate limits (429): Respects `Retry-After` header or applies exponential backoff with jitter capped at 30s; max 2 retries then failover.
    - Transient errors (5xx, timeouts, connection drops): Retries up to 2 times with staged delays (~0.5s, ~1.5s plus jitter) then failover.
    - Request errors (4xx): 0 retries; surfaces error or fails over.
  - Added dependency injection for sleep functions (`set_sleep_functions`, `reset_sleep_functions`, `sleep_fn`, `asleep_fn`) ensuring all test suites execute without real-time delays.
  - Added precise actionable instructions for local Ollama failures: connection refused (`start the daemon: ollama serve`) and missing model (`run: ollama pull <model>`) with zero auto-downloads.
  - Standardized provider timeouts: connect 5s, read 120s (cloud), read 300s (Ollama).
  - Enforced zero secret leaks with `redact_secrets` redacting Anthropic keys, OpenAI keys, Google AI keys, and Bearer tokens in all exception strings and logs.
  - Added `docs/TROUBLESHOOTING.md` reference guide.
