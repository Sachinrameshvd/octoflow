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
from typing import Any, Callable, Dict, List, Optional, Union
from pydantic import BaseModel
import httpx

from octoflow.config import OctoFlowConfig, LLMConfigEntry
from octoflow.outcome import ProviderExhaustedError, OctoFlowError


def redact_secrets(text: str) -> str:
    """Sanitize secrets, API keys, and Bearer tokens from text, exceptions, and logs."""
    if not text:
        return ""
    # Authorization header with Bearer token (e.g. Authorization: Bearer <token>)
    text = re.sub(r'Authorization:\s*Bearer\s+\S+', 'Authorization: Bearer [REDACTED_TOKEN]', text, flags=re.IGNORECASE)
    # Standalone Bearer tokens (e.g. Bearer <token>)
    text = re.sub(r'(?<!Authorization:\s)(?<!Authorization:)\bBearer\s+[a-zA-Z0-9_\-\.]{10,}', 'Bearer [REDACTED_TOKEN]', text, flags=re.IGNORECASE)
    # Non-bearer Authorization header values (e.g. Basic, Token, etc.)
    text = re.sub(r'Authorization:\s*(?!\s*Bearer\s+\[REDACTED_TOKEN\])[^\r\n]+', 'Authorization: [REDACTED]', text, flags=re.IGNORECASE)
    # API keys: Anthropic, OpenAI, Grok, etc. (sk-...)
    text = re.sub(r'sk-[a-zA-Z0-9_\-]{16,}', '[REDACTED_KEY]', text)
    # Google AI keys (AIza...)
    text = re.sub(r'AIza[0-9A-Za-z\-_]{30,}', '[REDACTED_KEY]', text)
    # GitHub personal access tokens
    text = re.sub(r'(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{20,}', '[REDACTED_GITHUB_TOKEN]', text)
    # Key-value query/header assignments
    text = re.sub(r'(api_key|apikey|key|token|secret|password)=([^\s&"\']+)', r'\1=[REDACTED]', text, flags=re.IGNORECASE)
    return text


_sanitize_secret_text = redact_secrets


# ==============================================================================
# Provider Error Taxonomy (Task 1)
# ==============================================================================
class ProviderError(OctoFlowError):
    """Base error for all provider-related failures.

    Attributes:
        provider: Identifier of the provider ('anthropic', 'openai', 'ollama', etc.)
        status: HTTP status code, if applicable (e.g. 401, 429, 503)
        hint: Actionable guidance instructing the user what to do next
    """

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        status: Optional[int] = None,
        hint: str = "",
    ):
        self.provider = provider
        self.status = status
        self.hint = redact_secrets(hint)
        self.raw_message = message
        clean_msg = redact_secrets(message)
        full_msg = f"[{provider}]"
        if status is not None:
            full_msg += f" (HTTP {status})"
        full_msg += f" {clean_msg}"
        if self.hint:
            full_msg += f" -> Hint: {self.hint}"
        super().__init__(full_msg)


class ProviderAuthError(ProviderError):
    """Authentication or authorization failure: 401, 403, or 400 with invalid-key signature."""
    pass


