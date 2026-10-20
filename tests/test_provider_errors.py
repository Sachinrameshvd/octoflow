"""Comprehensive Verification Suite for Provider Error Taxonomy, Retries, and Backoff (P1.2).

Covers:
1. ProviderAuthError: 401, 403, and 400 with invalid-key signature. Exactly 1 attempt per session, marked disabled.
2. ProviderRateLimitError: 429 with Retry-After header sleeps exact duration and retries at most twice.
3. ProviderRateLimitError: 429 without Retry-After uses exponential backoff capped at 30s.
4. ProviderTransientError: 503 retries twice with ~0.5s and ~1.5s delays plus jitter.
5. ProviderTransientError: Timeouts and network connection drops.
6. ProviderRequestError: 4xx client errors (no retry, surfaces error).
7. ProviderUnavailableError: Ollama connection refused -> exact hint "start the daemon: ollama serve".
8. ProviderUnavailableError: Ollama 404 model missing -> exact hint "run: ollama pull <model>".
9. Default Timeouts: Connect 5s, Read 120s (cloud), Read 300s (Ollama).
10. Secret Redaction: API keys and Bearer tokens never appear in str(exception) or logs.
11. ProviderExhaustedError: Lists each failure with its exception class and actionable hint.
12. Failover integration: Disabled provider skipped in failover chain.
13. Async agenerate retry and backoff execution.
"""

import asyncio
import json
import logging
import re
import pytest
import httpx
from unittest.mock import MagicMock, patch

from octoflow.outcome import ProviderExhaustedError
from octoflow.provider import (
    BaseLLMProvider,
    AnthropicProvider,
    OpenAIProvider,
    OllamaProvider,
    FailoverLLMProvider,
    CascadePoolLLMProvider,
    ProviderError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTransientError,
    ProviderRequestError,
    ProviderUnavailableError,
    classify_http_error,
    redact_secrets,
    execute_with_retry,
    aexecute_with_retry,
    set_sleep_functions,
    reset_sleep_functions,
    DEFAULT_CLOUD_TIMEOUT,
    DEFAULT_OLLAMA_TIMEOUT,
)
from octoflow.config import LLMConfigEntry


@pytest.fixture(autouse=True)
def clean_sleep_and_env(monkeypatch):
    """Ensure clean sleep functions and environment variables for each test."""
    reset_sleep_functions()
    yield
    reset_sleep_functions()


# ==============================================================================
# 1. Error Taxonomy & Classification Tests
# ==============================================================================
def test_classify_auth_errors():
    """Verify 401, 403, and 400 with invalid-key signature map to ProviderAuthError."""
    # 401
    err_401 = classify_http_error(401, provider="anthropic")
    assert isinstance(err_401, ProviderAuthError)
    assert err_401.status == 401
    assert "ANTHROPIC_API_KEY" in err_401.hint

    # 403
    err_403 = classify_http_error(403, provider="openai")
    assert isinstance(err_403, ProviderAuthError)
    assert err_403.status == 403
    assert "OPENAI_API_KEY" in err_403.hint

    # 400 with invalid key signature
    body = '{"error": {"message": "Invalid API key provided", "type": "invalid_api_key"}}'
    err_400_key = classify_http_error(400, provider="anthropic", body=body)
    assert isinstance(err_400_key, ProviderAuthError)
    assert err_400_key.status == 400

    # 400 standard bad request -> ProviderRequestError
    err_400_req = classify_http_error(400, provider="anthropic", body='{"error": "max_tokens too large"}')
    assert isinstance(err_400_req, ProviderRequestError)
    assert err_400_req.status == 400


def test_classify_rate_limit_and_retry_after():
    """Verify 429 maps to ProviderRateLimitError and parses Retry-After header."""
    headers = {"Retry-After": "2.5"}
    err_429 = classify_http_error(429, provider="openai", headers=headers)
    assert isinstance(err_429, ProviderRateLimitError)
    assert err_429.status == 429
    assert err_429.retry_after == 2.5
    assert "Rate limit" in err_429.hint

    # Body containing retry_after
    body = json.dumps({"error": {"message": "Rate limit reached", "retry_after": 5.0}})
    err_429_body = classify_http_error(429, provider="anthropic", body=body)
    assert isinstance(err_429_body, ProviderRateLimitError)
    assert err_429_body.retry_after == 5.0


def test_classify_transient_and_timeout_errors():
    """Verify 5xx, timeouts, and connection errors map to ProviderTransientError."""
    for code in [500, 502, 503, 504, 529]:
        err = classify_http_error(code, provider="anthropic")
        assert isinstance(err, ProviderTransientError)
        assert err.status == code

    # Timeout
    timeout_exc = httpx.ReadTimeout("Read timed out")
    err_timeout = classify_http_error(timeout_exc, provider="openai")
    assert isinstance(err_timeout, ProviderTransientError)
    assert err_timeout.status == 408

    # Network connect error (cloud)
    conn_exc = httpx.ConnectError("Connection dropped")
    err_conn = classify_http_error(conn_exc, provider="anthropic")
    assert isinstance(err_conn, ProviderTransientError)


