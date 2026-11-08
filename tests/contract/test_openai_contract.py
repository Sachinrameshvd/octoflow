"""Contract test verification for OpenAI provider."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

from octoflow.provider import BaseLLMProvider, OpenAIProvider
from tests.contract.provider_contract import ProviderContractSuite

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "openai"


class TestOpenAIContract(ProviderContractSuite):
    """Verify OpenAIProvider adheres to the OctoFlow LLM provider contract."""

    secret_key = "sk-proj-testsecretkey"

    def create_provider(
        self,
        transport: httpx.BaseTransport,
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        **kwargs: Any,
    ) -> BaseLLMProvider:
        return OpenAIProvider(
            api_key=self.secret_key,
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
        return 401, json.loads((FIXTURE_DIR / "401_auth.json").read_text(encoding="utf-8"))

    def get_rate_limit_payload(self) -> tuple[int, dict[str, Any], dict[str, str]]:
        return (
            429,
            json.loads((FIXTURE_DIR / "429_rate_limit.json").read_text(encoding="utf-8")),
            {"Retry-After": "2"},
        )

    def get_server_error_payload(self) -> tuple[int, dict[str, Any]]:
        return 500, json.loads((FIXTURE_DIR / "500_server_error.json").read_text(encoding="utf-8"))