class ProviderRateLimitError(ProviderError):
    """Rate limit or quota exhaustion: 429 error honoring Retry-After headers."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        status: Optional[int] = 429,
        hint: str = "",
        retry_after: Optional[float] = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, provider=provider, status=status, hint=hint)


class ProviderTransientError(ProviderError):
    """Transient service disruptions: 5xx errors, timeouts, and network connection drops."""
    pass


class ProviderRequestError(ProviderError):
    """Client request errors: other 4xx errors, bad payloads, and context-length violations."""
    pass


class ProviderUnavailableError(ProviderError):
    """Service or daemon unavailable: Ollama daemon stopped or model not pulled."""
    pass


# ==============================================================================
# Error Classifier (Task 2 & 4)
# ==============================================================================
def classify_http_error(
    error_or_status: Any,
    provider: str = "unknown",
    response: Optional[httpx.Response] = None,
    body: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    model: Optional[str] = None,
) -> ProviderError:
    """Classifies an HTTP status code, response, or exception into the ProviderError taxonomy."""
    p_name = provider.lower().strip()
    status_code: Optional[int] = None
    response_text: str = body or ""
    resp_headers: Dict[str, str] = dict(headers or {})

    if isinstance(error_or_status, httpx.HTTPStatusError):
        response = error_or_status.response

    if response is not None:
        status_code = response.status_code
        if not response_text:
            try:
                response_text = response.text
            except Exception:
                response_text = ""
        if not resp_headers:
            resp_headers = {k.lower(): v for k, v in response.headers.items()}
    elif isinstance(error_or_status, int):
        status_code = error_or_status
    elif isinstance(error_or_status, ProviderError):
        return error_or_status
    elif isinstance(error_or_status, Exception):
        if hasattr(error_or_status, "status_code"):
            status_code = getattr(error_or_status, "status_code")
        elif hasattr(error_or_status, "status"):
            status_code = getattr(error_or_status, "status")
        if status_code is None:
            m = re.search(r'\b(4\d\d|5\d\d)\b', str(error_or_status))
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
    msg = clean_text or (str(error_or_status) if not isinstance(error_or_status, int) else f"HTTP {status_code}")
    clean_msg = redact_secrets(msg)

    # 1. Ollama specific handling
    if p_name == "ollama":
        if status_code == 404 or "not found" in clean_text.lower():
            m = model or "model"
            return ProviderUnavailableError(
                f"Model '{m}' not found in Ollama",
                provider=provider,
                status=404,
                hint=f"run: ollama pull {m}",
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
        is_key_error = any(phrase in lower_body for phrase in [
            "invalid_api_key", "invalid api key", "authentication_error",
            "invalid_x_api_key", "api_key_invalid", "unauthorized",
            "api key not valid", "incorrect api key", "key not found"
        ])
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
    is_rate_limit = (
        status_code == 429
        or any(k in clean_text.lower() or k in clean_msg.lower() for k in [
            "429", "rate limit", "rate_limit", "quota", "resource_exhausted",
            "insufficient_quota", "credit", "exceeded", "too many requests"
        ])
    )
    if is_rate_limit:
        retry_after: Optional[float] = None
        if "retry-after" in norm_headers:
            try:
                retry_after = float(norm_headers["retry-after"])
            except (ValueError, TypeError):
                pass
        if retry_after is None and clean_text:
            try:
                parsed = json.loads(clean_text)
                if isinstance(parsed, dict):
                    ra = parsed.get("retry_after") or parsed.get("error", {}).get("retry_after")
                    if ra:
                        retry_after = float(ra)
            except Exception:
                pass

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
    sync_sleep: Optional[Callable[[float], None]] = None,
    async_sleep: Optional[Callable[[float], Any]] = None,
):
    """Inject global sleep functions for testing backoff and retries without real-time delays."""
    global _DEFAULT_SLEEP_FN, _DEFAULT_ASYNC_SLEEP_FN
    if sync_sleep is not None:
        _DEFAULT_SLEEP_FN = sync_sleep
    if async_sleep is not None:
        _DEFAULT_ASYNC_SLEEP_FN = async_sleep


def reset_sleep_functions():
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
    model: Optional[str] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> httpx.Response:
    """Executes an HTTP request honoring OctoFlow retry and backoff policy.

    - Auth errors: 0 retries; marks provider disabled for session, raises ProviderAuthError.
    - Rate limits: retries at most twice, honoring Retry-After or exponential backoff with jitter capped at 30s.
    - Transient errors: retries at most twice, using 0.5s and 1.5s delays plus jitter.
    - Request/Unavailable errors: 0 retries, raises immediately.
    """
    provider_name = getattr(provider, "provider_name", str(provider)) if not isinstance(provider, str) else provider
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
                raise err

            elif isinstance(err, ProviderRateLimitError):
                if rate_limit_retries < 2:
                    rate_limit_retries += 1
                    if err.retry_after is not None and err.retry_after > 0:
                        delay = min(err.retry_after, 30.0)
                    else:
                        delay = min(1.0 * (2 ** (rate_limit_retries - 1)) + random.uniform(0.1, 0.4), 30.0)
                    actual_sleep(delay)
                    continue
                raise err

            elif isinstance(err, ProviderTransientError):
                if transient_retries < 2:
                    transient_retries += 1
                    base_delay = 0.5 if transient_retries == 1 else 1.5
                    delay = base_delay + random.uniform(0.05, 0.2)
                    actual_sleep(delay)
                    continue
                raise err

            else:
                raise err


async def aexecute_with_retry(
    coro_fn: Callable[[], Any],
    provider: Any = "unknown",
    model: Optional[str] = None,
    asleep_fn: Optional[Callable[[float], Any]] = None,
) -> httpx.Response:
    """Asynchronously executes an HTTP request honoring OctoFlow retry and backoff policy."""
    provider_name = getattr(provider, "provider_name", str(provider)) if not isinstance(provider, str) else provider
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

    async def _do_sleep(d: float):
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
            return resp
        except Exception as raw_e:
            err = classify_http_error(raw_e, provider=provider_name, model=model_name)

            if isinstance(err, ProviderAuthError):
                if isinstance(provider, BaseLLMProvider):
                    provider.is_disabled = True
                    provider.disabled_reason = str(err)
                raise err

            elif isinstance(err, ProviderRateLimitError):
                if rate_limit_retries < 2:
                    rate_limit_retries += 1
                    if err.retry_after is not None and err.retry_after > 0:
                        delay = min(err.retry_after, 30.0)
                    else:
                        delay = min(1.0 * (2 ** (rate_limit_retries - 1)) + random.uniform(0.1, 0.4), 30.0)
                    await _do_sleep(delay)
                    continue
                raise err

            elif isinstance(err, ProviderTransientError):
                if transient_retries < 2:
                    transient_retries += 1
                    base_delay = 0.5 if transient_retries == 1 else 1.5
                    delay = base_delay + random.uniform(0.05, 0.2)
                    await _do_sleep(delay)
                    continue
                raise err

            else:
                raise err


def retry_http_request(fn: Callable[[], httpx.Response], max_retries: int = 3, base_delay: float = 1.0) -> httpx.Response:
    """Legacy helper: delegates to execute_with_retry."""
    return execute_with_retry(fn, provider="unknown")


async def aretry_http_request(coro_fn: Callable[[], Any], max_retries: int = 3, base_delay: float = 1.0) -> httpx.Response:
    """Legacy helper: delegates to aexecute_with_retry."""
    return await aexecute_with_retry(coro_fn, provider="unknown")


class LLMResponse(BaseModel):
    """Normalized response from an LLM call."""
    content: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    total_tokens: int = 0
    estimated_cost_dollars: float = 0.0
    tool_calls: List[Dict[str, Any]] = []


class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends."""
    provider_name: str = "base"
    model: str = "default"
    is_disabled: bool = False
    disabled_reason: Optional[str] = None
    sleep_fn: Optional[Callable[[float], None]] = None
    asleep_fn: Optional[Callable[[float], Any]] = None
    timeout: Optional[httpx.Timeout] = None

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
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
        return await asyncio.to_thread(self.generate, prompt, system_prompt, temperature, max_tokens)


