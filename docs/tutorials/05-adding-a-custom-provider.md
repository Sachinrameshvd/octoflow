# Tutorial 5: Adding a Custom LLM Provider

**Estimated Duration:** 9 minutes  
**Verification:** Verified on 2026-11-09, OctoFlow v0.2.0  

This tutorial walks through adding a custom inference backend (such as LM Studio, vLLM, or an internal enterprise inference gateway) using OctoFlow's `BaseLLMProvider` contract.

---

## The Provider Extension Contract

Every LLM backend in OctoFlow implements the `BaseLLMProvider` interface in `octoflow/provider.py`:
- `provider_name`: Lowercase string identifier.
- `generate(prompt, system_prompt=None, **kwargs)`: Returns a typed `LLMResponse(content, prompt_tokens, completion_tokens, latency_ms, is_estimated)`.
- `supports_tools`: Boolean property declaring function calling capabilities.

---

## Step 1: Write the Provider Class

Create a custom provider subclassing `BaseLLMProvider` (see `examples/custom_provider/lmstudio_provider.py` for a complete reference implementation):

```python
# my_provider.py
from octoflow.provider import BaseLLMProvider, LLMResponse, estimate_tokens_from_chars

class FastLocalProvider(BaseLLMProvider):
    provider_name = "fastlocal"
    model = "qwen2.5-coder:14b"
    supports_tools = True

    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> LLMResponse:
        import time
        t0 = time.time()

        # Call your custom inference endpoint (HTTP, IPC, or local library)
        # response = client.complete(prompt=prompt, system=system_prompt)
        text = "def solution():\n    return 42\n"

        latency = (time.time() - t0) * 1000.0
        p_tokens = estimate_tokens_from_chars(prompt)
        c_tokens = estimate_tokens_from_chars(text)

        return LLMResponse(
            content=text,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=p_tokens + c_tokens,
            latency_ms=latency,
            model=self.model,
            is_estimated=True,
        )
```

---

## Step 2: Register the Provider with OctoFlow

Register your provider at application startup or via your script:

```python
import octoflow

octoflow.register_provider("fastlocal", FastLocalProvider)
assert "fastlocal" in octoflow.list_registered_providers()
```

---

## Step 3: Verify Against the Provider Contract Suite

OctoFlow provides a reusable test harness in `tests/contract/provider_contract.py` to ensure your backend adheres to all error handling, secret redaction, and usage reporting rules:

```python
# test_my_provider.py
from tests.contract.provider_contract import ProviderContractSuite
from my_provider import FastLocalProvider

class TestMyProvider(ProviderContractSuite):
    def create_provider(self, **kwargs):
        return FastLocalProvider(**kwargs)
```

Run pytest against the contract:
```bash
pytest test_my_provider.py -v
```

*Expected output: All contract tests pass (basic generation, secret masking, usage accounting).*

---

## Step 4: Run Missions with Your Backend

Invoke the swarm passing your newly registered provider:

```bash
octoflow run "Build an LRU cache with tests" --provider fastlocal
```

---

## Next Steps

- Complete provider guide & contract checklists: [docs/extending/providers.md](../extending/providers.md)
- Learn how to integrate with Cursor & Claude Code: [Tutorial 6: Using OctoFlow from MCP](06-using-octoflow-from-mcp.md)
