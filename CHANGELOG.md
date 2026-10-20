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