class MockLLMProvider(BaseLLMProvider):
    """Deterministic, zero-cost LLM provider for unit tests and local simulation."""
    provider_name = "mock"
    model = "mock"

    def __init__(self, script_responses: Optional[Dict[str, str]] = None):
        self.script_responses = script_responses or {}
        self.call_count = 0
        self.total_tokens_spent = 0

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        self.call_count += 1
        prompt_lower = prompt.lower()

        # Check explicit custom scripts
        for pattern, response in self.script_responses.items():
            if pattern.lower() in prompt_lower:
                tokens_in = len(prompt) // 4
                tokens_out = len(response) // 4
                self.total_tokens_spent += (tokens_in + tokens_out)
                return LLMResponse(
                    content=response,
                    tokens_prompt=tokens_in,
                    tokens_completion=tokens_out,
                    total_tokens=tokens_in + tokens_out,
                    estimated_cost_dollars=0.0,
                )

        # Default intelligent mock responses for various agent roles
        if "developer question:" in prompt_lower or "inquiry:" in prompt_lower:
            role_hint = system_prompt.split(" (Arm")[0].replace("You are ", "").strip() if "You are " in system_prompt else "Specialist"
            content = (
                f"As the {role_hint}, I analyzed this domain carefully. "
                f"This decision enforces clean interface boundaries, high transaction concurrency, and robust data persistence. "
                f"All components adhere to the project specifications and pass AST pre-flight validation."
            )
        elif "test" in prompt_lower or "pytest" in prompt_lower:
            content = json.dumps({
                "action": "run_command",
                "command": "python -c 'print(\"1 passed in 0.01s\")'",
                "explanation": "Running unit test suite to verify code contracts.",
            })
        elif "write" in prompt_lower or "create" in prompt_lower:
            content = json.dumps({
                "action": "write_file",
                "path": "test_output.py",
                "content": "# Generated by OctoFlow Arm\ndef solve():\n    return True\n",
                "explanation": "Creating initial implementation file.",
            })
        elif "error" in prompt_lower or "fix" in prompt_lower:
            content = json.dumps({
                "action": "write_file",
                "path": "test_output.py",
                "content": "# Patched by OctoFlow Arm\ndef solve():\n    return True\n",
                "explanation": "Applying patch to resolve high sensory surprise error.",
            })
        else:
            content = json.dumps({
                "action": "mark_quiescent",
                "explanation": "Task objectives satisfied in full.",
            })

        tokens_in = len(prompt) // 4
        tokens_out = len(content) // 4
        self.total_tokens_spent += (tokens_in + tokens_out)

        return LLMResponse(
            content=content,
            tokens_prompt=tokens_in,
            tokens_completion=tokens_out,
            total_tokens=tokens_in + tokens_out,
            estimated_cost_dollars=0.0,
        )

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
    """Anthropic Claude API Provider (Claude 3.5 Sonnet / Opus)."""
    provider_name = "anthropic"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: Optional[httpx.Timeout] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
        asleep_fn: Optional[Callable[[float], Any]] = None,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or parameter required.")
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.timeout = timeout or DEFAULT_CLOUD_TIMEOUT
        self.sleep_fn = sleep_fn
        self.asleep_fn = asleep_fn

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = execute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                sleep_fn=self.sleep_fn,
            )
            data = resp.json()

        content = data["content"][0]["text"]
        in_toks = data.get("usage", {}).get("input_tokens", len(prompt) // 4)
        out_toks = data.get("usage", {}).get("output_tokens", len(content) // 4)

        # Claude 3.5 Sonnet pricing: $3 / MTok in, $15 / MTok out
        cost = (in_toks * 0.000003) + (out_toks * 0.000015)

        return LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=cost,
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await aexecute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                asleep_fn=self.asleep_fn,
            )
            data = resp.json()

        content = data["content"][0]["text"]
        in_toks = data.get("usage", {}).get("input_tokens", len(prompt) // 4)
        out_toks = data.get("usage", {}).get("output_tokens", len(content) // 4)
        cost = (in_toks * 0.000003) + (out_toks * 0.000015)

        return LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=cost,
        )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider (GPT-4o, GPT-4o-mini)."""
    provider_name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
        timeout: Optional[httpx.Timeout] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
        asleep_fn: Optional[Callable[[float], Any]] = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable or parameter required.")
        self.model = model
        raw_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        if not raw_url.endswith("/chat/completions"):
            self.base_url = f"{raw_url.rstrip('/')}/chat/completions"
        else:
            self.base_url = raw_url
        self.timeout = timeout or DEFAULT_CLOUD_TIMEOUT
        self.sleep_fn = sleep_fn
        self.asleep_fn = asleep_fn

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
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
        with httpx.Client(timeout=self.timeout) as client:
            resp = execute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                sleep_fn=self.sleep_fn,
            )
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        in_toks = data.get("usage", {}).get("prompt_tokens", len(prompt) // 4)
        out_toks = data.get("usage", {}).get("completion_tokens", len(content) // 4)

        # GPT-4o pricing: $2.50 / MTok in, $10 / MTok out
        cost = (in_toks * 0.0000025) + (out_toks * 0.000010)

        return LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=cost,
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await aexecute_with_retry(
                lambda: client.post(self.base_url, headers=headers, json=payload),
                provider=self,
                asleep_fn=self.asleep_fn,
            )
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        in_toks = data.get("usage", {}).get("prompt_tokens", len(prompt) // 4)
        out_toks = data.get("usage", {}).get("completion_tokens", len(content) // 4)
        cost = (in_toks * 0.0000025) + (out_toks * 0.000010)

        return LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=cost,
        )


class GeminiProvider(OpenAIProvider):
    """Google Gemini API Provider via OpenAI-compatible endpoint (Gemini 2.0 Flash / Pro)."""
    provider_name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash", base_url: Optional[str] = None, **kwargs):
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required.")
        url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai"
        super().__init__(api_key=key, model=model, base_url=url, **kwargs)


class GrokProvider(OpenAIProvider):
    """xAI Grok API Provider (Grok 2 / Grok beta)."""
    provider_name = "grok"

    def __init__(self, api_key: Optional[str] = None, model: str = "grok-2-1212", base_url: Optional[str] = None, **kwargs):
        key = api_key or os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        if not key:
            raise ValueError("XAI_API_KEY or GROK_API_KEY environment variable required.")
        url = base_url or "https://api.x.ai/v1"
        super().__init__(api_key=key, model=model, base_url=url, **kwargs)


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek API Provider (DeepSeek-V3 / DeepSeek-R1)."""
    provider_name = "deepseek"

    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat", base_url: Optional[str] = None, **kwargs):
        key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise ValueError("DEEPSEEK_API_KEY environment variable required.")
        url = base_url or "https://api.deepseek.com/v1"
        super().__init__(api_key=key, model=model, base_url=url, **kwargs)


class OllamaProvider(BaseLLMProvider):
    """Local, offline, 100% free Ollama Provider (DeepSeek-Coder, Qwen2.5, Llama-3)."""
    provider_name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:7b",
        timeout: Optional[httpx.Timeout] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
        asleep_fn: Optional[Callable[[float], Any]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout or DEFAULT_OLLAMA_TIMEOUT
        self.sleep_fn = sleep_fn
        self.asleep_fn = asleep_fn
        self._semaphore = None

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        endpoint = f"{self.base_url}/api/generate"
        with httpx.Client(timeout=self.timeout) as client:
            resp = execute_with_retry(
                lambda: client.post(endpoint, json=payload),
                provider=self,
                sleep_fn=self.sleep_fn,
            )
            data = resp.json()

        content = data.get("response", "")
        in_toks = data.get("prompt_eval_count", len(prompt) // 4)
        out_toks = data.get("eval_count", len(content) // 4)

        return LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=0.0,  # 100% free offline
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> LLMResponse:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(1)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        endpoint = f"{self.base_url}/api/generate"
        async with self._semaphore:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await aexecute_with_retry(
                    lambda: client.post(endpoint, json=payload),
                    provider=self,
                    asleep_fn=self.asleep_fn,
                )
                data = resp.json()

        content = data.get("response", "")
        in_toks = data.get("prompt_eval_count", len(prompt) // 4)
        out_toks = data.get("eval_count", len(content) // 4)

        return LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=0.0,
        )


class FailoverLLMProvider(BaseLLMProvider):
    """High-availability provider wrapper that executes automated failover across fallback models.

    If the primary provider hits a 429 Rate Limit, 529 Overloaded, network timeout,
    or provider error, FailoverLLMProvider transparently retries with the next available
    fallback provider in the synaptic chain (e.g. Anthropic -> OpenAI -> Ollama -> Mock).
    """

    def __init__(
        self,
        primary: BaseLLMProvider,
        fallbacks: Optional[List[BaseLLMProvider]] = None,
        on_failover: Optional[Callable[[str, str, Exception], None]] = None,
    ):
        self.primary = primary
        self.fallbacks = fallbacks or []
        self.on_failover = on_failover
        self.failover_history: List[Dict[str, Any]] = []

    def generate(
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
                return provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                err = classify_http_error(e, provider=prov_tag, model=getattr(provider, "model", None))
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
                self.failover_history.append({
                    "from": p_name,
                    "to": next_p,
                    "error_class": type(err).__name__,
                    "hint": getattr(err, "hint", ""),
                    "error": redact_secrets(str(err)),
                    "timestamp": time.time(),
                })
                if self.on_failover:
                    try:
                        self.on_failover(p_name, next_p, err)
                    except Exception:
                        pass

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
                err = classify_http_error(e, provider=prov_tag, model=getattr(provider, "model", None))
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
                self.failover_history.append({
                    "from": p_name,
                    "to": next_p,
                    "error_class": type(err).__name__,
                    "hint": getattr(err, "hint", ""),
                    "error": redact_secrets(str(err)),
                    "timestamp": time.time(),
                })
                if self.on_failover:
                    try:
                        self.on_failover(p_name, next_p, err)
                    except Exception:
                        pass

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


def _build_from_pool_entry(entry: LLMConfigEntry, dry_run: bool = False) -> BaseLLMProvider:
    """Build a concrete provider instance from an individual pool configuration entry."""
    p_name = entry.provider.lower().strip()
    key = entry.api_key or os.getenv(f"{p_name.upper()}_API_KEY") or os.getenv("API_KEY")
    is_dry = dry_run or (os.getenv("OCTOFLOW_DRY_RUN") == "1")

    if p_name in ["gemini", "google"]:
        model = entry.model if entry.model and entry.model != "default" else "gemini-2.0-flash"
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[{"name": entry.name, "provider": entry.provider, "model": model, "reason": "Missing API key"}],
            )
        return GeminiProvider(api_key=key, model=model)
    elif p_name in ["grok", "xai"]:
        model = entry.model if entry.model and entry.model != "default" else "grok-2-1212"
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[{"name": entry.name, "provider": entry.provider, "model": model, "reason": "Missing API key"}],
            )
        return GrokProvider(api_key=key, model=model)
    elif p_name == "deepseek":
        model = entry.model if entry.model and entry.model != "default" else "deepseek-chat"
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[{"name": entry.name, "provider": entry.provider, "model": model, "reason": "Missing API key"}],
            )
        return DeepSeekProvider(api_key=key, model=model)
    elif p_name == "anthropic":
        model = entry.model if entry.model and entry.model != "default" else "claude-3-5-sonnet-20241022"
        if not key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                f"Missing API key for provider '{entry.provider}'. Set {p_name.upper()}_API_KEY or use --dry-run.",
                failures=[{"name": entry.name, "provider": entry.provider, "model": model, "reason": "Missing API key"}],
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
                failures=[{"name": entry.name, "provider": entry.provider, "model": model, "reason": "Missing API key"}],
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
            failures=[{"name": entry.name, "provider": "mock", "model": "mock", "reason": "Mock provider requires --dry-run"}],
        )
    if is_dry:
        return MockLLMProvider()
    raise ProviderExhaustedError(
        f"Unsupported provider backend '{p_name}'.",
        failures=[{"name": entry.name, "provider": p_name, "model": getattr(entry, "model", "unknown"), "reason": "Unsupported provider backend"}],
    )


class CascadePoolLLMProvider(BaseLLMProvider):
    """Multi-URL LLM Cascade with hot-swap token and rate-limit failover.
    
    Users and developers can configure as many or as few LLMs/URLs as they choose.
    If 1 model runs out of tokens or hits a rate limit (429, QuotaExceeded, etc.),
    it dynamically falls back to the next model in the user's configured pool.
    """

    def __init__(
        self,
        entries: List[LLMConfigEntry],
        on_failover: Optional[Callable[[Dict[str, Any]], None]] = None,
        dry_run: bool = False,
    ):
        self.entries = [e for e in sorted(entries, key=lambda x: x.priority) if e.enabled]
        self.on_failover = on_failover
        self.dry_run = dry_run or (os.getenv("OCTOFLOW_DRY_RUN") == "1")
        self.active_index = 0
        self.providers: List[BaseLLMProvider] = []
        self.telemetry: List[Dict[str, Any]] = []

        for e in self.entries:
            try:
                prov = _build_from_pool_entry(e, dry_run=self.dry_run)
                self.providers.append(prov)
                self.telemetry.append({
                    "id": e.id,
                    "name": e.name,
                    "provider": e.provider,
                    "model": e.model,
                    "base_url": e.base_url or "",
                    "status": "STANDBY",
                    "tokens_used": 0,
                    "failover_count": 0,
                    "last_error": None,
                })
            except ProviderExhaustedError as pe:
                self.telemetry.append({
                    "id": e.id,
                    "name": e.name,
                    "provider": e.provider,
                    "model": e.model,
                    "base_url": e.base_url or "",
                    "status": "EXHAUSTED",
                    "tokens_used": 0,
                    "failover_count": 0,
                    "last_error": str(pe),
                })

        if self.telemetry:
            self.telemetry[0]["status"] = "ACTIVE"

    def get_status_summary(self) -> List[Dict[str, Any]]:
        """Return live telemetry snapshot of all configured LLMs in pool."""
        return list(self.telemetry)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
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
            summary = "; ".join(f"{f['provider']}:{f['model']} ({f['reason']})" for f in failures) if failures else "no providers configured in cascade pool"
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

            if (getattr(provider, "is_disabled", False) or t["status"] in ["DISABLED", "EXHAUSTED"]) and attempt_offset < n - 1:
                continue

            t["status"] = "ACTIVE"
            self.active_index = idx

            try:
                resp = provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                t["tokens_used"] += resp.total_tokens
                return resp
            except Exception as e:
                err = classify_http_error(e, provider=t.get("provider", "unknown"), model=t.get("model"))
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
                    except Exception:
                        pass

        if self.dry_run:
            import logging
            logging.getLogger("octoflow").warning(f"All configured LLM providers in cascade pool exhausted ({last_err}). Falling back to cephalopod neural heuristic inference.")
            return MockLLMProvider().generate(prompt, system_prompt, temperature, max_tokens)

        failures = [
            {
                "name": t.get("name", "unknown"),
                "provider": t.get("provider", "unknown"),
                "model": t.get("model", "unknown"),
                "error_class": t.get("error_class", type(last_err).__name__ if last_err else "ProviderError"),
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
        return await asyncio.to_thread(self.generate, prompt, system_prompt, temperature, max_tokens)


def _build_single_provider(provider_name: str, config: OctoFlowConfig, tier: Optional[str] = None, dry_run: bool = False) -> BaseLLMProvider:
    """Helper to instantiate an individual provider backend."""
    p_name = provider_name.lower().strip()
    is_dry = dry_run or getattr(config, "dry_run", False) or (os.getenv("OCTOFLOW_DRY_RUN") == "1")

    if p_name == "mock":
        if is_dry:
            return MockLLMProvider()
        raise ProviderExhaustedError(
            "Mock LLM provider requested without --dry-run. Pass --dry-run or configure a real provider.",
            failures=[{"provider": "mock", "model": "mock", "reason": "mock provider requires --dry-run"}],
        )

    elif p_name == "anthropic":
        api_key = config.anthropic_api_key or config.api_key or os.getenv("ANTHROPIC_API_KEY")
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
                failures=[{"provider": "anthropic", "model": model, "reason": "missing ANTHROPIC_API_KEY"}],
            )
        return AnthropicProvider(api_key=api_key, model=model)

    elif p_name == "openai":
        api_key = config.openai_api_key or config.api_key or os.getenv("OPENAI_API_KEY")
        if tier == "fast":
            model = config.fast_model or "gpt-4o-mini"
        elif tier == "frontier":
            model = config.frontier_model or "o3-mini"
        else:
            model = config.model_name if ("gpt" in config.model_name or "o3" in config.model_name or "o1" in config.model_name) else "gpt-4o"
        base_url = config.base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "OpenAI provider misconfigured: missing OPENAI_API_KEY",
                failures=[{"provider": "openai", "model": model, "reason": "missing OPENAI_API_KEY"}],
            )
        return OpenAIProvider(api_key=api_key, model=model, base_url=base_url)

    elif p_name in ["gemini", "google"]:
        api_key = config.gemini_api_key or config.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        model = config.model_name if "gemini" in config.model_name else "gemini-2.0-flash"
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "Gemini provider misconfigured: missing GEMINI_API_KEY",
                failures=[{"provider": "gemini", "model": model, "reason": "missing GEMINI_API_KEY"}],
            )
        return GeminiProvider(api_key=api_key, model=model)

    elif p_name in ["grok", "xai"]:
        api_key = config.grok_api_key or config.api_key or os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        model = config.model_name if "grok" in config.model_name else "grok-2-1212"
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "Grok provider misconfigured: missing GROK_API_KEY",
                failures=[{"provider": "grok", "model": model, "reason": "missing GROK_API_KEY"}],
            )
        return GrokProvider(api_key=api_key, model=model)

    elif p_name in ["deepseek"]:
        api_key = config.deepseek_api_key or config.api_key or os.getenv("DEEPSEEK_API_KEY")
        model = config.model_name if "deepseek" in config.model_name else "deepseek-chat"
        if not api_key:
            if is_dry:
                return MockLLMProvider()
            raise ProviderExhaustedError(
                "DeepSeek provider misconfigured: missing DEEPSEEK_API_KEY",
                failures=[{"provider": "deepseek", "model": model, "reason": "missing DEEPSEEK_API_KEY"}],
            )
        return DeepSeekProvider(api_key=api_key, model=model)

    elif p_name == "ollama":
        url = config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if tier == "fast":
            model = config.fast_model or "qwen2.5-coder:1.5b"
        elif tier == "frontier":
            model = config.frontier_model or "deepseek-coder-v2:16b"
        else:
            model = config.model_name if ("coder" in config.model_name or "llama" in config.model_name) else "qwen2.5-coder:7b"
        return OllamaProvider(base_url=url, model=model)

    if is_dry:
        return MockLLMProvider()
    raise ProviderExhaustedError(
        f"Unsupported provider backend '{provider_name}'",
        failures=[{"provider": provider_name, "reason": "unsupported provider backend"}],
    )


def get_llm_provider(config: OctoFlowConfig, tier: Optional[str] = None, dry_run: bool = False) -> BaseLLMProvider:
    """Factory creating configured LLM provider, optionally tailored by cognitive tier ('frontier', 'balanced', 'fast').
    
    Supports dynamic multi-URL cascade pools with auto-failover, heterogeneous routing, and fallbacks.
    """
    is_dry = dry_run or getattr(config, "dry_run", False) or (os.getenv("OCTOFLOW_DRY_RUN") == "1")
    force_live = (os.getenv("OCTOFLOW_FORCE_LIVE") == "1") or getattr(config, "force_live", False)
    is_testing = not force_live and (("PYTEST_CURRENT_TEST" in os.environ) or ("pytest" in sys.modules) or (os.getenv("OCTOFLOW_TESTING") == "1"))

    # 1. Determine target provider for requested cognitive tier
    provider_name = config.model_provider.lower()
    if tier == "frontier" and config.frontier_provider:
        provider_name = config.frontier_provider.lower()
    elif tier == "fast" and config.fast_provider:
        provider_name = config.fast_provider.lower()

    if provider_name == "mock":
        if is_dry or is_testing:
            return MockLLMProvider()
        raise ProviderExhaustedError(
            "Mock LLM provider requested without --dry-run. Pass --dry-run or configure a real provider.",
            failures=[{"provider": "mock", "model": "mock", "reason": "mock provider requires --dry-run"}],
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
        fallbacks: List[BaseLLMProvider] = []
        fb_names = getattr(config, "fallback_providers", ["openai", "ollama"])
        for fb_name in fb_names:
            if fb_name.lower() != provider_name:
                try:
                    fallbacks.append(_build_single_provider(fb_name, config, tier=tier, dry_run=is_dry))
                except ProviderExhaustedError:
                    pass

        if fallbacks:
            return FailoverLLMProvider(primary=primary, fallbacks=fallbacks)

    return primary


