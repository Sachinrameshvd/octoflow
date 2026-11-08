# Custom Provider Template: LM Studio & vLLM

This example demonstrates how to implement, register, and contract-test a custom LLM provider in OctoFlow in under 100 lines of code.

---

## 1. Overview

OctoFlow's provider architecture is centered on `BaseLLMProvider`. Any backend that implements the provider contract can be registered dynamically and used seamlessly across OctoFlow swarms, fallback cascades, and benchmark harnesses.

This example implements `LMStudioProvider` for local inference engines (such as **LM Studio**, **vLLM**, **LocalAI**, or **text-generation-webui**) providing an OpenAI-compatible `/chat/completions` endpoint.

---

## 2. Implementation (`lmstudio_provider.py`)

A minimal provider requires:
1. Subclassing `BaseLLMProvider`.
2. Defining `provider_name` and `supports_tools`.
3. Accepting `base_url`, `model`, `api_key`, `timeout`, `sleep_fn`, `asleep_fn`, and optional `transport`.
4. Implementing `generate()` wrapped in `execute_with_retry` and returning `LLMResponse`.

```python
from octoflow.provider import BaseLLMProvider, LLMResponse, execute_with_retry
import httpx

class LMStudioProvider(BaseLLMProvider):
    provider_name = "lmstudio"
    supports_tools = True

    def __init__(self, base_url="http://localhost:1234/v1", model="local-model", **kwargs):
        self.base_url = f"{base_url.rstrip('/')}/chat/completions"
        self.model = model
        self.timeout = kwargs.get("timeout")
        self.transport = kwargs.get("transport")

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            resp = execute_with_retry(
                lambda: client.post(self.base_url, json=payload),
                provider=self,
            )
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {})
        return LLMResponse(
            content=content,
            tokens_prompt=tokens.get("prompt_tokens", 0),
            tokens_completion=tokens.get("completion_tokens", 0),
            total_tokens=tokens.get("total_tokens", 0),
        )
```

---

## 3. Registering Your Provider

Register your provider before initializing OctoFlow:

```python
import octoflow
from lmstudio_provider import LMStudioProvider

# Register custom provider backend
octoflow.register_provider("lmstudio", LMStudioProvider)
```

Once registered, you can invoke OctoFlow specifying `--provider lmstudio`:

```bash
octoflow run "Build a REST API" --provider lmstudio --model "mistral-7b-instruct" --base-url "http://localhost:1234/v1"
```

Or configure it in your `octoflow.yaml` / cascade pool:

```yaml
providers:
  pool:
    - name: local-lmstudio
      provider: lmstudio
      model: mistral-7b-instruct
      base_url: http://localhost:1234/v1
      priority: 1
```

---

## 4. Contract Testing

Every provider in OctoFlow is verified against `ProviderContractSuite` to ensure:
- Content and usage token metrics are correctly formatted.
- 401/403 maps to `ProviderAuthError` and disables the session.
- 429 maps to `ProviderRateLimitError` and honors `Retry-After`.
- 5xx and timeouts map to `ProviderTransientError` with retries.
- Sensitive API keys are never leaked in exception messages.
- Empty completions do not crash the provider.

Run the contract tests:

```bash
pytest examples/custom_provider/test_custom_provider.py -v
```

