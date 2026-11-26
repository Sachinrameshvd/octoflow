"""Pluggable LLM Provider System.

Supports Anthropic Claude, OpenAI, local offline Ollama models, and a deterministic
MockLLMProvider for unit testing with zero API key dependencies and zero cost.
"""

import asyncio
import inspect
import json
import os
import random
import re
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, cast

import httpx
from pydantic import BaseModel

from octoflow.config import LLMConfigEntry, OctoFlowConfig
from octoflow.errors import (
    ProviderAuthError,
    ProviderError,
    ProviderExhaustedError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderTransientError,
    ProviderUnavailableError,
)
from octoflow.keyring_store import resolve_api_key
from octoflow.logging_config import get_logger
from octoflow.redactor import redact_outbound_text
from octoflow.usage import UsageLedger, estimate_tokens_from_chars

logger = get_logger("provider")


def redact_secrets(text: str) -> str:
    """Sanitize secrets, API keys, and Bearer tokens from text, exceptions, and logs."""
    if not text:
        return ""
    # Authorization header with Bearer token (e.g. Authorization: Bearer <token>)
    text = re.sub(
        r"Authorization:\s*Bearer\s+\S+",
        "Authorization: Bearer [REDACTED_TOKEN]",
        text,
        flags=re.IGNORECASE,
    )
    # Standalone Bearer tokens (e.g. Bearer <token>)
    text = re.sub(
        r"(?<!Authorization:\s)(?<!Authorization:)\bBearer\s+[a-zA-Z0-9_\-\.]{10,}",
        "Bearer [REDACTED_TOKEN]",
        text,
        flags=re.IGNORECASE,
    )
    # Non-bearer Authorization header values (e.g. Basic, Token, etc.)
    text = re.sub(
        r"Authorization:\s*(?!\s*Bearer\s+\[REDACTED_TOKEN\])[^\r\n]+",
        "Authorization: [REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    # API keys: Anthropic, OpenAI, Grok, etc. (sk-...)
    text = re.sub(r"sk-[a-zA-Z0-9_\-]{16,}", "[REDACTED_KEY]", text)
    # Google AI keys (AIza...)
    text = re.sub(r"AIza[0-9A-Za-z\-_]{16,}", "[REDACTED_KEY]", text)
    # GitHub personal access tokens
    text = re.sub(r"(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{20,}", "[REDACTED_GITHUB_TOKEN]", text)
    # Key-value query/header assignments
    text = re.sub(
        r'(api_key|apikey|key|token|secret|password)=([^\s&"\']+)',
        r"\1=[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    return text


_sanitize_secret_text = redact_secrets


# ==============================================================================
# Error Classifier (Task 2 & 4)
# ==============================================================================
def classify_http_error(
    error_or_status: Any,
    provider: str = "unknown",
    response: httpx.Response | None = None,
    body: str | None = None,
    headers: dict[str, str] | None = None,
    model: str | None = None,
) -> ProviderError:
    """Classifies an HTTP status code, response, or exception into the ProviderError taxonomy."""
    p_name = provider.lower().strip()
    status_code: int | None = None
    response_text: str = body or ""
    resp_headers: dict[str, str] = dict(headers or {})

    if isinstance(error_or_status, httpx.HTTPStatusError):
        response = error_or_status.response

    if response is not None:
        status_code = response.status_code
        if not response_text:
            try:
                response_text = response.text
            except Exception as e:
                logger.debug(
                    "Unable to read response.text: %s", e
                )  # best-effort: response payload may not be text or already closed
                response_text = ""
        if not resp_headers:
            resp_headers = {k.lower(): v for k, v in response.headers.items()}
    elif isinstance(error_or_status, int):
        status_code = error_or_status
    elif isinstance(error_or_status, ProviderError):
        return error_or_status
    elif isinstance(error_or_status, Exception):
        if hasattr(error_or_status, "status_code"):
            status_code = error_or_status.status_code
        elif hasattr(error_or_status, "status"):
            status_code = error_or_status.status
        if status_code is None:
            m = re.search(r"\b(4\d\d|5\d\d)\b", str(error_or_status))
            if m:
                status_code = int(m.group(1))
        if not response_text:
            response_text = str(error_or_status)

    norm_headers = {k.lower(): v for k, v in resp_headers.items()}

    # Check connection and timeout errors
    if isinstance(error_or_status, httpx.TimeoutException):
        return ProviderTransientError(
            "Request timed out",
            provider=provider,
            status=408,
            hint=f"Request to {provider} timed out. Consider checking network latency.",
        )

    if isinstance(error_or_status, (httpx.ConnectError, ConnectionError)):
        if p_name == "ollama":
            return ProviderUnavailableError(
                "Could not connect to Ollama daemon",
                provider=provider,
                status=None,
                hint="start the daemon: ollama serve",
            )
        return ProviderTransientError(
            f"Connection to {provider} failed",
            provider=provider,
            status=None,
            hint=f"Could not connect to {provider}. Check network connection or endpoint availability.",
        )

    clean_text = redact_secrets(response_text)
    msg = clean_text or (
        str(error_or_status) if not isinstance(error_or_status, int) else f"HTTP {status_code}"
    )
    clean_msg = redact_secrets(msg)

    # 1. Ollama specific handling
    if p_name == "ollama":
        if status_code == 404 or "not found" in clean_text.lower():
            mod_name = model or "model"
            return ProviderUnavailableError(
                f"Model '{mod_name}' not found in Ollama",
                provider=provider,
                status=404,
                hint=f"run: ollama pull {mod_name}",
            )

    # 2. Status 401 or 403 -> ProviderAuthError
    if status_code in (401, 403):
        return ProviderAuthError(
            clean_msg,
            provider=provider,
            status=status_code,
            hint=f"Check or update your {provider.upper()}_API_KEY credentials.",
        )

    # 3. Status 400 with invalid-key signature -> ProviderAuthError
    if status_code == 400:
        lower_body = clean_text.lower()
        is_key_error = any(
            phrase in lower_body
            for phrase in [
                "invalid_api_key",
                "invalid api key",
                "authentication_error",
                "invalid_x_api_key",
                "api_key_invalid",
                "unauthorized",
                "api key not valid",
                "incorrect api key",
                "key not found",
            ]
        )
        if is_key_error:
            return ProviderAuthError(
                clean_msg,
                provider=provider,
                status=400,
                hint=f"Invalid API key signature for {provider}. Verify your {provider.upper()}_API_KEY.",
            )
        return ProviderRequestError(
            clean_msg,
            provider=provider,
            status=400,
            hint=f"Bad request sent to {provider}. Check prompt format, parameters, or context length.",
        )

    # 4. Status 429 -> ProviderRateLimitError (with Retry-After extraction)
    is_rate_limit = status_code == 429 or any(
        k in clean_text.lower() or k in clean_msg.lower()
        for k in [
            "429",
            "rate limit",
            "rate_limit",
            "quota",
            "resource_exhausted",
            "insufficient_quota",
            "credit",
            "exceeded",
            "too many requests",
        ]
    )
    if is_rate_limit:
        retry_after: float | None = None
        if "retry-after" in norm_headers:
            try:
                retry_after = float(norm_headers["retry-after"])
            except (ValueError, TypeError) as e:
                logger.debug(
                    "Failed to parse numeric Retry-After header: %s", e
                )  # best-effort: non-numeric retry-after header
        if retry_after is None and clean_text:
            try:
                parsed = json.loads(clean_text)
                if isinstance(parsed, dict):
                    ra = parsed.get("retry_after") or parsed.get("error", {}).get("retry_after")
                    if ra:
                        retry_after = float(ra)
            except Exception as e:
                logger.debug(
                    "Response body not JSON or missing retry_after: %s", e
                )  # best-effort: response may be plain text or HTML

        return ProviderRateLimitError(
            clean_msg,
            provider=provider,
            status=429,
            hint=f"Rate limit reached for {provider}. Reduce concurrency or check account quotas.",
            retry_after=retry_after,
        )

    # 5. Status 5xx / 529 -> ProviderTransientError
    if status_code and (status_code >= 500 or status_code == 529):
        return ProviderTransientError(
            clean_msg,
            provider=provider,
            status=status_code,
            hint=f"Transient server error from {provider} (HTTP {status_code}). Service may be temporarily overloaded.",
        )

    # 6. Other 4xx -> ProviderRequestError
    if status_code and 400 <= status_code < 500:
        return ProviderRequestError(
            clean_msg,
            provider=provider,
            status=status_code,
            hint=f"Client request error from {provider} (HTTP {status_code}). Check request parameters.",
        )

    if isinstance(error_or_status, Exception):
        return ProviderTransientError(
            clean_msg,
            provider=provider,
            status=status_code,
            hint=f"Unexpected error communicating with {provider}.",
        )

    return ProviderError(clean_msg, provider=provider, status=status_code, hint="")


# ==============================================================================
# Injectable Sleep Functions & Timeouts (Task 3 & 5)
# ==============================================================================
_DEFAULT_SLEEP_FN: Callable[[float], None] = time.sleep
_DEFAULT_ASYNC_SLEEP_FN: Callable[[float], Any] = asyncio.sleep

DEFAULT_CLOUD_TIMEOUT = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=10.0)
DEFAULT_OLLAMA_TIMEOUT = httpx.Timeout(connect=5.0, read=300.0, write=30.0, pool=10.0)


def set_sleep_functions(
    sync_sleep: Callable[[float], None] | None = None,
    async_sleep: Callable[[float], Any] | None = None,
) -> None:
    """Inject global sleep functions for testing backoff and retries without real-time delays."""
    global _DEFAULT_SLEEP_FN, _DEFAULT_ASYNC_SLEEP_FN
    if sync_sleep is not None:
        _DEFAULT_SLEEP_FN = sync_sleep
    if async_sleep is not None:
        _DEFAULT_ASYNC_SLEEP_FN = async_sleep


def reset_sleep_functions() -> None:
    """Reset sleep functions to standard time.sleep and asyncio.sleep."""
    global _DEFAULT_SLEEP_FN, _DEFAULT_ASYNC_SLEEP_FN
    _DEFAULT_SLEEP_FN = time.sleep
    _DEFAULT_ASYNC_SLEEP_FN = asyncio.sleep


# ==============================================================================
# Retry Policy Engine (Task 3)
# ==============================================================================
def execute_with_retry(
    fn: Callable[[], httpx.Response],
    provider: Any = "unknown",
    model: str | None = None,
    sleep_fn: Callable[[float], None] | None = None,
) -> httpx.Response:
    """Executes an HTTP request honoring OctoFlow retry and backoff policy.

    - Auth errors: 0 retries; marks provider disabled for session, raises ProviderAuthError.
    - Rate limits: retries at most twice, honoring Retry-After or exponential backoff with jitter capped at 30s.
    - Transient errors: retries at most twice, using 0.5s and 1.5s delays plus jitter.
    - Request/Unavailable errors: 0 retries, raises immediately.
    """
    provider_name = (
        getattr(provider, "provider_name", str(provider))
        if not isinstance(provider, str)
        else provider
    )
    model_name = model or getattr(provider, "model", None)

    if isinstance(provider, BaseLLMProvider) and getattr(provider, "is_disabled", False):
        raise ProviderAuthError(
            f"Provider '{provider_name}' is disabled for the session due to authentication failure",
            provider=provider_name,
            status=401,
            hint=f"Provider disabled for session. Re-enable with valid {provider_name.upper()}_API_KEY.",
        )

    rate_limit_retries = 0
    transient_retries = 0
    actual_sleep = sleep_fn or getattr(provider, "sleep_fn", None) or _DEFAULT_SLEEP_FN

    while True:
        try:
            resp = fn()
            resp.raise_for_status()
            return resp
        except Exception as raw_e:
            err = classify_http_error(raw_e, provider=provider_name, model=model_name)

            if isinstance(err, ProviderAuthError):
                if isinstance(provider, BaseLLMProvider):
                    provider.is_disabled = True
                    provider.disabled_reason = str(err)
                raise err from raw_e

            elif isinstance(err, ProviderRateLimitError):
                if rate_limit_retries < 2:
                    rate_limit_retries += 1
                    if err.retry_after is not None and err.retry_after > 0:
                        delay = min(err.retry_after, 30.0)
                    else:
                        delay = min(
                            1.0 * (2 ** (rate_limit_retries - 1)) + random.uniform(0.1, 0.4), 30.0
                        )
                    actual_sleep(delay)
                    continue
                raise err from raw_e

            elif isinstance(err, ProviderTransientError):
                if transient_retries < 2:
                    transient_retries += 1
                    base_delay = 0.5 if transient_retries == 1 else 1.5
                    delay = base_delay + random.uniform(0.05, 0.2)
                    actual_sleep(delay)
                    continue
                raise err from raw_e

            else:
                raise err from raw_e


async def aexecute_with_retry(
    coro_fn: Callable[[], Any],
    provider: Any = "unknown",
    model: str | None = None,
    asleep_fn: Callable[[float], Any] | None = None,
) -> httpx.Response:
    """Asynchronously executes an HTTP request honoring OctoFlow retry and backoff policy."""
    provider_name = (
        getattr(provider, "provider_name", str(provider))
        if not isinstance(provider, str)
        else provider
    )
    model_name = model or getattr(provider, "model", None)

    if isinstance(provider, BaseLLMProvider) and getattr(provider, "is_disabled", False):
        raise ProviderAuthError(
            f"Provider '{provider_name}' is disabled for the session due to authentication failure",
            provider=provider_name,
            status=401,
            hint=f"Provider disabled for session. Re-enable with valid {provider_name.upper()}_API_KEY.",
        )

    rate_limit_retries = 0
    transient_retries = 0
    actual_asleep = asleep_fn or getattr(provider, "asleep_fn", None) or _DEFAULT_ASYNC_SLEEP_FN

    async def _do_sleep(d: float) -> None:
        if inspect.iscoroutinefunction(actual_asleep):
            await actual_asleep(d)
        else:
            res = actual_asleep(d)
            if asyncio.iscoroutine(res):
                await res

    while True:
        try:
            resp = await coro_fn()
            resp.raise_for_status()
            return cast(httpx.Response, resp)
        except Exception as raw_e:
            err = classify_http_error(raw_e, provider=provider_name, model=model_name)

            if isinstance(err, ProviderAuthError):
                if isinstance(provider, BaseLLMProvider):
                    provider.is_disabled = True
                    provider.disabled_reason = str(err)
                raise err from raw_e

            elif isinstance(err, ProviderRateLimitError):
                if rate_limit_retries < 2:
                    rate_limit_retries += 1
                    if err.retry_after is not None and err.retry_after > 0:
                        delay = min(err.retry_after, 30.0)
                    else:
                        delay = min(
                            1.0 * (2 ** (rate_limit_retries - 1)) + random.uniform(0.1, 0.4), 30.0
                        )
                    await _do_sleep(delay)
                    continue
                raise err from raw_e

            elif isinstance(err, ProviderTransientError):
                if transient_retries < 2:
                    transient_retries += 1
                    base_delay = 0.5 if transient_retries == 1 else 1.5
                    delay = base_delay + random.uniform(0.05, 0.2)
                    await _do_sleep(delay)
                    continue
                raise err from raw_e

            else:
                raise err from raw_e


def retry_http_request(
    fn: Callable[[], httpx.Response], max_retries: int = 3, base_delay: float = 1.0
) -> httpx.Response:
    """Legacy helper: delegates to execute_with_retry."""
    return execute_with_retry(fn, provider="unknown")


async def aretry_http_request(
    coro_fn: Callable[[], Any], max_retries: int = 3, base_delay: float = 1.0
) -> httpx.Response:
    """Legacy helper: delegates to aexecute_with_retry."""
    return await aexecute_with_retry(coro_fn, provider="unknown")


class LLMResponse(BaseModel):
    """Normalized response from an LLM call."""

    content: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    total_tokens: int = 0
    estimated_cost_dollars: float = 0.0
    tool_calls: list[dict[str, Any]] = []
    estimated: bool = False
    tokens_cached_read: int = 0
    tokens_cached_create: int = 0

    @property
    def prompt_tokens(self) -> int:
        return self.tokens_prompt

    @property
    def completion_tokens(self) -> int:
        return self.tokens_completion


class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends.

    Any provider implementation must satisfy the provider contract:
    1. Returns a valid `LLMResponse` containing `content: str` and token counts.
    2. Handles empty responses gracefully (returns empty content without crashing).
    3. Maps HTTP 401/403 to `ProviderAuthError` and disables the provider session.
    4. Maps HTTP 429 to `ProviderRateLimitError` (parsing Retry-After header or body).
    5. Maps HTTP 5xx and timeouts to `ProviderTransientError` with retry attempts.
    6. Scrubbing: Never leaks raw API keys or sensitive authorization tokens.
    7. Supports timeout and cancellation interplay for run budgets and failover.
    """

    provider_name: str = "base"
    model: str = "default"
    supports_tools: bool = False
    is_disabled: bool = False
    disabled_reason: str | None = None
    sleep_fn: Callable[[float], None] | None = None
    asleep_fn: Callable[[float], Any] | None = None
    timeout: httpx.Timeout | None = None
    transport: httpx.BaseTransport | None = None
    usage_ledger: UsageLedger | None = None
    redact_outbound: bool = True
    outbound_redactions_count: int = 0

    def is_local(self) -> bool:
        """Check if this provider executes locally on-device without outbound cloud network egress."""
        if self.provider_name in ("mock", "fake", "replay", "ollama"):
            return True
        base = getattr(self, "base_url", "") or ""
        if any(h in base for h in ("localhost", "127.0.0.1", "0.0.0.0", "::1")):
            return True
        return False

    def sanitize_outbound_prompt(self, prompt: str, system_prompt: str = "") -> tuple[str, str]:
        """Scrub sensitive credentials/tokens from outbound cloud prompts if redaction is enabled."""
        if not self.redact_outbound or self.is_local():
            return prompt, system_prompt
        clean_p, n_p = redact_outbound_text(prompt)
        clean_s, n_s = redact_outbound_text(system_prompt)
        self.outbound_redactions_count += (n_p + n_s)
        return clean_p, clean_s

    def get_redactions_count(self) -> int:
        """Return cumulative count of secrets scrubbed from outbound prompts."""
        return self.outbound_redactions_count

    def set_ledger(self, ledger: UsageLedger | None) -> None:
        """Attach a UsageLedger to accumulate token consumption."""
        self.usage_ledger = ledger

    def record_usage(self, response: LLMResponse) -> None:
        """Record usage into attached ledger if present."""
        if self.usage_ledger is not None:
            self.usage_ledger.record(
                prompt_tokens=response.tokens_prompt,
                completion_tokens=response.tokens_completion,
                estimated=response.estimated,
                provider=self.provider_name,
                model=self.model,
            )
        try:
            from octoflow.trace import get_active_tracer

            tracer = get_active_tracer()
            if tracer and tracer.enabled:
                tracer.log_provider_request(
                    provider=self.provider_name,
                    model=self.model,
                    prompt_tokens=response.tokens_prompt,
                    completion_tokens=response.tokens_completion,
                    total_tokens=response.total_tokens,
                    latency_ms=getattr(response, "latency_ms", 0.0),
                    status="success",
                )
        except Exception:
            pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        images: list[Any] | None = None,
    ) -> LLMResponse:
        """Synchronously generate an LLM completion."""
        pass

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Asynchronously generate an LLM completion."""
        import asyncio

        return await asyncio.to_thread(
            self.generate, prompt, system_prompt, temperature, max_tokens
        )


class MockLLMProvider(BaseLLMProvider):
    """Deterministic, zero-cost LLM provider for unit tests and local simulation."""

    provider_name = "mock"
    model = "mock"

    def __init__(self, script_responses: dict[str, str] | None = None):
        self.script_responses = script_responses or {}
        self.call_count = 0
        self.total_tokens_spent = 0

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        images: list[Any] | None = None,
    ) -> LLMResponse:
        self.call_count += 1
        prompt_lower = prompt.lower()
        if images:
            img_names = ", ".join(getattr(im, "filename", "image") for im in images)
            resp_text = (
                f"[Mock Vision] Received {len(images)} image attachment(s): {img_names}. "
                "Switch to Claude, OpenAI, Gemini, or a vision Ollama model (e.g. llava) for real image analysis."
            )
            tokens_in = estimate_tokens_from_chars(prompt)
            tokens_out = estimate_tokens_from_chars(resp_text)
            self.total_tokens_spent += tokens_in + tokens_out
            resp = LLMResponse(
                content=resp_text,
                tokens_prompt=tokens_in,
                tokens_completion=tokens_out,
                total_tokens=tokens_in + tokens_out,
                estimated_cost_dollars=0.0,
            )
            self.record_usage(resp)
            return resp

        # Check explicit custom scripts
        for pattern, response in self.script_responses.items():
            if pattern.lower() in prompt_lower:
                tokens_in = estimate_tokens_from_chars(prompt)
                tokens_out = estimate_tokens_from_chars(response)
                self.total_tokens_spent += tokens_in + tokens_out
                resp = LLMResponse(
                    content=response,
                    tokens_prompt=tokens_in,
                    tokens_completion=tokens_out,
                    total_tokens=tokens_in + tokens_out,
                    estimated_cost_dollars=0.0,
                    estimated=True,
                )
                self.record_usage(resp)
                return resp

        # Default intelligent mock responses for various agent roles
        if "developer question:" in prompt_lower or "inquiry:" in prompt_lower:
            role_hint = (
                system_prompt.split(" (Arm")[0].replace("You are ", "").strip()
                if "You are " in system_prompt
                else "Specialist"
            )
            content = (
                f"As the {role_hint}, I analyzed this domain carefully. "
                f"This decision enforces clean interface boundaries, high transaction concurrency, and robust data persistence. "
                f"All components adhere to the project specifications and pass AST pre-flight validation."
            )
        elif "reverse_words" in prompt_lower or "reverses words" in prompt_lower or "reverse words" in prompt_lower:
            is_qa = "you are qa" in system_prompt.lower() or "(arm 5)" in system_prompt.lower()
            if is_qa:
                content = json.dumps(
                    {
                        "action": "write_file",
                        "path": "test_reverse_words.py",
                        "content": (
                            "from reverse_words import reverse_words\n\n"
                            "def test_reverse_words_basic():\n"
                            "    assert reverse_words('hello world') == 'world hello'\n\n"
                            "def test_reverse_words_empty():\n"
                            "    assert reverse_words('') == ''\n\n"
                            "def test_reverse_words_multiple():\n"
                            "    assert reverse_words('the quick brown fox') == 'fox brown quick the'\n"
                        ),
                        "explanation": "Added unit test suite in test_reverse_words.py",
                    }
                )
            else:
                content = json.dumps(
                    {
                        "action": "write_file",
                        "path": "reverse_words.py",
                        "content": (
                            "def reverse_words(text: str) -> str:\n"
                            "    \"\"\"Reverse the order of words in a sentence.\"\"\"\n"
                            "    if not text.strip():\n"
                            "        return ''\n"
                            "    return ' '.join(reversed(text.split()))\n"
                        ),
                        "explanation": "Implemented reverse_words function in reverse_words.py",
                    }
                )
        elif "test" in prompt_lower or "pytest" in prompt_lower:
            content = json.dumps(
                {
                    "action": "run_command",
                    "command": "python -c 'print(\"1 passed in 0.01s\")'",
                    "explanation": "Running unit test suite to verify code contracts.",
                }
            )
        elif (
            "slidingwindowratelimiter" in prompt_lower
            or "limiter.py" in prompt_lower
            or "rate limiter" in prompt_lower
        ):
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "limiter.py",
                    "content": (
                        "import time\nimport threading\n\n"
                        "class SlidingWindowRateLimiter:\n"
                        "    def __init__(self):\n"
                        "        self._lock = threading.Lock()\n"
                        "        self._requests = {}\n\n"
                        "    def allow_request(self, client_id: str, limit: int, window_sec: float) -> bool:\n"
                        "        with self._lock:\n"
                        "            now = time.time()\n"
                        "            timestamps = self._requests.setdefault(client_id, [])\n"
                        "            self._requests[client_id] = [t for t in timestamps if now - t < window_sec]\n"
                        "            if len(self._requests[client_id]) < limit:\n"
                        "                self._requests[client_id].append(now)\n"
                        "                return True\n"
                        "            return False\n"
                    ),
                    "explanation": "Implemented thread-safe SlidingWindowRateLimiter in limiter.py",
                }
            )
        elif "lrucache" in prompt_lower or "lru.py" in prompt_lower or "lru cache" in prompt_lower:
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "lru.py",
                    "content": (
                        "from collections import OrderedDict\n\n"
                        "class LRUCache:\n"
                        "    def __init__(self, capacity: int):\n"
                        "        self.capacity = capacity\n"
                        "        self.cache = OrderedDict()\n\n"
                        "    def get(self, key: int) -> int:\n"
                        "        if key not in self.cache:\n"
                        "            return -1\n"
                        "        self.cache.move_to_end(key)\n"
                        "        return self.cache[key]\n\n"
                        "    def put(self, key: int, value: int) -> None:\n"
                        "        if key in self.cache:\n"
                        "            self.cache.move_to_end(key)\n"
                        "        self.cache[key] = value\n"
                        "        if len(self.cache) > self.capacity:\n"
                        "            self.cache.popitem(last=False)\n"
                    ),
                    "explanation": "Implemented O(1) LRUCache in lru.py",
                }
            )
        elif "generate_token" in prompt_lower or "auth.py" in prompt_lower or "jwt" in prompt_lower:
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "auth.py",
                    "content": (
                        "import hmac\nimport hashlib\nimport json\nimport base64\n\n"
                        "def generate_token(payload: dict, secret: str) -> str:\n"
                        "    payload_str = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()\n"
                        "    signature = hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()\n"
                        "    return f'{payload_str}.{signature}'\n\n"
                        "def verify_token(token: str, secret: str) -> dict:\n"
                        "    try:\n"
                        "        parts = token.split('.')\n"
                        "        if len(parts) != 2:\n"
                        "            return None\n"
                        "        payload_str, signature = parts\n"
                        "        expected_sig = hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()\n"
                        "        if not hmac.compare_digest(signature, expected_sig):\n"
                        "            return None\n"
                        "        return json.loads(base64.urlsafe_b64decode(payload_str.encode()).decode())\n"
                        "    except Exception:\n"
                        "        return None\n"
                    ),
                    "explanation": "Implemented HMAC-SHA256 JWT Tokenizer in auth.py",
                }
            )
        elif (
            "resolve_dependencies" in prompt_lower
            or "topo.py" in prompt_lower
            or "topological" in prompt_lower
            or "dag" in prompt_lower
        ):
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "topo.py",
                    "content": (
                        "def resolve_dependencies(nodes, edges):\n"
                        "    from collections import defaultdict, deque\n"
                        "    in_degree = {n: 0 for n in nodes}\n"
                        "    adj = defaultdict(list)\n"
                        "    for u, v in edges:\n"
                        "        adj[v].append(u)\n"
                        "        in_degree[u] += 1\n"
                        "    queue = deque([n for n in nodes if in_degree[n] == 0])\n"
                        "    order = []\n"
                        "    while queue:\n"
                        "        curr = queue.popleft()\n"
                        "        order.append(curr)\n"
                        "        for neighbor in adj[curr]:\n"
                        "            in_degree[neighbor] -= 1\n"
                        "            if in_degree[neighbor] == 0:\n"
                        "                queue.append(neighbor)\n"
                        "    if len(order) != len(nodes):\n"
                        "        raise ValueError('Cycle detected in graph')\n"
                        "    return order\n"
                    ),
                    "explanation": "Implemented Topological DAG Resolver in topo.py",
                }
            )
        elif "write" in prompt_lower or "create" in prompt_lower:
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "test_output.py",
                    "content": "# Generated by OctoFlow Arm\ndef solve():\n    return True\n",
                    "explanation": "Creating initial implementation file.",
                }
            )
        elif "error" in prompt_lower or "fix" in prompt_lower:
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "test_output.py",
                    "content": "# Patched by OctoFlow Arm\ndef solve():\n    return True\n",
                    "explanation": "Applying patch to resolve high sensory surprise error.",
                }
            )
        else:
            content = json.dumps(
                {
                    "action": "mark_quiescent",
                    "explanation": "Task objectives satisfied in full.",
                }
            )

        tokens_in = estimate_tokens_from_chars(prompt)
        tokens_out = estimate_tokens_from_chars(content)
        self.total_tokens_spent += tokens_in + tokens_out

        resp = LLMResponse(
            content=content,
            tokens_prompt=tokens_in,
            tokens_completion=tokens_out,
            total_tokens=tokens_in + tokens_out,
            estimated_cost_dollars=0.0,
            estimated=True,
        )
        self.record_usage(resp)
        return resp

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        import asyncio

        await asyncio.sleep(0.001)
        return self.generate(prompt, system_prompt, temperature, max_tokens)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API Provider (Claude 3.5 Sonnet / Opus / Haiku) with Prompt Caching."""

    provider_name = "anthropic"
    supports_tools = True

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        redact_outbound: bool = True,
        transport: httpx.BaseTransport | None = None,
        enable_prompt_caching: bool = True,
    ):
        self.api_key = api_key or resolve_api_key("anthropic")[0]
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or parameter required.")
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.timeout = timeout or DEFAULT_CLOUD_TIMEOUT
        self.sleep_fn = sleep_fn
        self.asleep_fn = asleep_fn
        self.redact_outbound = redact_outbound
        self.transport = transport
        self.enable_prompt_caching = enable_prompt_caching

    def _build_request_payload(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
        images: list[Any] | None = None,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        headers = {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        if self.enable_prompt_caching:
            headers["anthropic-beta"] = "prompt-caching-2024-07-31"

        if images:
            user_content: Any = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": getattr(img, "media_type", "image/png"),
                        "data": getattr(img, "base64_data", ""),
                    },
                }
                for img in images
            ] + [{"type": "text", "text": prompt}]
        else:
            user_content = prompt

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user_content}],
        }

        if system_prompt:
            if self.enable_prompt_caching:
                payload["system"] = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                payload["system"] = system_prompt

        if tools:
            anthropic_tools = []
            for t in tools:
                schema = (
                    t.get("input_schema")
                    or t.get("parameters")
                    or {"type": "object", "properties": {}}
                )
                anthropic_tools.append(
                    {
                        "name": t.get("name", ""),
                        "description": t.get("description", ""),
                        "input_schema": schema,
                    }
                )
            payload["tools"] = anthropic_tools

        return headers, payload

    def _parse_response_data(
        self,
        data: dict[str, Any],
        prompt: str,
    ) -> LLMResponse:
        items = data.get("content", [])
        text_pieces: list[str] = []
        tool_calls: list[dict[str, Any]] = []

        for item in items:
            item_type = item.get("type")
            if item_type == "text":
                text_pieces.append(item.get("text", ""))
            elif item_type == "tool_use":
                tool_calls.append(
                    {
                        "id": item.get("id", ""),
                        "name": item.get("name", ""),
                        "arguments": item.get("input", {}),
                    }
                )

        content = "".join(text_pieces)
        usage = data.get("usage")

        cache_read = 0
        cache_create = 0

        if (
            usage
            and usage.get("input_tokens") is not None
            and usage.get("output_tokens") is not None
        ):
            in_toks = int(usage["input_tokens"])
            out_toks = int(usage["output_tokens"])
            cache_read = int(usage.get("cache_read_input_tokens", 0))
            cache_create = int(usage.get("cache_creation_input_tokens", 0))
            estimated = False
        else:
            in_toks = estimate_tokens_from_chars(prompt)
            out_toks = estimate_tokens_from_chars(content)
            estimated = True

        # Model-aware Truthful Pricing Calculation
        model_lower = self.model.lower()
        if "haiku" in model_lower:
            cost = (
                (in_toks * 0.0000008)
                + (cache_read * 0.00000008)
                + (cache_create * 0.0000010)
                + (out_toks * 0.000004)
            )
        elif "opus" in model_lower:
            cost = (
                (in_toks * 0.000015)
                + (cache_read * 0.0000015)
                + (cache_create * 0.00001875)
                + (out_toks * 0.000075)
            )
        else:
            # Claude 3.5 Sonnet / Default:
            # $3/M base input, $0.30/M cache read (90% off!), $3.75/M cache creation, $15/M output
            cost = (
                (in_toks * 0.000003)
                + (cache_read * 0.0000003)
                + (cache_create * 0.00000375)
                + (out_toks * 0.000015)
            )

        total_prompt = in_toks + cache_read

        return LLMResponse(
            content=content,
            tokens_prompt=total_prompt,
            tokens_completion=out_toks,
            total_tokens=total_prompt + out_toks,
            estimated_cost_dollars=round(cost, 6),
            tool_calls=tool_calls,
            estimated=estimated,
            tokens_cached_read=cache_read,
            tokens_cached_create=cache_create,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
        images: list[Any] | None = None,
    ) -> LLMResponse:
        prompt, system_prompt = self.sanitize_outbound_prompt(prompt, system_prompt)
        headers, payload = self._build_request_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            images=images,
        )
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            http_resp = execute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                sleep_fn=self.sleep_fn,
            )
            data = http_resp.json()

        llm_resp = self._parse_response_data(data, prompt)
        self.record_usage(llm_resp)
        return llm_resp

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        prompt, system_prompt = self.sanitize_outbound_prompt(prompt, system_prompt)
        headers, payload = self._build_request_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            http_resp = await aexecute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                asleep_fn=self.asleep_fn,
            )
            data = http_resp.json()

        llm_resp = self._parse_response_data(data, prompt)
        self.record_usage(llm_resp)
        return llm_resp


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider (GPT-4o, GPT-4o-mini)."""

    provider_name = "openai"
    supports_tools = True

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        base_url: str | None = None,
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        redact_outbound: bool = True,
        transport: httpx.BaseTransport | None = None,
    ):
        self.api_key = api_key or resolve_api_key("openai")[0]
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable or parameter required.")
        self.model = model
        raw_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        if not raw_url.endswith("/chat/completions"):
            self.base_url = f"{raw_url.rstrip('/')}/chat/completions"
        else:
            self.base_url = raw_url
        self.timeout = timeout or DEFAULT_CLOUD_TIMEOUT
        self.sleep_fn = sleep_fn
        self.asleep_fn = asleep_fn
        self.redact_outbound = redact_outbound
        self.transport = transport

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        images: list[Any] | None = None,
    ) -> LLMResponse:
        prompt, system_prompt = self.sanitize_outbound_prompt(prompt, system_prompt)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if images:
            user_content: Any = [{"type": "text", "text": prompt}] + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{getattr(img, 'media_type', 'image/png')};base64,{getattr(img, 'base64_data', '')}"
                    },
                }
                for img in images
            ]
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            http_resp = execute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                sleep_fn=self.sleep_fn,
            )
            data = http_resp.json()

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

        # GPT-4o pricing: $2.50 / MTok in, $10 / MTok out
        cost = (in_toks * 0.0000025) + (out_toks * 0.000010)

        llm_resp = LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=cost,
            estimated=estimated,
        )
        self.record_usage(llm_resp)
        return llm_resp

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        prompt, system_prompt = self.sanitize_outbound_prompt(prompt, system_prompt)
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
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            http_resp = await aexecute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                asleep_fn=self.asleep_fn,
            )
            data = http_resp.json()

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
        cost = (in_toks * 0.0000025) + (out_toks * 0.000010)

        llm_resp = LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=cost,
            estimated=estimated,
        )
        self.record_usage(llm_resp)
        return llm_resp


