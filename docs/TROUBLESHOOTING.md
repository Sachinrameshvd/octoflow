# OctoFlow Troubleshooting Guide

This guide covers error codes, diagnostic hints, and operational troubleshooting for OctoFlow missions.

---

## Error Catalog & Quick Reference

OctoFlow issues standardized error codes in the format `E-XXXX`. Every failure prints the cause in plain language, the consequence, and a concrete next-step command.

| Code | Exception Class | Meaning | Quick Action | Anchor |
| :--- | :--- | :--- | :--- | :--- |
| **`E-PROV-AUTH`** | `ProviderAuthError` | Provider authentication rejected (401/403) | `octoflow setup` | [#e-prov-auth](#e-prov-auth) |
| **`E-PROV-RATE`** | `ProviderRateLimitError` | Rate limit or quota exhausted (429) | Wait or switch provider | [#e-prov-rate](#e-prov-rate) |
| **`E-OLLAMA-DOWN`** | `ProviderUnavailableError` | Local Ollama offline or missing model | `ollama serve` / `ollama pull` | [#e-ollama-down](#e-ollama-down) |
| **`E-PROV-TRANSIENT`** | `ProviderTransientError` | 5xx server downtime or timeout | Retry or check status page | [#e-prov-transient](#e-prov-transient) |
| **`E-PROV-REQUEST`** | `ProviderRequestError` | 4xx payload error or context exceeded | Prune context files | [#e-prov-request](#e-prov-request) |
| **`E-PROV-EXHAUSTED`** | `ProviderExhaustedError` | All cascade providers failed | `octoflow setup` / `--dry-run` | [#e-prov-exhausted](#e-prov-exhausted) |
| **`E-PROV-FAILED`** | `ProviderError` | Unclassified provider failure | Re-run with `--trace` | [#e-prov-failed](#e-prov-failed) |
| **`E-CONFIG-INVALID`** | `ConfigError` | Invalid settings in config.json | `octoflow config show` | [#e-config-invalid](#e-config-invalid) |
| **`E-USAGE-INVALID`** | `UsageError` | Invalid CLI syntax or arguments | `octoflow --help` | [#e-usage-invalid](#e-usage-invalid) |
| **`E-TOOL-DENIED`** | `ToolError` | Tool sandbox confinement or timeout | Increase timeout | [#e-tool-denied](#e-tool-denied) |
| **`E-WORKSPACE-ESCAPE`**| `WorkspaceError` | File path escaped workspace root | Use relative paths | [#e-workspace-escape](#e-workspace-escape) |
| **`E-BUDGET`** | `BudgetExceeded` | Token, call, cost, or time limit hit | `--budget` / `--no-limits` | [#e-budget](#e-budget) |
| **`E-NOGIT`** | `GitError` | Workspace is not a Git repo | `git init` | [#e-nogit](#e-nogit) |
| **`E-GENERAL`** | `OctoFlowError` | General operational failure | Check logs with `--trace` | [#e-general](#e-general) |

---

## Detailed Error Codes & Remediation

### <a id="e-prov-auth"></a>E-PROV-AUTH — Authentication or Authorization Failure
- **Cause**: The inference provider rejected your credentials (HTTP 401 or 403). The API key is invalid, revoked, expired, or forbidden for the requested model.
- **Consequence**: OctoFlow cannot authenticate requests with the selected AI model provider and halts live generation.
- **Remediation**:
  1. Run `octoflow setup` to launch the interactive setup wizard and update keys.
  2. Alternatively, export the provider API key in your current shell:
     ```bash
     export ANTHROPIC_API_KEY="sk-ant-..."
     export OPENAI_API_KEY="sk-..."
     export GEMINI_API_KEY="AIza..."
     ```
  3. Verify that your provider account has an active balance and billing tier enabled.

### <a id="e-prov-rate"></a>E-PROV-RATE — Provider Rate Limit or Quota Exhaustion
- **Cause**: The inference provider throttled requests due to rate limits (RPM/TPM) or exhausted credit balance (HTTP 429).
- **Consequence**: Current model requests are paused. OctoFlow automatically retries up to 2 times honoring `Retry-After` headers, then halts or cascades.
- **Remediation**:
  1. Wait for the quota window to reset.
  2. Switch to local inference to continue without internet or quota limits:
     ```bash
     octoflow config set llm_provider ollama
     ```
  3. Configure multiple failover providers in `~/.octoflow/config.json`.

### <a id="e-ollama-down"></a>E-OLLAMA-DOWN — Local Daemon Offline or Model Missing
- **Cause**: The local Ollama service is unreachable at `http://127.0.0.1:11434` or the requested model has not been pulled to disk.
- **Consequence**: Local model inference cannot proceed.
- **Remediation**:
  1. If the daemon is not running, start it in a separate terminal:
     ```bash
     ollama serve
     ```
  2. If the model is not found (HTTP 404), download the recommended model:
     ```bash
     ollama pull qwen2.5-coder:7b
     ```
  3. Check Ollama connectivity using `octoflow doctor`.

### <a id="e-prov-transient"></a>E-PROV-TRANSIENT — Transient Provider Network Failure
- **Cause**: The remote provider experienced a temporary server outage (HTTP 500, 502, 503, 504), connection drop, or network read timeout.
- **Consequence**: The current inference attempt failed after automatic retry attempts with exponential backoff.
- **Remediation**:
  1. Check your internet connectivity.
  2. Check the provider's official status page (e.g. status.anthropic.com, status.openai.com).
  3. Re-run the mission:
     ```bash
     octoflow run
     ```

### <a id="e-prov-request"></a>E-PROV-REQUEST — Invalid Provider Request Payload or Context Exceeded
- **Cause**: The request payload was rejected (HTTP 4xx) or the prompt token count exceeded the model's context window.
- **Consequence**: Generation was halted because the provider cannot accept payloads exceeding its architecture limits.
- **Remediation**:
  1. Reduce context size by excluding large build folders or data artifacts in `.gitignore`.
  2. Switch to a model with a larger context window:
     ```bash
     octoflow config set model claude-3-7-sonnet-20250219
     ```

### <a id="e-prov-exhausted"></a>E-PROV-EXHAUSTED — All Configured Inference Providers Failed
- **Cause**: Every LLM provider in the fallback cascade failed or had exhausted credentials.
- **Consequence**: The swarm has exhausted all failover options and halts truthfully with exit code `2`.
- **Remediation**:
  1. Run `octoflow setup` to refresh API keys or configure a local model.
  2. Use dry-run simulation mode to verify mission workflows without live API calls:
     ```bash
     octoflow run "my objective" --dry-run
     ```

### <a id="e-prov-failed"></a>E-PROV-FAILED — Inference Provider Generic Failure
- **Cause**: An unclassified operational error occurred during API communication.
- **Consequence**: Model inference failed and swarm generation stopped.
- **Remediation**:
  1. Inspect rotating logs in `~/.octoflow/logs/octoflow.log`.
  2. Re-run with `--trace` to view full error traces:
     ```bash
     octoflow --trace run "my objective"
     ```

### <a id="e-config-invalid"></a>E-CONFIG-INVALID — Invalid or Corrupted Configuration
- **Cause**: The settings file `~/.octoflow/config.json` contains invalid JSON, unrecognized keys, or out-of-range values.
- **Consequence**: OctoFlow cannot load operational settings and exits with code `3`.
- **Remediation**:
  1. Inspect current settings:
     ```bash
     octoflow config show
     ```
  2. Reset configuration or run the setup wizard:
     ```bash
     octoflow setup
     ```

### <a id="e-usage-invalid"></a>E-USAGE-INVALID — Invalid Command Line Syntax or Argument
- **Cause**: An unrecognized CLI flag, missing mandatory argument, or invalid combination was supplied.
- **Consequence**: Command parsing failed and execution exited with code `3`.
- **Remediation**:
  1. Inspect valid syntax and flags:
     ```bash
     octoflow --help
     ```
  2. For specific subcommands, run `octoflow <command> --help`.

### <a id="e-tool-denied"></a>E-TOOL-DENIED — Tool Execution Confinement or Timeout
- **Cause**: A tool action violated sandbox confinement policy, exceeded execution timeout, or returned a nonzero failure code.
- **Consequence**: Tool execution was halted to protect workspace security.
- **Remediation**:
  1. Review tool parameters or increase timeout via configuration:
     ```bash
     octoflow config set tool_timeout 60
     ```
  2. Pass `--timeout <seconds>` on the CLI.

### <a id="e-workspace-escape"></a>E-WORKSPACE-ESCAPE — Workspace Boundary Confinement Violation
- **Cause**: A file path operation attempted to traverse outside the designated workspace root (e.g. `../` traversal or absolute path).
- **Consequence**: File operation was blocked to prevent reading or modifying unauthorized system files.
- **Remediation**:
  1. Ensure all file paths are relative to the project workspace root.
  2. If targeting an alternate folder, pass `--dir <path>`:
     ```bash
     octoflow run "objective" --dir /path/to/project
     ```

### <a id="e-budget"></a>E-BUDGET — Mission Execution Budget Exceeded
- **Cause**: The mission reached its configured ceiling for tokens, LLM API calls, dollar cost, or wall-clock timeout.
- **Consequence**: Swarm paused execution to prevent runaway costs or loops.
- **Remediation**:
  1. Increase the spending limit:
     ```bash
     octoflow run "objective" --budget 25.00
     ```
  2. Increase token limits or bypass limits with `--no-limits`:
     ```bash
     octoflow run "objective" --no-limits
     ```

### <a id="e-nogit"></a>E-NOGIT — Git Repository Missing or Operation Failed
- **Cause**: The current workspace is not a Git repository, or a Git rollback/checkpoint operation failed.
- **Consequence**: Automatic branch checkpointing and safe rollback protection cannot be guaranteed.
- **Remediation**:
  1. Initialize a Git repository in the current workspace:
     ```bash
     git init
     ```
  2. Or run the automatic repair command:
     ```bash
     octoflow doctor --fix
     ```

### <a id="e-general"></a>E-GENERAL — General OctoFlow Operational Error
- **Cause**: An unclassified operational error occurred during OctoFlow execution.
- **Consequence**: Command failed with exit code `1`.
- **Remediation**:
  1. Check system diagnostics with `octoflow doctor`.
  2. Inspect rotating logs in `~/.octoflow/logs/octoflow.log`.
  3. Re-run with `--trace` for full traceback.

---

## Secret Redaction

To prevent sensitive credentials from leaking into terminal output, error logs, or telemetry, all exceptions and logs pass through `redact_secrets`:
- Anthropic keys (`sk-ant-...`) -> `[REDACTED_KEY]`
- OpenAI keys (`sk-...`) -> `[REDACTED_KEY]`
- Google AI keys (`AIza...`) -> `[REDACTED_KEY]`
- Bearer tokens (`Authorization: Bearer ...`) -> `Authorization: Bearer [REDACTED_TOKEN]`
- Query/header secrets (`api_key=...`, `token=...`) -> `[REDACTED]`

---

## Default Timeouts

- **Connect Timeout**: `5.0` seconds
- **Read Timeout (Cloud)**: `120.0` seconds
- **Read Timeout (Local Ollama)**: `300.0` seconds
- **Write Timeout**: `30.0` seconds
- **Pool Timeout**: `10.0` seconds
