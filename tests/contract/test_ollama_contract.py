"""Contract test verification for local Ollama provider."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

from octoflow.errors import ProviderUnavailableError
from octoflow.provider import BaseLLMProvider, OllamaProvider
from tests.contract.provider_contract import ProviderContractSuite

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "ollama"


class TestOllamaContract(ProviderContractSuite):
    """Verify OllamaProvider adheres to the OctoFlow LLM provider contract."""

    secret_key = "sk-ollama-local-test-not-used"

    def create_provider(
        self,
        transport: httpx.BaseTransport,
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        **kwargs: Any,
    ) -> BaseLLMProvider:
        return OllamaProvider(
            base_url="http://localhost:11434",
            model="qwen2.5-coder:7b",
            transport=transport,
            timeout=timeout,
            sleep_fn=sleep_fn,
            asleep_fn=asleep_fn,
            **kwargs,
        )

    def get_success_payload(self) -> dict[str, Any]:
        return json.loads((FIXTURE_DIR / "200_ok.json").read_text(encoding="utf-8"))

    def get_empty_payload(self) -> dict[str, Any]:
        return json.loads((FIXTURE_DIR / "200_empty.json").read_text(encoding="utf-8"))

    def get_auth_error_payload(self) -> tuple[int, dict[str, Any]]:
        # Reverse proxy / gateway auth failure
        return 401, {"error": f"Unauthorized proxy access with token {self.secret_key}"}

    def get_rate_limit_payload(self) -> tuple[int, dict[str, Any], dict[str, str]]:
        return 429, {"error": "Too many requests to local Ollama queue"}, {"Retry-After": "2"}

    def get_server_error_payload(self) -> tuple[int, dict[str, Any]]:
        return 500, json.loads((FIXTURE_DIR / "500_server_error.json").read_text(encoding="utf-8"))

    # Ollama-specific contract extensions
    def test_contract_ollama_404_model_missing_maps_to_unavailable(self):
        """Ollama specific: 404 model missing maps to ProviderUnavailableError with pull hint."""
        err_payload = json.loads((FIXTURE_DIR / "404_model_not_found.json").read_text(encoding="utf-8"))

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json=err_payload, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport)

        with pytest.raises(ProviderUnavailableError) as exc_info:
            provider.generate("Test prompt")

        assert exc_info.value.status == 404
        assert "ollama pull" in exc_info.value.hint.lower()

    def test_contract_ollama_connection_refused_maps_to_unavailable(self):
        """Ollama specific: connect failure maps to ProviderUnavailableError with serve hint."""
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused by localhost:11434")

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport)

        with pytest.raises(ProviderUnavailableError) as exc_info:
            provider.generate("Test prompt")

        assert "ollama serve" in exc_info.value.hint.lower()