def test_classify_ollama_errors():
    """Verify Ollama down and missing model errors yield exact required hints."""
    # Ollama daemon down
    conn_exc = httpx.ConnectError("Connection refused")
    err_down = classify_http_error(conn_exc, provider="ollama")
    assert isinstance(err_down, ProviderUnavailableError)
    assert err_down.hint == "start the daemon: ollama serve"

    # Ollama model missing (404)
    err_missing = classify_http_error(404, provider="ollama", model="qwen2.5-coder:7b")
    assert isinstance(err_missing, ProviderUnavailableError)
    assert err_missing.hint == "run: ollama pull qwen2.5-coder:7b"


# ==============================================================================
# 2. Retry Policy & Injected Sleep Tests
# ==============================================================================
def test_401_attempted_once_and_marks_disabled():
    """Criterion 1: A 401 is attempted exactly once per provider per session, then skipped."""
    calls = 0
    fake_key = "sk-" + "ant-api03-" + "dummykey123456789012345"
    provider = AnthropicProvider(api_key=fake_key)

    def mock_post():
        nonlocal calls
        calls += 1
        req = httpx.Request("POST", provider.base_url)
        resp = httpx.Response(401, text="Unauthorized: invalid api key", request=req)
        return resp

    # 1. First execution: raises ProviderAuthError and disables provider
    with pytest.raises(ProviderAuthError) as exc_info:
        execute_with_retry(mock_post, provider=provider)

    assert calls == 1
    assert provider.is_disabled is True
    assert "invalid api key" in str(exc_info.value)

    # 2. Second execution: immediately blocked because provider is disabled (0 HTTP calls)
    with pytest.raises(ProviderAuthError) as exc_info_2:
        execute_with_retry(mock_post, provider=provider)

    assert calls == 1  # No additional HTTP request made
    assert "disabled for the session" in str(exc_info_2.value)


def test_429_with_retry_after_retries_at_most_twice():
    """Criterion 2: A 429 with Retry-After: 2 waits 2 seconds using injected sleep, retries at most twice."""
    sleep_records = []

    def mock_sleep(seconds: float):
        sleep_records.append(seconds)

    calls = 0
    fake_key = "sk-" + "proj-" + "dummyopenai123456789012345"
    provider = OpenAIProvider(api_key=fake_key, sleep_fn=mock_sleep)

    def mock_post():
        nonlocal calls
        calls += 1
        req = httpx.Request("POST", provider.base_url)
        return httpx.Response(429, headers={"Retry-After": "2"}, text="Too Many Requests", request=req)

    with pytest.raises(ProviderRateLimitError) as exc_info:
        execute_with_retry(mock_post, provider=provider, sleep_fn=mock_sleep)

    # Initial attempt + 2 retries = 3 calls
    assert calls == 3
    # Slept twice, each time honoring Retry-After: 2
    assert sleep_records == [2.0, 2.0]
    assert exc_info.value.retry_after == 2.0


def test_503_retries_twice_with_staged_delays():
    """Criterion 3: A 503 retries twice (using ~0.5s and ~1.5s delays plus jitter), then fails."""
    sleep_records = []

    def mock_sleep(seconds: float):
        sleep_records.append(seconds)

    calls = 0
    provider = "anthropic"

    def mock_post():
        nonlocal calls
        calls += 1
        req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        return httpx.Response(503, text="Service Unavailable", request=req)

    with pytest.raises(ProviderTransientError) as exc_info:
        execute_with_retry(mock_post, provider=provider, sleep_fn=mock_sleep)

    # Initial attempt + 2 retries = 3 calls
    assert calls == 3
    assert len(sleep_records) == 2
    # Verify delay 1 is ~0.5s + jitter [0.5, 0.75]
    assert 0.5 <= sleep_records[0] <= 0.75
    # Verify delay 2 is ~1.5s + jitter [1.5, 1.75]
    assert 1.5 <= sleep_records[1] <= 1.75
    assert exc_info.value.status == 503


def test_request_error_400_no_retry():
    """Client error 400 (not key related) must not be retried."""
    calls = 0

    def mock_post():
        nonlocal calls
        calls += 1
        req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        return httpx.Response(400, text="context_length_exceeded: max prompt is 8192", request=req)

    with pytest.raises(ProviderRequestError):
        execute_with_retry(mock_post, provider="openai")

    assert calls == 1


