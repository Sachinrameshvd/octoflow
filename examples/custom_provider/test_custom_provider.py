"""Contract and integration tests for custom LMStudioProvider.

Verifies:
1. LMStudioProvider passes the 100% provider contract suite.
2. Registration via `octoflow.register_provider("lmstudio", LMStudioProvider)`.
3. Resolution via `get_llm_provider(config)` with custom provider backend.
4. Compatibility with benchmark harness via MockTransport.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

# Ensure parent and examples are on path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
EXAMPLE_DIR = Path(__file__).resolve().parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

import octoflow
from octoflow.config import OctoFlowConfig
from octoflow.provider import (
    BaseLLMProvider,
    get_llm_provider,
    register_provider,
    unregister_provider,
)
from lmstudio_provider import LMStudioProvider
from tests.contract.provider_contract import ProviderContractSuite


class TestLMStudioContract(ProviderContractSuite):
    """Run custom LMStudioProvider against the OctoFlow LLM provider contract."""

    secret_key = "sk-lmstudio-local-token-xyz"

    def create_provider(
        self,
        transport: httpx.BaseTransport,
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        **kwargs: Any,
    ) -> BaseLLMProvider:
        return LMStudioProvider(
            base_url="http://localhost:1234/v1",
            model="mistral-7b-instruct",
            api_key=self.secret_key,
            transport=transport,
            timeout=timeout,
            sleep_fn=sleep_fn,
            asleep_fn=asleep_fn,
            **kwargs,
        )

    def get_success_payload(self) -> dict[str, Any]:
        return {
            "id": "chatcmpl-lmstudio-200",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "mistral-7b-instruct",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "LM Studio generated response for contract testing.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 14,
                "completion_tokens": 8,
                "total_tokens": 22,
            },
        }

    def get_empty_payload(self) -> dict[str, Any]:
        return {
            "id": "chatcmpl-lmstudio-empty",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "mistral-7b-instruct",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": ""},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 8, "completion_tokens": 0, "total_tokens": 8},
        }

    def get_auth_error_payload(self) -> tuple[int, dict[str, Any]]:
        return 401, {
            "error": {"message": f"Unauthorized LM Studio key: {self.secret_key}"}
        }

    def get_rate_limit_payload(self) -> tuple[int, dict[str, Any], dict[str, str]]:
        return 429, {"error": {"message": "Queue full in LM Studio"}}, {"Retry-After": "2"}

    def get_server_error_payload(self) -> tuple[int, dict[str, Any]]:
        return 500, {"error": {"message": "LM Studio worker crashed"}}


# =============================================================================
# Registration & Harness Integration Tests
# =============================================================================
def test_custom_provider_registration():
    """Verify dynamic provider registration and instantiation in get_llm_provider."""
    try:
        register_provider("lmstudio", LMStudioProvider)
        assert "lmstudio" in octoflow.list_registered_providers()

        config = OctoFlowConfig(
            model_provider="lmstudio",
            model_name="qwen2.5-coder:14b",
            base_url="http://localhost:1234/v1",
            force_live=True,
        )

        provider = get_llm_provider(config)
        assert isinstance(provider, LMStudioProvider)
        assert provider.provider_name == "lmstudio"
        assert provider.model == "qwen2.5-coder:14b"
        assert provider.base_url == "http://localhost:1234/v1/chat/completions"
        assert provider.supports_tools is True
    finally:
        unregister_provider("lmstudio")


def test_custom_provider_works_with_mock_transport_bench_harness():
    """Verify custom provider works in simulated / benchmark mode via MockTransport."""
    def mock_lmstudio_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "def add(a, b): return a + b"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
            },
            request=request,
        )

    transport = httpx.MockTransport(mock_lmstudio_handler)
    provider = LMStudioProvider(
        base_url="http://localhost:1234/v1",
        model="deepseek-coder",
        transport=transport,
    )

    resp = provider.generate("Write an add function")
    assert resp.content == "def add(a, b): return a + b"
    assert resp.tokens_prompt == 10
    assert resp.tokens_completion == 12
    assert resp.total_tokens == 22
    assert resp.estimated is False

