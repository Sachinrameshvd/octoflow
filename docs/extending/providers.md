# Extending OctoFlow: Custom LLM Providers

This guide walks through creating, registering, configuring, and contract-testing a custom LLM provider in OctoFlow (e.g., for **vLLM**, **LM Studio**, **LocalAI**, **Ollama custom models**, or proprietary private cloud gateways).

---

## 1. The Provider Extension Architecture

In OctoFlow, all LLM communication routes through subclasses of `BaseLLMProvider` (`octoflow.provider.BaseLLMProvider`). The architecture enforces:
- **Normalized Response Interface**: All calls return an `LLMResponse` with `content: str`, measured or estimated token counts, and tool calls.
- **Typed Error Taxonomy**: Status codes and exceptions automatically map into `ProviderError` subclasses (`ProviderAuthError`, `ProviderRateLimitError`, `ProviderTransientError`, `ProviderUnavailableError`).
- **Secret Redaction**: API keys and tokens are automatically scrubbed from outbound prompts, logs, and exception strings.
- **Sensory Gate & Token Ledger Accounting**: Providers automatically report token consumption to attached `UsageLedger` instances.
- **Hot-Swap Failover**: Providers plug directly into `CascadePoolLLMProvider` and `FailoverLLMProvider`.

---

## 2. The Provider Contract

Every provider must satisfy the universal contract verified by `tests/contract/provider_contract.py`:

| Requirement | Contract Specification | Expected Behavior |
|:---|:---|:---|
| **Return Schema** | `generate(...) -> LLMResponse` | `content` is a non-null string; `tokens_prompt >= 0`, `tokens_completion >= 0`, `total_tokens == sum`. |
| **Empty Content** | Handles `choices: []` or empty text | Returns `LLMResponse(content="", tokens_completion=0)` without raising `IndexError` or crashing. |
| **Authentication** | HTTP 401 / 403 or invalid key 400 | Raises `ProviderAuthError`, disables provider for session (`is_disabled = True`), 0 retries. |
| **Rate Limits** | HTTP 429 | Raises `ProviderRateLimitError`, honors `Retry-After` header if present, retries at most twice. |
| **Transient Errors** | HTTP 5xx / 529 | Raises `ProviderTransientError`, retries at most twice with exponential backoff and jitter. |
| **Timeouts** | `httpx.TimeoutException` | Raises `ProviderTransientError(status=408)` with network retry policy. |
| **Key Scrubbing** | API Keys & Bearer tokens | Credentials must NEVER appear in exception strings or logs. |
| **Tool Support** | `supports_tools: bool` | Declares whether the backend supports structured function/tool calling. |
| **Mock Transport** | Accepts `transport: httpx.BaseTransport` | Enables 100% offline unit and contract testing without live servers or real credentials. |

---

## 3. Step-by-Step Implementation

### Step 1: Create the Provider Class

Create a new module, for example `my_provider.py`:

```python
"""Custom LLM provider for an OpenAI-compatible local server (e.g. vLLM or LM Studio)."""

from __future__ import annotations

from typing import Any, Callable
import httpx

from octoflow.provider import (
    BaseLLMProvider,
    LLMResponse,
    DEFAULT_CLOUD_TIMEOUT,
    execute_with_retry,
    estimate_tokens_from_chars,
)


class MyCustomProvider(BaseLLMProvider):
    """Custom provider for internal OpenAI-compatible endpoint."""

    provider_name: str = "myprovider"
    supports_tools: bool = True

    def __init__(
        self,
        base_url: str | None = None,
        model: str = "default-model",
        api_key: str | None = None,
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        transport: httpx.BaseTransport | None = None,
        **kwargs: Any,
    ):
        raw_url = base_url or "http://localhost:8000/v1"
        self.base_url = (
            raw_url.rstrip("/")
            if raw_url.endswith("/chat/completions")
            else f"{raw_url.rstrip('/')}/chat/completions"
        )
        self.model = model
        self.api_key = api_key or "not-required"
        self.timeout = timeout or DEFAULT_CLOUD_TIMEOUT
        self.sleep_fn = sleep_fn
        self.asleep_fn = asleep_fn
        self.transport = transport

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        # 1. Scrub outbound prompts if outbound privacy redaction is enabled
        prompt, system_prompt = self.sanitize_outbound_prompt(prompt, system_prompt)

        # 2. Build OpenAI-compatible request payload
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 3. Execute HTTP request with OctoFlow retry and error mapping policy
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            http_resp = execute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                sleep_fn=self.sleep_fn,
            )
            data = http_resp.json()

        # 4. Extract content and token counts safely
        choices = data.get("choices", [])
        content = (choices[0].get("message", {}).get("content") or "") if choices else ""
        usage = data.get("usage")
        if (
            usage
            and usage.get("prompt_tokens") is not None
            and usage.get("completion_tokens") is not None
        ):
            in_toks = int(usage["prompt_tokens"])
            out_toks = int(usage["completion_tokens"])
            estimated = False
        else:
            in_toks = estimate_tokens_from_chars(prompt)
            out_toks = estimate_tokens_from_chars(content)
            estimated = True

        resp = LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=0.0,
            estimated=estimated,
        )

        # 5. Record usage into active ledger
        self.record_usage(resp)
        return resp
```