class GeminiProvider(OpenAIProvider):
    """Google Gemini API Provider via OpenAI-compatible endpoint (Gemini 2.0 Flash / Pro)."""

    provider_name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        base_url: str | None = None,
        **kwargs: Any,
    ):
        key = api_key or resolve_api_key("gemini")[0]
        if not key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required.")
        url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai"
        super().__init__(api_key=key, model=model, base_url=url, **kwargs)


class GrokProvider(OpenAIProvider):
    """xAI Grok API Provider (Grok 2 / Grok beta)."""

    provider_name = "grok"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "grok-2-1212",
        base_url: str | None = None,
        **kwargs: Any,
    ):
        key = api_key or resolve_api_key("grok")[0]
        if not key:
            raise ValueError("XAI_API_KEY or GROK_API_KEY environment variable required.")
        url = base_url or "https://api.x.ai/v1"
        super().__init__(api_key=key, model=model, base_url=url, **kwargs)


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek API Provider (DeepSeek-V3 / DeepSeek-R1)."""

    provider_name = "deepseek"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-chat",
        base_url: str | None = None,
        **kwargs: Any,
    ):
        key = api_key or resolve_api_key("deepseek")[0]
        if not key:
            raise ValueError("DEEPSEEK_API_KEY environment variable required.")
        url = base_url or "https://api.deepseek.com/v1"
        super().__init__(api_key=key, model=model, base_url=url, **kwargs)


class OllamaProvider(BaseLLMProvider):
    """Local, offline, 100% free Ollama Provider (DeepSeek-Coder, Qwen2.5, Llama-3)."""

    provider_name = "ollama"
    supports_tools = True

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:7b",
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout or DEFAULT_OLLAMA_TIMEOUT
        self.sleep_fn = sleep_fn
        self.asleep_fn = asleep_fn
        self.transport = transport
        self._semaphore: asyncio.Semaphore | None = None

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 512,
        images: list[Any] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if images:
            payload["images"] = [getattr(img, "base64_data", "") for img in images]
        endpoint = f"{self.base_url}/api/generate"
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            http_resp = execute_with_retry(
                lambda: client.post(endpoint, json=payload),
                provider=self,
                sleep_fn=self.sleep_fn,
            )
            data = http_resp.json()

        content = data.get("response", "")
        in_eval = data.get("prompt_eval_count")
        out_eval = data.get("eval_count")
        if in_eval is not None and out_eval is not None:
            in_toks = int(in_eval)
            out_toks = int(out_eval)
            estimated = False
        else:
            in_toks = estimate_tokens_from_chars(prompt)
            out_toks = estimate_tokens_from_chars(content)
            estimated = True

        llm_resp = LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=0.0,  # 100% free offline
            estimated=estimated,
        )
        self.record_usage(llm_resp)
        return llm_resp

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> LLMResponse:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(1)
        sem = self._semaphore

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        endpoint = f"{self.base_url}/api/generate"
        async with sem:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                http_resp = await aexecute_with_retry(
                    lambda: client.post(endpoint, json=payload),
                    provider=self,
                    asleep_fn=self.asleep_fn,
                )
                data = http_resp.json()

        content = data.get("response", "")
        in_eval = data.get("prompt_eval_count")
        out_eval = data.get("eval_count")
        if in_eval is not None and out_eval is not None:
            in_toks = int(in_eval)
            out_toks = int(out_eval)
            estimated = False
        else:
            in_toks = estimate_tokens_from_chars(prompt)
            out_toks = estimate_tokens_from_chars(content)
            estimated = True

        llm_resp = LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=0.0,
            estimated=estimated,
        )
        self.record_usage(llm_resp)
        return llm_resp


class FailoverLLMProvider(BaseLLMProvider):
    """High-availability provider wrapper that executes automated failover across fallback models.

    If the primary provider hits a 429 Rate Limit, 529 Overloaded, network timeout,
    or provider error, FailoverLLMProvider transparently retries with the next available
    fallback provider in the synaptic chain (e.g. Anthropic -> OpenAI -> Ollama -> Mock).
    """

    def __init__(
        self,
        primary: BaseLLMProvider,
        fallbacks: list[BaseLLMProvider] | None = None,
        on_failover: Callable[[str, str, Exception], None] | None = None,
    ):
        self.primary = primary
        self.fallbacks = fallbacks or []
        self.on_failover = on_failover
        self.failover_history: list[dict[str, Any]] = []

    def set_ledger(self, ledger: UsageLedger | None) -> None:
        """Attach UsageLedger to self and all underlying cascade providers."""
        self.usage_ledger = ledger
        if hasattr(self.primary, "set_ledger"):
            self.primary.set_ledger(ledger)
        for fb in self.fallbacks:
            if hasattr(fb, "set_ledger"):
                fb.set_ledger(ledger)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        images: list[Any] | None = None,
    ) -> LLMResponse:
        chain = [self.primary] + self.fallbacks
        last_error = None
        failures = []

        for idx, provider in enumerate(chain):
            if getattr(provider, "is_disabled", False):
                continue
            p_name = type(provider).__name__
            next_p = type(chain[idx + 1]).__name__ if idx + 1 < len(chain) else "None"
            prov_tag = getattr(provider, "provider_name", "")
            if not prov_tag or prov_tag == "base":
                prov_tag = p_name
            try:
                gen_kw: dict[str, Any] = {
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if images:
                    gen_kw["images"] = images
                return provider.generate(**gen_kw)
            except Exception as e:
                err = classify_http_error(
                    e, provider=prov_tag, model=getattr(provider, "model", None)
                )
                if isinstance(err, ProviderAuthError):
                    provider.is_disabled = True
                    provider.disabled_reason = str(err)
                last_error = err
                fail_record = {
                    "provider": p_name,
                    "model": getattr(provider, "model", "unknown"),
                    "error_class": type(err).__name__,
                    "status": getattr(err, "status", None),
                    "hint": getattr(err, "hint", ""),
                    "reason": redact_secrets(str(err)),
                }
                failures.append(fail_record)
                self.failover_history.append(
                    {
                        "from": p_name,
                        "to": next_p,
                        "error_class": type(err).__name__,
                        "hint": getattr(err, "hint", ""),
                        "error": redact_secrets(str(err)),
                        "timestamp": time.time(),
                    }
                )
                if self.on_failover:
                    try:
                        self.on_failover(p_name, next_p, err)
                    except Exception as e:
                        logger.debug(
                            "on_failover callback raised exception: %s", e, exc_info=True
                        )  # best-effort: callback error must not crash failover loop

        summary_items = []
        for f in failures:
            item = f"{f['provider']} [{f.get('error_class', 'Error')}]: {f.get('reason', 'Failed')}"
            if f.get("hint"):
                item += f" -> Hint: {f['hint']}"
            summary_items.append(item)
        summary = " | ".join(summary_items) if summary_items else str(last_error)
        raise ProviderExhaustedError(
            f"All synaptic providers in failover chain exhausted: {summary}",
            failures=failures,
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        chain = [self.primary] + self.fallbacks
        last_error = None
        failures = []

        for idx, provider in enumerate(chain):
            if getattr(provider, "is_disabled", False):
                continue
            p_name = type(provider).__name__
            next_p = type(chain[idx + 1]).__name__ if idx + 1 < len(chain) else "None"
            prov_tag = getattr(provider, "provider_name", "")
            if not prov_tag or prov_tag == "base":
                prov_tag = p_name
            try:
                return await provider.agenerate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                err = classify_http_error(
                    e, provider=prov_tag, model=getattr(provider, "model", None)
                )
                if isinstance(err, ProviderAuthError):
                    provider.is_disabled = True
                    provider.disabled_reason = str(err)
                last_error = err
                fail_record = {
                    "provider": p_name,
                    "model": getattr(provider, "model", "unknown"),
                    "error_class": type(err).__name__,
                    "status": getattr(err, "status", None),
                    "hint": getattr(err, "hint", ""),
                    "reason": redact_secrets(str(err)),
                }
                failures.append(fail_record)
                self.failover_history.append(
                    {
                        "from": p_name,
                        "to": next_p,
                        "error_class": type(err).__name__,
                        "hint": getattr(err, "hint", ""),
                        "error": redact_secrets(str(err)),
                        "timestamp": time.time(),
                    }
                )
                if self.on_failover:
                    try:
                        self.on_failover(p_name, next_p, err)
                    except Exception as e:
                        logger.debug(
                            "Async on_failover callback raised exception: %s", e, exc_info=True
                        )  # best-effort: callback error must not crash failover loop

        summary_items = []
        for f in failures:
            item = f"{f['provider']} [{f.get('error_class', 'Error')}]: {f.get('reason', 'Failed')}"
            if f.get("hint"):
                item += f" -> Hint: {f['hint']}"
            summary_items.append(item)
        summary = " | ".join(summary_items) if summary_items else str(last_error)
        raise ProviderExhaustedError(
            f"All synaptic providers in failover chain exhausted: {summary}",
            failures=failures,
        )

    def get_redactions_count(self) -> int:
        cnt = getattr(self.primary, "get_redactions_count", lambda: 0)()
        for fb in self.fallbacks:
            cnt += getattr(fb, "get_redactions_count", lambda: 0)()
        return cnt


# ==============================================================================
# Custom Provider Registry (P8.1)
# ==============================================================================
_CUSTOM_PROVIDERS: dict[str, type[BaseLLMProvider] | Callable[..., BaseLLMProvider]] = {}


def register_provider(
    name: str,
    provider_cls_or_factory: type[BaseLLMProvider] | Callable[..., BaseLLMProvider],
) -> None:
    """Register a custom LLM provider backend under a normalized name."""
    _CUSTOM_PROVIDERS[name.lower().strip()] = provider_cls_or_factory


def unregister_provider(name: str) -> None:
    """Unregister a custom LLM provider (useful for test isolation)."""
    _CUSTOM_PROVIDERS.pop(name.lower().strip(), None)


def get_registered_provider(
    name: str,
) -> type[BaseLLMProvider] | Callable[..., BaseLLMProvider] | None:
    """Look up a custom registered provider by name."""
    return _CUSTOM_PROVIDERS.get(name.lower().strip())


def list_registered_providers() -> list[str]:
    """Return a list of all currently registered custom provider names."""
    return sorted(_CUSTOM_PROVIDERS.keys())


def _build_from_pool_entry(entry: LLMConfigEntry, dry_run: bool = False) -> BaseLLMProvider:
    """Build a concrete provider instance from an individual pool configuration entry."""
    p_name = entry.provider.lower().strip()
    key = entry.api_key or resolve_api_key(p_name)[0]
    is_dry = dry_run or (os.getenv("OCTOFLOW_DRY_RUN") == "1")

    # Check custom provider registry
    custom_cls = get_registered_provider(p_name)
    if custom_cls is not None:
        try:
            return custom_cls(
                base_url=entry.base_url,
                model=entry.model or "default",
                api_key=key,
            )
        except TypeError:
            return custom_cls()

    if p_name in ["gemini", "google"]:
        model = entry.model if entry.model and entry.model != "default" else "gemini-2.0-flash"
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[
                    {
                        "name": entry.name,
                        "provider": entry.provider,
                        "model": model,
                        "reason": "Missing API key",
                    }
                ],
            )
        return GeminiProvider(api_key=key, model=model)
    elif p_name in ["grok", "xai"]:
        model = entry.model if entry.model and entry.model != "default" else "grok-2-1212"
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[
                    {
                        "name": entry.name,
                        "provider": entry.provider,
                        "model": model,
                        "reason": "Missing API key",
                    }
                ],
            )
        return GrokProvider(api_key=key, model=model)
    elif p_name == "deepseek":
        model = entry.model if entry.model and entry.model != "default" else "deepseek-chat"
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[
                    {
                        "name": entry.name,
                        "provider": entry.provider,
                        "model": model,
                        "reason": "Missing API key",
                    }
                ],
            )
        return DeepSeekProvider(api_key=key, model=model)
    elif p_name == "anthropic":
        model = (
            entry.model
            if entry.model and entry.model != "default"
            else "claude-3-5-sonnet-20241022"
        )
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[
                    {
                        "name": entry.name,
                        "provider": entry.provider,
                        "model": model,
                        "reason": "Missing API key",
                    }
                ],
            )
        return AnthropicProvider(api_key=key, model=model)
    elif p_name == "openai":
        model = entry.model if entry.model and entry.model != "default" else "gpt-4o"
        base_url = entry.base_url or "https://api.openai.com/v1"
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[
                    {
                        "name": entry.name,
                        "provider": entry.provider,
                        "model": model,
                        "reason": "Missing API key",
                    }
                ],
            )
        return OpenAIProvider(api_key=key, model=model, base_url=base_url)
    elif p_name == "ollama":
        model = entry.model if entry.model and entry.model != "default" else "qwen2.5-coder:7b"
        base_url = entry.base_url or "http://localhost:11434"
        return OllamaProvider(base_url=base_url, model=model)
    elif p_name in ["custom", "vllm", "local"]:
        model = entry.model if entry.model and entry.model != "default" else "custom-model"
        base_url = entry.base_url or "http://localhost:8000/v1"
        return OpenAIProvider(api_key=key or "custom-key", model=model, base_url=base_url)
    elif p_name == "mock":
        if is_dry:
            return MockLLMProvider()
        raise ProviderExhaustedError(
            "Mock LLM provider requested without --dry-run. Pass --dry-run or configure a real provider.",
            failures=[
                {
                    "name": entry.name,
                    "provider": "mock",
                    "model": "mock",
                    "reason": "Mock provider requires --dry-run",
                }
            ],
        )
    if is_dry:
        return MockLLMProvider()
    raise ProviderExhaustedError(
        f"Unsupported provider backend '{p_name}'.",
        failures=[
            {
                "name": entry.name,
                "provider": p_name,
                "model": getattr(entry, "model", "unknown"),
                "reason": "Unsupported provider backend",
            }
        ],
    )


class CascadePoolLLMProvider(BaseLLMProvider):
    """Multi-URL LLM Cascade with hot-swap token and rate-limit failover.

    Users and developers can configure as many or as few LLMs/URLs as they choose.
    If 1 model runs out of tokens or hits a rate limit (429, QuotaExceeded, etc.),
    it dynamically falls back to the next model in the user's configured pool.
    """

    def __init__(
        self,
        entries: list[LLMConfigEntry],
        on_failover: Callable[[dict[str, Any]], None] | None = None,
        dry_run: bool = False,
    ):
        self.entries = [e for e in sorted(entries, key=lambda x: x.priority) if e.enabled]
        self.on_failover = on_failover
        self.dry_run = dry_run or (os.getenv("OCTOFLOW_DRY_RUN") == "1")
        self.active_index = 0
        self.providers: list[BaseLLMProvider] = []
        self.telemetry: list[dict[str, Any]] = []

        for e in self.entries:
            try:
                prov = _build_from_pool_entry(e, dry_run=self.dry_run)
                self.providers.append(prov)
                self.telemetry.append(
                    {
                        "id": e.id,
                        "name": e.name,
                        "provider": e.provider,
                        "model": e.model,
                        "base_url": e.base_url or "",
                        "status": "STANDBY",
                        "tokens_used": 0,
                        "failover_count": 0,
                        "last_error": None,
                    }
                )
            except ProviderExhaustedError as pe:
                self.telemetry.append(
                    {
                        "id": e.id,
                        "name": e.name,
                        "provider": e.provider,
                        "model": e.model,
                        "base_url": e.base_url or "",
                        "status": "EXHAUSTED",
                        "tokens_used": 0,
                        "failover_count": 0,
                        "last_error": str(pe),
                    }
                )

        if self.telemetry:
            self.telemetry[0]["status"] = "ACTIVE"

    def get_status_summary(self) -> list[dict[str, Any]]:
        """Return live telemetry snapshot of all configured LLMs in pool."""
        return list(self.telemetry)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        images: list[Any] | None = None,
    ) -> LLMResponse:
        if not self.providers:
            if self.dry_run:
                return MockLLMProvider().generate(prompt, system_prompt, temperature, max_tokens)
            failures = [
                {
                    "name": t.get("name", "unknown"),
                    "provider": t.get("provider", "unknown"),
                    "model": t.get("model", "unknown"),
                    "reason": t.get("last_error") or "No valid provider instantiated",
                }
                for t in self.telemetry
            ]
            summary = (
                "; ".join(f"{f['provider']}:{f['model']} ({f['reason']})" for f in failures)
                if failures
                else "no providers configured in cascade pool"
            )
            raise ProviderExhaustedError(
                f"All configured LLM providers in cascade pool exhausted: {summary}",
                failures=failures,
            )

        start_idx = self.active_index
        n = len(self.providers)
        last_err = None

        for attempt_offset in range(n):
            idx = (start_idx + attempt_offset) % n
            provider = self.providers[idx]
            t = self.telemetry[idx]

            if (
                getattr(provider, "is_disabled", False) or t["status"] in ["DISABLED", "EXHAUSTED"]
            ) and attempt_offset < n - 1:
                continue

            t["status"] = "ACTIVE"
            self.active_index = idx

            try:
                gen_kw: dict[str, Any] = {
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if images:
                    gen_kw["images"] = images
                resp = provider.generate(**gen_kw)
                t["tokens_used"] += resp.total_tokens
                return resp
            except Exception as e:
                err = classify_http_error(
                    e, provider=t.get("provider", "unknown"), model=t.get("model")
                )
                last_err = err
                err_str = redact_secrets(str(err))
                if isinstance(err, ProviderAuthError):
                    provider.is_disabled = True
                    t["status"] = "DISABLED"
                elif isinstance(err, ProviderRateLimitError):
                    t["status"] = "EXHAUSTED"
                else:
                    t["status"] = "ERROR"
                t["error_class"] = type(err).__name__
                t["hint"] = getattr(err, "hint", "")
                t["last_error"] = err_str
                t["failover_count"] += 1

                next_idx = (idx + 1) % n
                next_t = self.telemetry[next_idx]
                next_t["status"] = "ACTIVE"
                self.active_index = next_idx

                failover_event = {
                    "from_id": t["id"],
                    "from_name": t["name"],
                    "to_id": next_t["id"],
                    "to_name": next_t["name"],
                    "reason": err_str,
                    "error_class": type(err).__name__,
                    "hint": getattr(err, "hint", ""),
                    "is_rate_limit": isinstance(err, ProviderRateLimitError),
                    "timestamp": time.time(),
                }
                if self.on_failover:
                    try:
                        self.on_failover(failover_event)
                    except Exception as e:
                        logger.debug(
                            "Cascade failover callback raised exception: %s", e, exc_info=True
                        )  # best-effort: callback error must not interrupt cascade

        if self.dry_run:
            import logging

            logging.getLogger("octoflow").warning(
                f"All configured LLM providers in cascade pool exhausted ({last_err}). Falling back to cephalopod neural heuristic inference."
            )
            return MockLLMProvider().generate(prompt, system_prompt, temperature, max_tokens)

        failures = [
            {
                "name": t.get("name", "unknown"),
                "provider": t.get("provider", "unknown"),
                "model": t.get("model", "unknown"),
                "error_class": t.get(
                    "error_class", type(last_err).__name__ if last_err else "ProviderError"
                ),
                "hint": t.get("hint", getattr(last_err, "hint", "")),
                "reason": t.get("last_error") or "exhausted or unavailable",
            }
            for t in self.telemetry
        ]
        summary_items = []
        for f in failures:
            item = f"{f['provider']}:{f['model']} [{f.get('error_class', 'Error')}]: {f.get('reason', 'Failed')}"
            if f.get("hint"):
                item += f" -> Hint: {f['hint']}"
            summary_items.append(item)
        summary = "; ".join(summary_items)
        raise ProviderExhaustedError(
            f"All configured LLM providers in cascade pool exhausted: {summary}",
            failures=failures,
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        import asyncio

        return await asyncio.to_thread(
            self.generate, prompt, system_prompt, temperature, max_tokens
        )

    def get_redactions_count(self) -> int:
        cnt = 0
        for p in self.providers.values():
            cnt += getattr(p, "get_redactions_count", lambda: 0)()
        return cnt


_MODEL_PREFIX_TO_PROVIDER: tuple[tuple[str, str], ...] = (
    ("claude", "anthropic"),
    ("gpt", "openai"),
    ("o1-", "openai"),
    ("o3-", "openai"),
    ("o4-", "openai"),
    ("gemini", "gemini"),
    ("grok", "grok"),
    ("deepseek", "deepseek"),
    ("qwen", "ollama"),
    ("llama", "ollama"),
    ("codellama", "ollama"),
    ("mistral", "ollama"),
)


def resolve_provider_and_model(raw: str) -> tuple[str, str | None]:
    """Normalize a provider or model identifier into (provider_name, model_name_or_None)."""
    val = (raw or "").strip()
    lower = val.lower()
    for prefix, provider in _MODEL_PREFIX_TO_PROVIDER:
        if lower.startswith(prefix):
            return provider, val
    return lower, None


def _build_single_provider(
    provider_name: str, config: OctoFlowConfig, tier: str | None = None, dry_run: bool = False
) -> BaseLLMProvider:
    """Helper to instantiate an individual provider backend."""
    p_name, inferred_model = resolve_provider_and_model(provider_name)
    if inferred_model and not getattr(config, "model_name", None):
        config.model_name = inferred_model
    is_dry = dry_run or getattr(config, "dry_run", False) or (os.getenv("OCTOFLOW_DRY_RUN") == "1")
    redact_flag = getattr(config, "privacy_redact_outbound", True)

    # Check custom provider registry first
    custom_cls = get_registered_provider(p_name)
    if custom_cls is not None:
        try:
            return custom_cls(
                base_url=config.base_url,
                model=config.model_name or "default",
                api_key=config.api_key,
                timeout=getattr(config, "timeout", None),
            )
        except TypeError:
            return custom_cls()

    if p_name in ("fake", "replay"):
        from octoflow.bench import FakeBenchmarkProvider

        return FakeBenchmarkProvider()

    if p_name == "mock":
        if is_dry or getattr(config, "allow_mock", False) or getattr(config, "is_bench", False):
            return MockLLMProvider()
        raise ProviderExhaustedError(
            "Mock LLM provider requested without --dry-run. Pass --dry-run or configure a real provider.",
            failures=[
                {"provider": "mock", "model": "mock", "reason": "mock provider requires --dry-run"}
            ],
        )

    elif p_name == "anthropic":
        api_key = config.anthropic_api_key or config.api_key or resolve_api_key("anthropic")[0]
        if tier == "fast":
            model = config.fast_model or "claude-3-5-haiku-20241022"
        elif tier == "frontier":
            model = config.frontier_model or "claude-3-7-sonnet-20250219"
        else:
            model = config.model_name or "claude-3-5-sonnet-20241022"
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "Anthropic provider misconfigured: missing ANTHROPIC_API_KEY",
                failures=[
                    {"provider": "anthropic", "model": model, "reason": "missing ANTHROPIC_API_KEY"}
                ],
            )
        return AnthropicProvider(api_key=api_key, model=model, redact_outbound=redact_flag)

    elif p_name == "openai":
        api_key = config.openai_api_key or config.api_key or resolve_api_key("openai")[0]
        if tier == "fast":
            model = config.fast_model or "gpt-4o-mini"
        elif tier == "frontier":
            model = config.frontier_model or "o3-mini"
        else:
            model = (
                config.model_name
                if (
                    "gpt" in config.model_name
                    or "o3" in config.model_name
                    or "o1" in config.model_name
                )
                else "gpt-4o"
            )
        base_url = config.base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "OpenAI provider misconfigured: missing OPENAI_API_KEY",
                failures=[
                    {"provider": "openai", "model": model, "reason": "missing OPENAI_API_KEY"}
                ],
            )
        return OpenAIProvider(api_key=api_key, model=model, base_url=base_url, redact_outbound=redact_flag)

    elif p_name in ["gemini", "google"]:
        api_key = config.gemini_api_key or config.api_key or resolve_api_key("gemini")[0]
        model = config.model_name if "gemini" in config.model_name else "gemini-2.0-flash"
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "Gemini provider misconfigured: missing GEMINI_API_KEY",
                failures=[
                    {"provider": "gemini", "model": model, "reason": "missing GEMINI_API_KEY"}
                ],
            )
        return GeminiProvider(api_key=api_key, model=model, redact_outbound=redact_flag)

    elif p_name in ["grok", "xai"]:
        api_key = config.grok_api_key or config.api_key or resolve_api_key("grok")[0]
        model = config.model_name if "grok" in config.model_name else "grok-2-1212"
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "Grok provider misconfigured: missing GROK_API_KEY",
                failures=[{"provider": "grok", "model": model, "reason": "missing GROK_API_KEY"}],
            )
        return GrokProvider(api_key=api_key, model=model, redact_outbound=redact_flag)

    elif p_name in ["deepseek"]:
        api_key = config.deepseek_api_key or config.api_key or resolve_api_key("deepseek")[0]
        model = config.model_name if "deepseek" in config.model_name else "deepseek-chat"
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "DeepSeek provider misconfigured: missing DEEPSEEK_API_KEY",
                failures=[
                    {"provider": "deepseek", "model": model, "reason": "missing DEEPSEEK_API_KEY"}
                ],
            )
        return DeepSeekProvider(api_key=api_key, model=model, redact_outbound=redact_flag)

    elif p_name == "ollama":
        url = config.base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        if config.model_provider == "ollama":
            # Homogeneous Ollama execution (e.g. local bench with single pulled model)
            resolved_default = (
                config.model_name
                if config.model_name and not any(k in config.model_name for k in ("claude", "gpt"))
                else "qwen2.5-coder:7b"
            )
            if tier == "fast":
                model = config.fast_model or resolved_default
            elif tier == "frontier":
                model = config.frontier_model or resolved_default
            else:
                model = resolved_default
        else:
            # Heterogeneous routing (e.g. Anthropic frontier + Ollama fast)
            if tier == "fast":
                model = config.fast_model or "qwen2.5-coder:1.5b"
            elif tier == "frontier":
                model = config.frontier_model or "deepseek-coder-v2:16b"
            else:
                model = (
                    config.model_name
                    if config.model_name
                    and not any(k in config.model_name for k in ("claude", "gpt"))
                    else "qwen2.5-coder:7b"
                )
        return OllamaProvider(base_url=url, model=model)

    if is_dry:
        return MockLLMProvider()
    raise ProviderExhaustedError(
        f"Unsupported provider backend '{provider_name}'",
        failures=[{"provider": provider_name, "reason": "unsupported provider backend"}],
    )


def get_llm_provider(
    config: OctoFlowConfig, tier: str | None = None, dry_run: bool = False
) -> BaseLLMProvider:
    """Factory creating configured LLM provider, optionally tailored by cognitive tier ('frontier', 'balanced', 'fast').

    Supports dynamic multi-URL cascade pools with auto-failover, heterogeneous routing, and fallbacks.
    """
    is_dry = dry_run or getattr(config, "dry_run", False) or (os.getenv("OCTOFLOW_DRY_RUN") == "1")
    force_live = (os.getenv("OCTOFLOW_FORCE_LIVE") == "1") or getattr(config, "force_live", False)
    is_testing = not force_live and (
        ("PYTEST_CURRENT_TEST" in os.environ)
        or ("pytest" in sys.modules)
        or (os.getenv("OCTOFLOW_TESTING") == "1")
    )

    # 1. Determine target provider for requested cognitive tier
    provider_name = config.model_provider.lower()
    if tier == "frontier" and config.frontier_provider:
        provider_name = config.frontier_provider.lower()
    elif tier == "fast" and config.fast_provider:
        provider_name = config.fast_provider.lower()

    if provider_name == "fake":
        from octoflow.bench import FakeBenchmarkProvider

        return FakeBenchmarkProvider()

    if provider_name == "mock":
        if (
            is_dry
            or is_testing
            or getattr(config, "allow_mock", False)
            or getattr(config, "is_bench", False)
        ):
            return MockLLMProvider()
        raise ProviderExhaustedError(
            "Mock LLM provider requested without --dry-run. Pass --dry-run or configure a real provider.",
            failures=[
                {"provider": "mock", "model": "mock", "reason": "mock provider requires --dry-run"}
            ],
        )

    # 2. If user configured an LLM cascade pool and requested pool routing (or did not request a specific single provider)
    is_explicit_single = provider_name not in ["pool", "cascade", "cascade_pool"]
    if not is_explicit_single or provider_name in ["pool", "cascade", "cascade_pool"]:
        if getattr(config, "llm_pool", None) and len(config.llm_pool) > 0:
            active_entries = [e for e in config.llm_pool if e.enabled]
            if active_entries:
                return CascadePoolLLMProvider(entries=active_entries, dry_run=is_dry)

    primary = _build_single_provider(provider_name, config, tier=tier, dry_run=is_dry)

    # If failover is enabled and primary is a cloud provider, configure fallbacks
    if getattr(config, "enable_failover", False) and provider_name not in ["mock"]:
        fallbacks: list[BaseLLMProvider] = []
        fb_names = getattr(config, "fallback_providers", ["openai", "ollama"])
        for fb_name in fb_names:
            if fb_name.lower() != provider_name:
                try:
                    fallbacks.append(
                        _build_single_provider(fb_name, config, tier=tier, dry_run=is_dry)
                    )
                except ProviderExhaustedError as e:
                    logger.debug(
                        "Fallback candidate %s unavailable: %s", fb_name, e
                    )  # best-effort: skip unconfigured fallback and check next

        if fallbacks:
            return FailoverLLMProvider(primary=primary, fallbacks=fallbacks)

    return primary
