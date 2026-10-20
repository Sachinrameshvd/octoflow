# Troubleshooting Guide

This guide covers common errors encountered when running OctoFlow missions and working with LLM providers.

## Provider Error Taxonomy

OctoFlow classifies all LLM provider communication issues into structured error classes derived from `ProviderError`. When all providers in a cascade or failover pool fail, OctoFlow raises `ProviderExhaustedError`, listing each failure, its exception class, and an actionable hint.

| Error Class | HTTP Status / Trigger | Meaning | Automatic Swarm Action | Actionable Fix |
| :--- | :--- | :--- | :--- | :--- |
| **`ProviderAuthError`** | `401`, `403`, or `400` with invalid key signature | Authentication failed; API key is invalid, revoked, or forbidden. | **No retries**. The provider is marked disabled for the remainder of the session and execution immediately fails over to the next provider. | Verify your credentials in the environment or `.env` file (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.). Ensure the key has proper model permissions and credit balance. |
| **`ProviderRateLimitError`** | `429` (Too Many Requests) | Provider quota or rate limit exceeded. | Retries **up to 2 times**. Respects provider's `Retry-After` header if supplied, otherwise applies exponential backoff with jitter capped at 30 seconds. If still throttled, fails over. | Wait for the quota window to reset, increase your tier/rate limits with the provider, or configure multiple cascade providers in `OCTOFLOW_LLM_PROVIDER` to balance load. |
| **`ProviderTransientError`** | `5xx` (500, 502, 503, 504), Connect Timeout (5s), Read Timeout (120s / 300s), Connection Drops | Server-side downtime, transient network blip, or request timeout. | Retries **up to 2 times** with staged delays (~0.5s and ~1.5s plus random jitter), then fails over to the next provider. | Verify local internet connectivity and check provider status pages (e.g., status.anthropic.com, status.openai.com). If timeouts persist, consider using smaller context windows or local Ollama inference. |
| **`ProviderRequestError`** | `4xx` (e.g. 400, 422) not key-related, context length exceeded | Client payload error, invalid parameters, or prompt too long for the model's context window. | **No retries**. Immediately surfaces error or fails over to alternative configured providers. | Check prompt size and task specifications. For context length errors, prune codebase context or choose a model with a larger context window. |
| **`ProviderUnavailableError`** | Connection refused to `localhost:11434`, or `404` model not found on local Ollama | Local inference service is not running or the requested model has not been downloaded. | **No retries**. Immediately fails over to subsequent providers in the cascade. | • **Connection refused**: Start daemon: `ollama serve`<br>• **404 Model not found**: Run: `ollama pull <model>` *(OctoFlow never downloads models automatically)* |
| **`ProviderExhaustedError`** | All configured providers in the cascade failed or were disabled | Swarm has exhausted all failover options and cannot proceed with live generation. | Halts execution truthfully with exit code `2` (`[FAILED]`). Does not silently fall back to mock data. | Inspect the failure summary output for specific provider hints. Configure at least one healthy provider or run with `--dry-run` to test mission workflow without live API calls. |

---

## Secret Redaction

To prevent sensitive credentials from leaking into terminal output, error logs, or telemetry, all provider exceptions and logs pass through `redact_secrets`.
- `sk-ant-...` tokens are replaced with `[REDACTED_ANTHROPIC_KEY]`.
- `sk-...` tokens are replaced with `[REDACTED_OPENAI_KEY]`.
- `AIza...` tokens are replaced with `[REDACTED_GOOGLE_KEY]`.
- `Bearer ...` tokens are replaced with `Bearer [REDACTED_TOKEN]`.
- General query/header parameters (`api_key=...`, `password=...`) are replaced with `[REDACTED]`.

---

## Default Timeouts

OctoFlow enforces conservative default timeouts across all provider HTTP calls:

- **Connect Timeout**: `5.0` seconds (fail fast if endpoint is unreachable).
- **Read Timeout (Cloud)**: `120.0` seconds (Anthropic, OpenAI, Gemini, Grok, DeepSeek).
- **Read Timeout (Local Ollama)**: `300.0` seconds (allows local GPU/CPU generation for large prompts).
- **Write Timeout**: `30.0` seconds.
- **Pool Timeout**: `10.0` seconds.