---

### Step 2: Register the Provider

Register your provider before initializing OctoFlow:

```python
import octoflow
from my_provider import MyCustomProvider

# Register provider name (case-insensitive)
octoflow.register_provider("myprovider", MyCustomProvider)
```

Verify that it is recognized:

```python
assert "myprovider" in octoflow.list_registered_providers()
```

---

### Step 3: Run the Contract Test Suite

OctoFlow provides `ProviderContractSuite` in `tests/contract/provider_contract.py`. To ensure your provider meets all production guarantees, inherit from `ProviderContractSuite`:

```python
# test_my_provider_contract.py
import httpx
from my_provider import MyCustomProvider
from tests.contract.provider_contract import ProviderContractSuite

class TestMyProviderContract(ProviderContractSuite):
    secret_key = "sk-custom-test-secret-key-123"

    def create_provider(self, transport: httpx.BaseTransport, **kwargs):
        return MyCustomProvider(
            base_url="http://localhost:8000/v1",
            api_key=self.secret_key,
            transport=transport,
            **kwargs,
        )

    def get_success_payload(self):
        return {
            "choices": [{"message": {"content": "Hello from custom provider!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    def get_empty_payload(self):
        return {
            "choices": [{"message": {"content": ""}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 0, "total_tokens": 8},
        }

    def get_auth_error_payload(self):
        return 401, {"error": {"message": f"Unauthorized key {self.secret_key}"}}

    def get_rate_limit_payload(self):
        return 429, {"error": {"message": "Rate limited"}}, {"Retry-After": "2"}

    def get_server_error_payload(self):
        return 500, {"error": {"message": "Server error"}}
```

Run pytest on your contract test:

```bash
pytest test_my_provider_contract.py -v
```

All 12 contract assertions (success, async, usage recording, empty response, error mappings, timeouts, key redaction, and cancellation) will execute automatically via mock transport without making any live network calls.

---

### Step 4: Use Your Provider in OctoFlow CLI

Once registered or configured, use your provider directly with the `octoflow` CLI:

```bash
octoflow run "Implement binary search tree in Python" \
  --provider myprovider \
  --model "meta-llama/Llama-3-8B-Instruct" \
  --base-url "http://localhost:8000/v1"
```

Or configure it in your `octoflow.yaml`:

```yaml
providers:
  pool:
    - name: primary-vllm
      provider: myprovider
      model: Llama-3-8B-Instruct
      base_url: http://localhost:8000/v1
      priority: 1
    - name: fallback-ollama
      provider: ollama
      model: qwen2.5-coder:7b
      priority: 2
```

---

## 4. Built-in Provider Results

All built-in OctoFlow providers have been verified against the contract test suite:

| Provider | Backend / Endpoint | `supports_tools` | Contract Tests | Status |
|:---|:---|:---:|:---:|:---:|
| **Anthropic** | `https://api.anthropic.com/v1/messages` | `True` | 12 / 12 | **PASS** |
| **OpenAI** | `https://api.openai.com/v1/chat/completions` | `True` | 12 / 12 | **PASS** |
| **Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai` | `True` | 12 / 12 | **PASS** |
| **Ollama** | `http://localhost:11434/api/generate` | `True` | 14 / 14 | **PASS** |
| **LMStudio (Example)** | `http://localhost:1234/v1/chat/completions` | `True` | 14 / 14 | **PASS** |

See [`examples/custom_provider/`](../../examples/custom_provider/) for the complete runnable example.

