"""OctoFlow LLM Provider Contract Test Suite.

A reusable specification and contract test mixin that any BaseLLMProvider implementation
must pass. Verifies:
1. Returns text and usage (valid LLMResponse, tokens_prompt >= 0, tokens_completion >= 0, total_tokens == sum).
2. Asynchronous generation (agenerate) parity.
3. Usage ledger recording when attached.
4. Graceful handling of empty model responses without crashing.
5. Error taxonomy mapping:
   - 401/403 -> ProviderAuthError (and provider is disabled)
   - 429 -> ProviderRateLimitError (with Retry-After parsing)
   - 5xx -> ProviderTransientError (with retries)
   - Timeouts -> ProviderTransientError (status 408)
6. Secret scrubbing: API keys and bearer tokens never leak in exception messages.
7. Timeout honoring: custom timeout configurations are preserved.
8. Capability reflection: supports_tools is declared and boolean.
9. Cancellation and budget interplay: handles async cancellation cleanly.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

from octoflow.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTransientError,
)
from octoflow.provider import (
    BaseLLMProvider,
    LLMResponse,
    reset_sleep_functions,
)
from octoflow.usage import UsageLedger


class ProviderContractSuite:
    """Base test mixin defining the universal OctoFlow provider contract.

    Concrete test classes must subclass this and implement:
      - `create_provider(transport, timeout, **kwargs)`
      - `fixture_path(name)` or provide response dicts:
          - `get_success_payload()`
          - `get_empty_payload()`
          - `get_auth_error_payload()`
          - `get_rate_limit_payload()`
          - `get_server_error_payload()`
    """

    secret_key: str = "sk-test-secret-contract-key-998877"

    def create_provider(
        self,
        transport: httpx.BaseTransport,
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        **kwargs: Any,
    ) -> BaseLLMProvider:
        """Instantiate the concrete provider with injected mock transport and sleep."""
        raise NotImplementedError("Subclasses must implement create_provider")

    def get_success_payload(self) -> dict[str, Any]:
        """Return a valid successful 200 response payload."""
        raise NotImplementedError("Subclasses must implement get_success_payload")

    def get_empty_payload(self) -> dict[str, Any]:
        """Return a 200 response with empty choices/content."""
        raise NotImplementedError("Subclasses must implement get_empty_payload")

    def get_auth_error_payload(self) -> tuple[int, dict[str, Any]]:
        """Return (status_code, error_payload) for 401/403 authentication error."""
        return 401, {"error": {"message": f"Invalid API key: {self.secret_key}"}}

    def get_rate_limit_payload(self) -> tuple[int, dict[str, Any], dict[str, str]]:
        """Return (status_code, error_payload, headers) for 429 rate limit."""
        return (
            429,
            {"error": {"message": "Rate limit exceeded"}},
            {"Retry-After": "2"},
        )

    def get_server_error_payload(self) -> tuple[int, dict[str, Any]]:
        """Return (status_code, error_payload) for 500/503 transient error."""
        return 500, {"error": {"message": "Internal server error"}}

    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest.fixture(autouse=True)
    def clean_env(self):
        reset_sleep_functions()
        yield
        reset_sleep_functions()

    # =========================================================================
    # Contract 1: Success Returns Text and Usage
    # =========================================================================
    def test_contract_generate_success(self):
        """Contract: generate() must return LLMResponse with content and token counts."""
        payload = self.get_success_payload()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport)

        resp = provider.generate("Contract verification prompt", system_prompt="Test system")
        assert isinstance(resp, LLMResponse)
        assert isinstance(resp.content, str)
        assert len(resp.content) > 0
        assert resp.tokens_prompt >= 0
        assert resp.tokens_completion >= 0
        assert resp.total_tokens == (resp.tokens_prompt + resp.tokens_completion)
        assert isinstance(resp.estimated, bool)

    # =========================================================================
    # Contract 2: Async agenerate Parity
    # =========================================================================
    @pytest.mark.anyio
    async def test_contract_agenerate_success(self):
        """Contract: agenerate() must asynchronously return LLMResponse with content and tokens."""
        payload = self.get_success_payload()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport)

        resp = await provider.agenerate("Async contract prompt")
        assert isinstance(resp, LLMResponse)
        assert isinstance(resp.content, str)
        assert len(resp.content) > 0
        assert resp.tokens_prompt >= 0
        assert resp.tokens_completion >= 0
        assert resp.total_tokens == (resp.tokens_prompt + resp.tokens_completion)

    # =========================================================================
    # Contract 3: Usage Recording via UsageLedger
    # =========================================================================
    def test_contract_usage_recording_with_ledger(self):
        """Contract: Attached UsageLedger accumulates prompt and completion tokens."""
        payload = self.get_success_payload()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport)
        ledger = UsageLedger()
        provider.set_ledger(ledger)

        resp = provider.generate("Test prompt")
        assert resp.total_tokens > 0

        assert ledger.total_tokens == resp.total_tokens
        assert ledger.total_calls == 1
        assert ledger.prompt_tokens == resp.tokens_prompt
        assert ledger.completion_tokens == resp.tokens_completion

    # =========================================================================
    # Contract 4: Graceful Handling of Empty Responses
    # =========================================================================
    def test_contract_handles_empty_response(self):
        """Contract: Empty content from the API must not crash; returns empty string."""
        empty_payload = self.get_empty_payload()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=empty_payload, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport)

        resp = provider.generate("Test prompt")
        assert isinstance(resp, LLMResponse)
        assert resp.content == ""
        assert resp.tokens_completion == 0
        assert resp.tokens_prompt >= 0

    # =========================================================================
    # Contract 5: Error Taxonomy Mapping - 401/403 Authentication Error
    # =========================================================================
    def test_contract_maps_auth_error_and_disables_session(self):
        """Contract: 401/403 must raise ProviderAuthError and set is_disabled = True."""
        code, err_payload = self.get_auth_error_payload()
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(code, json=err_payload, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport)

        with pytest.raises(ProviderAuthError) as exc_info:
            provider.generate("Test prompt")

        assert exc_info.value.status == code
        assert provider.is_disabled is True
        assert call_count == 1  # Exactly 1 attempt; zero retries on auth failure

        # Subsequent call immediately blocked without HTTP request
        with pytest.raises(ProviderAuthError) as exc_info_2:
            provider.generate("Second prompt")
        assert call_count == 1
        assert "disabled for the session" in str(exc_info_2.value)

    # =========================================================================
    # Contract 6: Error Taxonomy Mapping - 429 Rate Limit with Retries
    # =========================================================================
    def test_contract_maps_rate_limit_and_retries(self):
        """Contract: 429 must retry at most twice with sleep backoff and raise ProviderRateLimitError."""
        code, err_payload, headers = self.get_rate_limit_payload()
        call_count = 0
        sleep_records: list[float] = []

        def mock_sleep(sec: float):
            sleep_records.append(sec)

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(code, json=err_payload, headers=headers, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport, sleep_fn=mock_sleep)

        with pytest.raises(ProviderRateLimitError) as exc_info:
            provider.generate("Test prompt")

        assert exc_info.value.status == 429
        # Initial attempt + 2 retries = 3 calls
        assert call_count == 3
        # Slept twice
        assert len(sleep_records) == 2
        if "Retry-After" in headers:
            assert exc_info.value.retry_after == float(headers["Retry-After"])

    # =========================================================================
    # Contract 7: Error Taxonomy Mapping - 5xx Transient Error with Retries
    # =========================================================================
    def test_contract_maps_transient_server_error(self):
        """Contract: 5xx must retry at most twice and raise ProviderTransientError."""
        code, err_payload = self.get_server_error_payload()
        call_count = 0
        sleep_records: list[float] = []

        def mock_sleep(sec: float):
            sleep_records.append(sec)

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(code, json=err_payload, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport, sleep_fn=mock_sleep)

        with pytest.raises(ProviderTransientError) as exc_info:
            provider.generate("Test prompt")

        assert exc_info.value.status == code
        assert call_count == 3
        assert len(sleep_records) == 2

    # =========================================================================
    # Contract 8: Error Taxonomy Mapping - Timeouts Map to ProviderTransientError
    # =========================================================================
    def test_contract_maps_timeout_to_transient_error(self):
        """Contract: httpx.TimeoutException must map to ProviderTransientError with status 408."""
        call_count = 0
        sleep_records: list[float] = []

        def mock_sleep(sec: float):
            sleep_records.append(sec)

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            raise httpx.ReadTimeout("Connection read timed out during inference")

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport, sleep_fn=mock_sleep)

        with pytest.raises(ProviderTransientError) as exc_info:
            provider.generate("Test prompt")

        assert exc_info.value.status == 408
        assert "timed out" in str(exc_info.value).lower()
        assert call_count == 3  # retried twice as transient

    # =========================================================================
    # Contract 9: Secret Scrubbing - Keys Must Never Leak
    # =========================================================================
    def test_contract_never_leaks_keys_in_errors(self):
        """Contract: Secret API keys in payloads or headers must be redacted from error messages."""
        code, err_payload = self.get_auth_error_payload()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(code, json=err_payload, request=request)

        transport = httpx.MockTransport(handler)
        provider = self.create_provider(transport=transport)

        with pytest.raises(ProviderAuthError) as exc_info:
            provider.generate("Test prompt")

        err_str = str(exc_info.value)
        assert self.secret_key not in err_str, f"Secret key leaked in exception message: {err_str}"
        assert "[REDACTED" in err_str or "REDACTED" in err_str or "invalid" in err_str.lower()

    # =========================================================================
    # Contract 10: Respects Timeout Configuration
    # =========================================================================
    def test_contract_respects_custom_timeout(self):
        """Contract: Provider preserves custom httpx.Timeout setting."""
        custom_timeout = httpx.Timeout(12.5, connect=3.2)
        provider = self.create_provider(
            transport=httpx.MockTransport(lambda req: httpx.Response(200)),
            timeout=custom_timeout,
        )
        assert provider.timeout == custom_timeout

    # =========================================================================
    # Contract 11: Tool Capability Flag
    # =========================================================================
    def test_contract_declares_supports_tools(self):
        """Contract: Provider must declare supports_tools boolean attribute."""
        provider = self.create_provider(
            transport=httpx.MockTransport(lambda req: httpx.Response(200))
        )
        assert hasattr(provider, "supports_tools")
        assert isinstance(provider.supports_tools, bool)

    # =========================================================================
    # Contract 12: Cancellation & Interplay with Budgets
    # =========================================================================
    @pytest.mark.anyio
    async def test_contract_async_cancellation(self):
        """Contract: agenerate() responds cleanly to async task cancellation."""
        payload = self.get_success_payload()

        class CancellableSlowTransport(httpx.BaseTransport, httpx.AsyncBaseTransport):
            def handle_request(self, request: httpx.Request) -> httpx.Response:
                import time
                time.sleep(0.3)
                return httpx.Response(200, json=payload, request=request)

            async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
                await asyncio.sleep(0.3)
                return httpx.Response(200, json=payload, request=request)

        transport = CancellableSlowTransport()
        provider = self.create_provider(transport=transport)

        task = asyncio.create_task(provider.agenerate("Prompt"))
        await asyncio.sleep(0.02)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
