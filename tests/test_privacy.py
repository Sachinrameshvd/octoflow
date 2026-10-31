"""Tests for outbound prompt redaction and privacy guard (P5.4)."""

from unittest.mock import MagicMock, patch

import pytest

from octoflow.provider import (
    AnthropicProvider,
    MockLLMProvider,
    OllamaProvider,
    OpenAIProvider,
)
from octoflow.redactor import redact_outbound_text


def test_redact_outbound_text_secrets():
    """Verify core secret types are redacted to stable placeholders."""
    raw_prompt = (
        "Here are our keys:\n"
        "OpenAI: sk-proj-123456789012345678901234567890\n"
        "Anthropic: sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890\n"
        "AWS: AKIAIOSFODNN7EXAMPLE and secret wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
        "GitHub: ghp_123456789012345678901234567890123456\n"
        "Slack: xoxb-123456789012-123456789012-abcdefghijklmnopqrstuvwx\n"
        "Bearer: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDcSemACt8x4iTMCda8Yhe3iZaWbvV5XKSTbuAn0M\n"
    )

    clean_text, count = redact_outbound_text(raw_prompt)
    assert count >= 6
    assert "[REDACTED:OPENAI_API_KEY]" in clean_text
    assert "[REDACTED:ANTHROPIC_API_KEY]" in clean_text
    assert "[REDACTED:AWS_ACCESS_KEY]" in clean_text
    assert "[REDACTED:GITHUB_TOKEN]" in clean_text
    assert "[REDACTED:SLACK_TOKEN]" in clean_text
    assert "[REDACTED:BEARER_TOKEN]" in clean_text

    # None of the raw secret substrings should remain
    assert "sk-proj-123456789012345678901234567890" not in clean_text
    assert "AKIAIOSFODNN7EXAMPLE" not in clean_text
    assert "ghp_123456789012345678901234567890123456" not in clean_text


def test_redact_outbound_text_preserves_code_without_false_positives():
    """Verify that normal programming code and local IPs are not corrupted."""
    code_snippet = """
    import httpx

    def connect_service():
        host = "127.0.0.1"
        port = 8088
        url = f"http://{host}:{port}/api/health"
        timeout = 30.0
        retry_count = 3
        # Regex pattern for UUID
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        return httpx.get(url, timeout=timeout)
    """

    clean_text, count = redact_outbound_text(code_snippet)
    assert count == 0
    assert clean_text == code_snippet


def test_cloud_provider_redacts_outbound_prompt():
    """Anthropic and OpenAI providers must scrub secrets before dispatching requests."""
    fake_api_key = "sk-ant-test-key-000000000000000000"
    provider = AnthropicProvider(api_key=fake_api_key, redact_outbound=True)

    secret_prompt = "Analyze this config: AWS_KEY=AKIAIOSFODNN7EXAMPLE"
    secret_sys = "You are a reviewer with token: ghp_123456789012345678901234567890123456"

    clean_p, clean_s = provider.sanitize_outbound_prompt(secret_prompt, secret_sys)
    assert "[REDACTED:AWS_ACCESS_KEY]" in clean_p
    assert "AKIAIOSFODNN7EXAMPLE" not in clean_p
    assert "[REDACTED:GITHUB_TOKEN]" in clean_s
    assert "ghp_123456789012345678901234567890123456" not in clean_s
    assert provider.get_redactions_count() == 2


def test_local_provider_skips_redaction():
    """Local providers (Ollama, Mock) must skip redaction to keep prompts unmodified."""
    ollama = OllamaProvider(base_url="http://localhost:11434")
    mock = MockLLMProvider()

    assert ollama.is_local() is True
    assert mock.is_local() is True

    secret_prompt = "Local debugging: AKIAIOSFODNN7EXAMPLE"
    clean_p, _ = ollama.sanitize_outbound_prompt(secret_prompt)
    assert clean_p == secret_prompt
    assert ollama.get_redactions_count() == 0

    clean_p2, _ = mock.sanitize_outbound_prompt(secret_prompt)
    assert clean_p2 == secret_prompt
    assert mock.get_redactions_count() == 0


def test_cloud_provider_skips_redaction_when_disabled():
    """When redact_outbound is False, prompts are not scrubbed."""
    provider = OpenAIProvider(api_key="sk-openai-key-test-000000000000", redact_outbound=False)
    secret_prompt = "Skip redaction: AKIAIOSFODNN7EXAMPLE"

    clean_p, _ = provider.sanitize_outbound_prompt(secret_prompt)
    assert clean_p == secret_prompt
    assert provider.get_redactions_count() == 0

