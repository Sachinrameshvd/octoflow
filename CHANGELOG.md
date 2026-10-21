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
- **Cockpit Shell-Router Safety & Non-Blocking Confirmation (P1.3)**:
  - Extracted pure input router into `octoflow/router.py` with `classify_input(line: str) -> Route` and deterministic `RouteKind` evaluation (`SWARM_GOAL`, `SHELL_SIMPLE`, `SHELL_EXPLICIT`, `SLASH_COMMAND`, `EMPTY`).
  - Implemented safe pass-through execution for `SHELL_SIMPLE` using `subprocess.run(argv, shell=False, cwd=workspace, timeout=60)` with 64 KB captured output truncation.
  - Added prose-versus-argument heuristic disambiguating natural language goals (e.g. `make a resume analyzer`, `list the requirements.txt issues`, `touch the code up`) to `SWARM_GOAL`.
  - Added non-blocking 20 FPS confirmation loop (`confirm_live_cockpit`) in the terminal cockpit preserving runner and banner animations during `y/N` prompts (defaulting to No).
  - Enforced destructive command safety gates for `rm`, `rmdir`, `mv`, `cp -r`, `chmod -R`, `chown`, `dd`, `mkfs`, `sudo`, destructive git operations (`reset --hard`, `clean`, `push --force`, `checkout .`, `branch -D`), directory traversal (`..`), and out-of-workspace absolute paths.
  - Enforced explicit command confirmation for lines prefixed with `!` or `$` before running with `shell=True`.
  - Hardened bracketed paste handling: pasted text is placed into the input buffer for review without auto-submitting; multi-line paste displays line count badges and routes to `SWARM_GOAL` unless prefixed with `!`.
  - Handled directory navigation (`cd`) in-process by updating the active workspace variable after verifying target directory exists, without calling global `os.chdir()`.
  - Implemented session command history logging in memory and persisted to `~/.octoflow/history` with restricted permissions `0600`.
  - Added deprecated escape hatch `OCTOFLOW_LEGACY_ROUTER=1`.
  - Added 95+ table-driven, characterization, and PTY simulation tests in `tests/test_router.py`.
- **Tool Sandbox Audit and Enforcement (P1.4)**:
  - Hardened `WorkspaceSandbox` in `octoflow/tools.py` with strict path confinement for `read_file`, `write_file`, and `list_dir`.
  - Enforced canonical path resolution, blocking `..` traversal, out-of-workspace absolute paths, and null-byte injection (`\x00`).
  - Added multi-level symlink escape defenses checking direct symlinks and recursively validating parent directory hierarchy for nonexistent target files.
  - Hardened `run_command` with argument array execution (`argv`) and `shell=False` by default, parsing commands via `shlex.split`.
  - Added `DEFAULT_ALLOWED_COMMANDS` allowlist restricting subprocess execution to approved compilers, interpreters, test runners, package managers, and safe utilities.
  - Added compound shell operator detection (`has_compound_operators`) blocking unquoted shell metacharacters and chaining (`|`, `;`, `&&`, `||`, `>`, `<`, backticks, `$(...)`).
  - Added explicit, documented opt-in `allow_unrestricted=True` for commands outside the allowlist.
  - Enforced configurable timeouts with default 60.0s and maximum 300.0s, returning exit code 124 on `TimeoutExpired` and terminating processes cleanly.
  - Bounded stdout/stderr capture to 64 KB (`MAX_CAPTURE_BYTES = 65,536`), truncating excessive output with clear diagnostic markers.
  - Controlled subprocess environment inheritance (`SAFE_ENV_PASSTHROUGH`), automatically scrubbing keys matching `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL`, `AUTH`, `APIKEY`.
  - Integrated `redact_secrets` across all tool outputs, exception strings, directory listings, and error diagnostics.
  - Standardized tool exit code reporting: 0 for success, 1 for general error, 124 for timeout, 126 for disallowed command or traversal attempt, 127 for missing executable.
  - Created `docs/SECURITY.md` and added comprehensive security test suite in `tests/test_tools_security.py` (18 tests).
- **Telemetry Server and Secrets Hardening (P1.5)**:
  - Default bind host hardened to loopback `127.0.0.1` (never `0.0.0.0` by default); binding to non-localhost via `--host` displays prominent network exposure warning.
  - Added strict WebSocket Origin validation on `/ws/telemetry`: accepts missing Origin (non-browser tests/CLI) and exact localhost/127.0.0.1 matches on served port; accepts Vite dev origin `http://localhost:5173` only in `dev_mode`; rejects untrusted origins with RFC 6455 close code `1008`.
  - Added HTTP Host header validation middleware protecting against DNS-rebinding attacks, rejecting unauthorized Host headers with status `400`.
  - Hardened telemetry payload sanitization: recursively strips prompts (`prompt`, `system_prompt`, `user_prompt`, `messages`), file contents (`file_content`, `diff`, `patch`), subprocess outputs (`stdout`, `stderr`, `command_output`), and credentials (`api_key`, `token`, `secret`); processes all free-text fields through `redact_secrets()`.
  - Enforced POSIX filesystem permission hardening: creates `~/.octoflow` with mode `0700` and `config.json` with mode `0600`; automatically tightens looser permissions on load with a one-line notice.
  - Hardened `octos setup` and cockpit credential inputs using non-echoing `getpass.getpass()`.
  - Masked all displayed API keys across CLI listings and REST endpoints to first 3 characters followed by `****` (e.g. `sk-****`).
  - Added `.gitignore` exclusions for `*.key`, `*.pem`, `*.checkpoint`, `checkpoints/`, `.octoflow_bench/`.
  - Created `docs/SECURITY_MODEL.md` ("Local telemetry server") and added comprehensive test suite in `tests/test_server_security.py` (16 tests).