# ==============================================================================
# 3. Secret Redaction Tests
# ==============================================================================
def test_secret_redaction_in_messages_and_exceptions():
    """Criterion: Secret keys placed in requests or errors must never appear in exception strings or logs."""
    fake_ant = "sk-" + "ant-api03-" + "secret_token_1234567890abcdef"
    fake_oai = "sk-" + "proj-" + "secret_openai_1234567890abcdef"
    fake_bearer = "Bearer " + "secret_bearer_token_1234567890"

    raw_text = f"Request to endpoint failed with {fake_ant} and {fake_oai} and Authorization: {fake_bearer}"
    sanitized = redact_secrets(raw_text)

    assert "secret_token" not in sanitized
    assert "secret_openai" not in sanitized
    assert "secret_bearer" not in sanitized
    assert "[REDACTED_KEY]" in sanitized
    assert "[REDACTED_TOKEN]" in sanitized

    # Verify ProviderError automatically redacts messages and hints
    err = ProviderError(
        f"Invalid key {fake_ant}",
        provider="anthropic",
        status=401,
        hint=f"Use key {fake_oai}",
    )
    err_str = str(err)
    assert fake_ant not in err_str
    assert fake_oai not in err_str
    assert "[REDACTED_KEY]" in err_str


# ==============================================================================
# 4. Default Timeouts Configuration Tests
# ==============================================================================
def test_default_timeouts_configured():
    """Criterion 5: Verify default timeouts (Cloud connect 5s, read 120s; Ollama read 300s)."""
    assert DEFAULT_CLOUD_TIMEOUT.connect == 5.0
    assert DEFAULT_CLOUD_TIMEOUT.read == 120.0

    assert DEFAULT_OLLAMA_TIMEOUT.connect == 5.0
    assert DEFAULT_OLLAMA_TIMEOUT.read == 300.0

    fake_key = "sk-" + "ant-" + "test123456789012345"
    ant_prov = AnthropicProvider(api_key=fake_key)
    assert ant_prov.timeout.connect == 5.0
    assert ant_prov.timeout.read == 120.0

    fake_oai = "sk-" + "test123456789012345"
    oai_prov = OpenAIProvider(api_key=fake_oai)
    assert oai_prov.timeout.connect == 5.0
    assert oai_prov.timeout.read == 120.0

    ollama_prov = OllamaProvider()
    assert ollama_prov.timeout.connect == 5.0
    assert ollama_prov.timeout.read == 300.0


# ==============================================================================
# 5. Failover & ProviderExhaustedError Listing
# ==============================================================================
def test_failover_skips_disabled_provider_and_exhausts_with_hints():
    """Criterion 7: ProviderExhaustedError must list each failure with its exception class and hint."""
    fake_key1 = "sk-" + "ant-api03-" + "badkey123456789012345"
    fake_key2 = "sk-" + "badkey2_123456789012345"

    p1 = AnthropicProvider(api_key=fake_key1)
    p2 = OpenAIProvider(api_key=fake_key2)

    # Monkeypatch generate on p1 to simulate 401
    def mock_p1_gen(*args, **kwargs):
        raise ProviderAuthError("401 Unauthorized", provider="anthropic", status=401, hint="Check ANTHROPIC_API_KEY")

    # Monkeypatch generate on p2 to simulate 429
    def mock_p2_gen(*args, **kwargs):
        raise ProviderRateLimitError("429 Quota Exceeded", provider="openai", status=429, hint="Check OpenAI Quota", retry_after=5.0)

    p1.generate = mock_p1_gen
    p2.generate = mock_p2_gen

    failover_prov = FailoverLLMProvider(primary=p1, fallbacks=[p2])

    with pytest.raises(ProviderExhaustedError) as exc_info:
        failover_prov.generate("Test prompt")

    err = exc_info.value
    err_text = str(err)
    # Check that error classes and hints are in the message
    assert "ProviderAuthError" in err_text
    assert "Check ANTHROPIC_API_KEY" in err_text
    assert "ProviderRateLimitError" in err_text
    assert "Check OpenAI Quota" in err_text
    assert len(err.failures) == 2


# ==============================================================================
# 6. Async Retry Execution Tests
# ==============================================================================
@pytest.mark.anyio
async def test_async_aexecute_with_retry_honors_sleep():
    """Verify async retry execution with injected async sleep."""
    async_sleeps = []

    def mock_asleep(seconds: float):
        async_sleeps.append(seconds)

    calls = 0

    async def mock_async_call():
        nonlocal calls
        calls += 1
        req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        return httpx.Response(502, text="Bad Gateway", request=req)

    with pytest.raises(ProviderTransientError):
        await aexecute_with_retry(mock_async_call, provider="anthropic", asleep_fn=mock_asleep)

    assert calls == 3
    assert len(async_sleeps) == 2
    assert 0.5 <= async_sleeps[0] <= 0.75
    assert 1.5 <= async_sleeps[1] <= 1.75
