# Error Code Reference

OctoFlow uses standardized error codes in the format `E-XXXX`. Every error specifies
the plain-language cause, the operational consequence, and a concrete next-step command.

## Error Catalog Summary

| Error Code | Class | Exit Code | Title | Docs Anchor |
| :--- | :--- | :---: | :--- | :--- |
| `E-BUDGET` | `BudgetExceeded` | `1` | Mission Execution Budget Exceeded | [docs/TROUBLESHOOTING.md#e-budget](docs/TROUBLESHOOTING.md#e-budget) |
| `E-CONFIG-INVALID` | `ConfigError` | `3` | Invalid or Corrupted Configuration | [docs/TROUBLESHOOTING.md#e-config-invalid](docs/TROUBLESHOOTING.md#e-config-invalid) |
| `E-GENERAL` | `OctoFlowError` | `1` | General OctoFlow Operational Error | [docs/TROUBLESHOOTING.md#e-general](docs/TROUBLESHOOTING.md#e-general) |
| `E-NOGIT` | `GitError` | `1` | Git Repository Missing or Operation Failed | [docs/TROUBLESHOOTING.md#e-nogit](docs/TROUBLESHOOTING.md#e-nogit) |
| `E-OLLAMA-DOWN` | `ProviderUnavailableError` | `2` | Local Inference Daemon Offline or Model Missing | [docs/TROUBLESHOOTING.md#e-ollama-down](docs/TROUBLESHOOTING.md#e-ollama-down) |
| `E-PROV-AUTH` | `ProviderAuthError` | `2` | Authentication or Authorization Failure | [docs/TROUBLESHOOTING.md#e-prov-auth](docs/TROUBLESHOOTING.md#e-prov-auth) |
| `E-PROV-EXHAUSTED` | `ProviderExhaustedError` | `2` | All Configured Inference Providers Failed | [docs/TROUBLESHOOTING.md#e-prov-exhausted](docs/TROUBLESHOOTING.md#e-prov-exhausted) |
| `E-PROV-FAILED` | `ProviderError` | `2` | Inference Provider Generic Failure | [docs/TROUBLESHOOTING.md#e-prov-failed](docs/TROUBLESHOOTING.md#e-prov-failed) |
| `E-PROV-RATE` | `ProviderRateLimitError` | `2` | Provider Rate Limit or Quota Exhaustion | [docs/TROUBLESHOOTING.md#e-prov-rate](docs/TROUBLESHOOTING.md#e-prov-rate) |
| `E-PROV-REQUEST` | `ProviderRequestError` | `2` | Invalid Provider Request Payload or Context Exceeded | [docs/TROUBLESHOOTING.md#e-prov-request](docs/TROUBLESHOOTING.md#e-prov-request) |
| `E-PROV-TRANSIENT` | `ProviderTransientError` | `2` | Transient Provider Network Failure | [docs/TROUBLESHOOTING.md#e-prov-transient](docs/TROUBLESHOOTING.md#e-prov-transient) |
| `E-TOOL-DENIED` | `ToolError` | `1` | Tool Execution Confinement or Timeout | [docs/TROUBLESHOOTING.md#e-tool-denied](docs/TROUBLESHOOTING.md#e-tool-denied) |
| `E-USAGE-INVALID` | `UsageError` | `3` | Invalid Command Line Syntax or Argument | [docs/TROUBLESHOOTING.md#e-usage-invalid](docs/TROUBLESHOOTING.md#e-usage-invalid) |
| `E-WORKSPACE-ESCAPE` | `WorkspaceError` | `1` | Workspace Boundary Confinement Violation | [docs/TROUBLESHOOTING.md#e-workspace-escape](docs/TROUBLESHOOTING.md#e-workspace-escape) |

---

## Detailed Error Catalog

### <a id="e-budget"></a>E-BUDGET — Mission Execution Budget Exceeded

- **Class**: `BudgetExceeded`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-budget](docs/TROUBLESHOOTING.md#e-budget)
- **Cause**: The mission exceeded its configured token count, LLM call count, cost ceiling, or wall-clock timeout.
- **Consequence**: Swarm execution was halted to prevent unintended resource consumption.
- **Next Step**: `Increase limits via '--budget <amount>', '--max-tokens <n>', '--timeout <sec>', or pass '--no-limits'.`

```text
E-BUDGET The mission exceeded its configured token count, LLM call count, cost ceiling, or wall-clock timeout.
Hint: Increase budget limits via CLI flags (--budget, --max-tokens, --timeout) or pass '--no-limits'.
```

### <a id="e-config-invalid"></a>E-CONFIG-INVALID — Invalid or Corrupted Configuration

- **Class**: `ConfigError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-config-invalid](docs/TROUBLESHOOTING.md#e-config-invalid)
- **Cause**: The settings file ~/.octoflow/config.json contains invalid keys, types, or syntax.
- **Consequence**: OctoFlow cannot load operational settings.
- **Next Step**: `Inspect settings with 'octoflow config show' or reset configuration with 'octoflow setup'.`

```text
E-CONFIG-INVALID The settings file ~/.octoflow/config.json contains invalid keys, types, or syntax.
Hint: Run 'octoflow config show' to view current keys or run 'octoflow setup' to regenerate configuration.
```

### <a id="e-general"></a>E-GENERAL — General OctoFlow Operational Error

- **Class**: `OctoFlowError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-general](docs/TROUBLESHOOTING.md#e-general)
- **Cause**: An unexpected operational error occurred during OctoFlow execution.
- **Consequence**: The requested operation failed.
- **Next Step**: `Inspect logs in ~/.octoflow/logs/octoflow.log or re-run with '--trace'.`

```text
E-GENERAL An unexpected operational error occurred during OctoFlow execution.
Hint: Run 'octoflow doctor' to diagnose system issues or re-run with '--trace'.
```

### <a id="e-nogit"></a>E-NOGIT — Git Repository Missing or Operation Failed

- **Class**: `GitError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-nogit](docs/TROUBLESHOOTING.md#e-nogit)
- **Cause**: The current workspace is not a Git repository or a Git checkpoint operation failed.
- **Consequence**: Automatic branch snapshotting and safe rollback cannot be performed.
- **Next Step**: `Initialize version control with 'git init' or run 'octoflow doctor --fix'.`

```text
E-NOGIT The current workspace is not a Git repository or a Git checkpoint operation failed.
Hint: Run 'git init' to initialize version control or run 'octoflow doctor --fix'.
```

### <a id="e-ollama-down"></a>E-OLLAMA-DOWN — Local Inference Daemon Offline or Model Missing

- **Class**: `ProviderUnavailableError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-ollama-down](docs/TROUBLESHOOTING.md#e-ollama-down)
- **Cause**: The local Ollama service is unreachable at http://127.0.0.1:11434 or requested model is missing.
- **Consequence**: Local model inference cannot proceed.
- **Next Step**: `Start the daemon with 'ollama serve' or pull the model with 'ollama pull qwen2.5-coder:7b'.`

```text
E-OLLAMA-DOWN The local Ollama service is unreachable at http://127.0.0.1:11434 or requested model is missing.
Hint: Run 'ollama serve' to start local inference or run 'ollama pull <model>' to download required weights.
```

### <a id="e-prov-auth"></a>E-PROV-AUTH — Authentication or Authorization Failure

- **Class**: `ProviderAuthError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-prov-auth](docs/TROUBLESHOOTING.md#e-prov-auth)
- **Cause**: The inference provider rejected your credentials (HTTP 401 or 403).
- **Consequence**: OctoFlow cannot authenticate requests with the selected AI model provider.
- **Next Step**: `Run 'octoflow setup' or export a valid API key (e.g. export ANTHROPIC_API_KEY='sk-...').`

```text
E-PROV-AUTH The inference provider rejected your credentials (HTTP 401 or 403).
Hint: Run 'octoflow setup' to configure valid credentials or export the required environment variable.
```

### <a id="e-prov-exhausted"></a>E-PROV-EXHAUSTED — All Configured Inference Providers Failed

- **Class**: `ProviderExhaustedError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-prov-exhausted](docs/TROUBLESHOOTING.md#e-prov-exhausted)
- **Cause**: All configured LLM providers in the fallback cascade failed or had exhausted credentials.
- **Consequence**: OctoFlow cannot complete autonomous code generation.
- **Next Step**: `Run 'octoflow setup' to configure working provider credentials or pass '--dry-run' for mock simulation.`

```text
E-PROV-EXHAUSTED All configured LLM providers in the fallback cascade failed or had exhausted credentials.
Hint: Configure healthy inference credentials with 'octoflow setup' or test with '--dry-run'.
```

### <a id="e-prov-failed"></a>E-PROV-FAILED — Inference Provider Generic Failure

- **Class**: `ProviderError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-prov-failed](docs/TROUBLESHOOTING.md#e-prov-failed)
- **Cause**: An unclassified operational error occurred while communicating with the AI model provider.
- **Consequence**: Model inference failed and swarm generation stopped.
- **Next Step**: `Inspect logs in ~/.octoflow/logs/octoflow.log or re-run with '--trace'.`

```text
E-PROV-FAILED An unclassified operational error occurred while communicating with the AI model provider.
Hint: Run 'octoflow doctor' to diagnose environment health or run with '--trace'.
```

### <a id="e-prov-rate"></a>E-PROV-RATE — Provider Rate Limit or Quota Exhaustion

- **Class**: `ProviderRateLimitError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-prov-rate](docs/TROUBLESHOOTING.md#e-prov-rate)
- **Cause**: The inference provider throttled requests due to rate limits or exhausted account credits (HTTP 429).
- **Consequence**: Current model requests are paused or rejected until the quota window resets.
- **Next Step**: `Wait for the provider quota reset or switch provider using 'octoflow config set llm_provider ollama'.`

```text
E-PROV-RATE The inference provider throttled requests due to rate limits or exhausted account credits (HTTP 429).
Hint: Wait for your quota window to reset or switch providers using 'octoflow config set llm_provider <name>'.
```

### <a id="e-prov-request"></a>E-PROV-REQUEST — Invalid Provider Request Payload or Context Exceeded

- **Class**: `ProviderRequestError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-prov-request](docs/TROUBLESHOOTING.md#e-prov-request)
- **Cause**: The request payload was rejected (HTTP 4xx) or prompt length exceeded the model's context window.
- **Consequence**: The model refused the payload and generation was halted.
- **Next Step**: `Reduce workspace context or configure a larger context model with 'octoflow config set model <name>'.`

```text
E-PROV-REQUEST The request payload was rejected (HTTP 4xx) or prompt length exceeded the model's context window.
Hint: Prune large context files or choose a model with a larger context window.
```

### <a id="e-prov-transient"></a>E-PROV-TRANSIENT — Transient Provider Network Failure

- **Class**: `ProviderTransientError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-prov-transient](docs/TROUBLESHOOTING.md#e-prov-transient)
- **Cause**: The remote provider experienced a temporary server error (HTTP 5xx), connection drop, or network timeout.
- **Consequence**: The current inference attempt failed after automatic retry attempts.
- **Next Step**: `Check internet connectivity and provider status page, then re-run with 'octoflow run'.`

```text
E-PROV-TRANSIENT The remote provider experienced a temporary server error (HTTP 5xx), connection drop, or network timeout.
Hint: Verify network connection and provider service status, then retry the mission.
```

### <a id="e-tool-denied"></a>E-TOOL-DENIED — Tool Execution Confinement or Timeout

- **Class**: `ToolError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-tool-denied](docs/TROUBLESHOOTING.md#e-tool-denied)
- **Cause**: A tool action violated security sandbox policies, exceeded execution timeout, or returned a failure code.
- **Consequence**: The tool execution was blocked to preserve workspace safety.
- **Next Step**: `Review tool parameters or increase timeout with 'octoflow config set tool_timeout 60'.`

```text
E-TOOL-DENIED A tool action violated security sandbox policies, exceeded execution timeout, or returned a failure code.
Hint: Review tool security constraints or increase timeout via CLI flags.
```

### <a id="e-usage-invalid"></a>E-USAGE-INVALID — Invalid Command Line Syntax or Argument

- **Class**: `UsageError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-usage-invalid](docs/TROUBLESHOOTING.md#e-usage-invalid)
- **Cause**: An unrecognized command, unknown flag, or invalid argument combination was provided.
- **Consequence**: The command could not be dispatched.
- **Next Step**: `Run 'octoflow --help' to see valid syntax and available options.`

```text
E-USAGE-INVALID An unrecognized command, unknown flag, or invalid argument combination was provided.
Hint: Run 'octoflow --help' to inspect valid CLI options and command syntax.
```

### <a id="e-workspace-escape"></a>E-WORKSPACE-ESCAPE — Workspace Boundary Confinement Violation

- **Class**: `WorkspaceError`
- **Troubleshooting Anchor**: [docs/TROUBLESHOOTING.md#e-workspace-escape](docs/TROUBLESHOOTING.md#e-workspace-escape)
- **Cause**: A file path operation attempted to access files outside the designated workspace directory.
- **Consequence**: The operation was blocked to prevent reading or modifying files outside the project root.
- **Next Step**: `Use relative paths within the workspace or specify a target directory with '--dir <path>'.`

```text
E-WORKSPACE-ESCAPE A file path operation attempted to access files outside the designated workspace directory.
Hint: Ensure all file paths stay within the workspace boundary or pass '--dir <path>'.
```
