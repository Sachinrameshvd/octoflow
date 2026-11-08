"""Minimal OpenAI-compatible custom LLM provider for LM Studio and vLLM.

Implements the OctoFlow BaseLLMProvider contract in ~60 lines.
"""

from __future__ import annotations

from typing import Any, Callable
import httpx

from octoflow.provider import (
    DEFAULT_CLOUD_TIMEOUT,
    BaseLLMProvider,
    LLMResponse,
    estimate_tokens_from_chars,
    execute_with_retry,
)


class LMStudioProvider(BaseLLMProvider):
    """Local OpenAI-compatible provider for LM Studio and vLLM inference servers."""

    provider_name: str = "lmstudio"
    supports_tools: bool = True

    def __init__(
        self,
        base_url: str | None = None,
        model: str = "local-model",
        api_key: str | None = None,
        timeout: httpx.Timeout | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        asleep_fn: Callable[[float], Any] | None = None,
        transport: httpx.BaseTransport | None = None,
        **kwargs: Any,
    ):
        raw_url = base_url or "http://localhost:1234/v1"
        self.base_url = (
            raw_url.rstrip("/")
            if raw_url.endswith("/chat/completions")
            else f"{raw_url.rstrip('/')}/chat/completions"
        )
        self.model = model
        self.api_key = api_key or "lm-studio"
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

        resp = LLMResponse(
            content=content,
            tokens_prompt=in_toks,
            tokens_completion=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_dollars=0.0,  # Local execution
            estimated=estimated,
        )
        self.record_usage(resp)
        return resp

