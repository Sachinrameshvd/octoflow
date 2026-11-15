"""Tests for Anthropic Claude 3.5 Sonnet Ephemeral Prompt Caching & Tool Use.

Verifies:
- Prompt caching beta header 'anthropic-beta: prompt-caching-2024-07-31'.
- System prompt formatted as block with cache_control: {'type': 'ephemeral'}.
- Accurate extraction of cache_read_input_tokens and cache_creation_input_tokens.
- 90% discount pricing calculation for cache read tokens ($0.30/M vs $3.00/M).
- Native tool calling extraction from Anthropic tool_use blocks.
- Full asynchronous (agenerate) parity.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from octoflow.provider import AnthropicProvider, LLMResponse


def test_anthropic_prompt_caching_payload_and_header() -> None:
    """Verify AnthropicProvider sends beta header and ephemeral cache_control block."""
    captured_requests: list[httpx.Request] = []

    def mock_transport(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        response_body = {
            "id": "msg_caching_test_01",
            "type": "message",
            "role": "assistant",
            "model": "claude-3-5-sonnet-20241022",
            "content": [{"type": "text", "text": "Cached response completed."}],
            "usage": {
                "input_tokens": 150,
                "output_tokens": 50,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 2048,
            },
        }
        return httpx.Response(200, json=response_body, request=request)

    transport = httpx.MockTransport(mock_transport)
    provider = AnthropicProvider(
        api_key="sk-ant-api03-validtestkey1234567890",
        transport=transport,
        enable_prompt_caching=True,
    )

    system_prompt = "You are Arm 2 (Backend API specialist). Always adhere to Clean Architecture."
    user_prompt = "Implement rate limiter handler"

    response = provider.generate(prompt=user_prompt, system_prompt=system_prompt)

    assert len(captured_requests) == 1
    req = captured_requests[0]

    # Verify headers
    assert req.headers["anthropic-beta"] == "prompt-caching-2024-07-31"
    assert req.headers["anthropic-version"] == "2023-06-01"
    assert req.headers["content-type"] == "application/json"

    # Verify body payload
    body = json.loads(req.content.decode("utf-8"))
    assert "system" in body
    assert isinstance(body["system"], list)
    assert len(body["system"]) == 1
    assert body["system"][0]["type"] == "text"
    assert body["system"][0]["text"] == system_prompt
    assert body["system"][0]["cache_control"] == {"type": "ephemeral"}

    # Verify LLMResponse cache tokens
    assert response.tokens_cached_read == 2048
    assert response.tokens_cached_create == 0
    assert response.tokens_prompt == 150 + 2048  # Total prompt tokens
    assert response.tokens_completion == 50
    assert response.content == "Cached response completed."

    # Verify Truthful Discount Pricing:
    # in_toks (150) * $0.000003 = $0.000450
    # cache_read (2048) * $0.0000003 = $0.0006144  <-- 90% discount!
    # out_toks (50) * $0.000015 = $0.000750
    # total expected = 0.000450 + 0.0006144 + 0.000750 = 0.001814
    expected_cost = round((150 * 0.000003) + (2048 * 0.0000003) + (50 * 0.000015), 6)
    assert response.estimated_cost_dollars == expected_cost


def test_anthropic_native_tool_use_extraction() -> None:
    """Verify AnthropicProvider extracts native tool_use blocks into tool_calls."""
    def mock_transport(request: httpx.Request) -> httpx.Response:
        response_body = {
            "id": "msg_tool_test_02",
            "type": "message",
            "role": "assistant",
            "model": "claude-3-5-sonnet-20241022",
            "content": [
                {"type": "text", "text": "Checking the rate limiter file."},
                {
                    "type": "tool_use",
                    "id": "toolu_01A8BcDeF",
                    "name": "read_file",
                    "input": {"path": "limiter.py", "max_lines": 50},
                },
            ],
            "usage": {
                "input_tokens": 300,
                "output_tokens": 80,
                "cache_creation_input_tokens": 1200,
                "cache_read_input_tokens": 0,
            },
        }
        return httpx.Response(200, json=response_body, request=request)

    transport = httpx.MockTransport(mock_transport)
    provider = AnthropicProvider(
        api_key="sk-ant-api03-validtestkey1234567890",
        transport=transport,
    )

    tools = [
        {
            "name": "read_file",
            "description": "Read file contents",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        }
    ]

    response = provider.generate("Inspect limiter.py", tools=tools)

    assert response.content == "Checking the rate limiter file."
    assert len(response.tool_calls) == 1
    tc = response.tool_calls[0]
    assert tc["id"] == "toolu_01A8BcDeF"
    assert tc["name"] == "read_file"
    assert tc["arguments"] == {"path": "limiter.py", "max_lines": 50}
    assert response.tokens_cached_create == 1200


@pytest.mark.anyio
async def test_anthropic_async_agenerate_prompt_caching() -> None:
    """Verify asynchronous agenerate supports prompt caching identically."""
    def mock_transport(request: httpx.Request) -> httpx.Response:
        response_body = {
            "id": "msg_async_03",
            "type": "message",
            "role": "assistant",
            "model": "claude-3-5-sonnet-20241022",
            "content": [{"type": "text", "text": "Async cached output."}],
            "usage": {
                "input_tokens": 80,
                "output_tokens": 25,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 3000,
            },
        }
        return httpx.Response(200, json=response_body, request=request)

    transport = httpx.MockTransport(mock_transport)
    provider = AnthropicProvider(
        api_key="sk-ant-api03-validtestkey1234567890",
        transport=transport,
    )

    response = await provider.agenerate(
        prompt="Async task",
        system_prompt="Cached system instructions",
    )

    assert response.content == "Async cached output."
    assert response.tokens_cached_read == 3000
    assert response.tokens_prompt == 80 + 3000
    assert response.tokens_completion == 25
