"""Tests for API key resolution order and keyring integration (P5.4).

Resolution hierarchy:
1. Environment variables (e.g. ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY)
2. OS Keyring (if octoflow[keyring] installed and entry exists)
3. Config file (~/.octoflow/config.json)
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from octoflow.config import OctoFlowConfig
from octoflow.keyring_store import (
    KEYRING_SERVICE_NAME,
    delete_keyring_key,
    get_config_key,
    get_env_key,
    get_keyring_key,
    is_keyring_available,
    resolve_api_key,
    set_keyring_key,
)


def test_env_var_takes_highest_precedence(monkeypatch):
    """Environment variable must override both keyring and config file."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env-1234567890123456")
    fake_config = {"anthropic_api_key": "sk-ant-from-config-1234567890123456"}

    with patch("octoflow.keyring_store.get_keyring_key", return_value="sk-ant-from-keyring-12345"):
        key, source = resolve_api_key("anthropic", config=fake_config)

    assert key == "sk-ant-from-env-1234567890123456"
    assert source == "env"


def test_keyring_takes_precedence_over_config(monkeypatch):
    """When env var is unset, keyring must override config file."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    fake_config = {"anthropic_api_key": "sk-ant-from-config-1234567890123456"}

    with patch("octoflow.keyring_store.get_keyring_key", return_value="sk-ant-from-keyring-99999"):
        key, source = resolve_api_key("anthropic", config=fake_config)

    assert key == "sk-ant-from-keyring-99999"
    assert source == "keyring"


def test_config_fallback_when_env_and_keyring_unset(monkeypatch):
    """When env var and keyring are unset, fallback to config file."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake_config = {"openai_api_key": "sk-proj-from-config-1234567890123456"}

    with patch("octoflow.keyring_store.get_keyring_key", return_value=None):
        key, source = resolve_api_key("openai", config=fake_config)

    assert key == "sk-proj-from-config-1234567890123456"
    assert source == "config"


def test_gemini_env_vars_fallback(monkeypatch):
    """GEMINI_API_KEY or GOOGLE_API_KEY are resolved properly."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSyGoogleKey12345678901234567890")

    key, source = resolve_api_key("gemini", config={})
    assert key == "AIzaSyGoogleKey12345678901234567890"
    assert source == "env"


def test_unconfigured_provider_returns_none(monkeypatch):
    """Unconfigured provider returns (None, 'none')."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with patch("octoflow.keyring_store.get_keyring_key", return_value=None):
        key, source = resolve_api_key("deepseek", config={})

    assert key is None
    assert source == "none"


def test_octoflow_config_post_init_respects_resolution_order(monkeypatch):
    """OctoFlowConfig post_init uses resolve_api_key to populate keys."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-postinit-test-12345678")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with patch("octoflow.config.load_secure_config", return_value={"openai_api_key": "sk-proj-cfg-test"}):
        with patch("octoflow.keyring_store.get_keyring_key", return_value=None):
            cfg = OctoFlowConfig(model_provider="anthropic")

    assert cfg.anthropic_api_key == "sk-ant-env-postinit-test-12345678"
    assert cfg.openai_api_key == "sk-proj-cfg-test"
    assert cfg.api_key == "sk-ant-env-postinit-test-12345678"


def test_keyring_functions_handle_missing_dependency():
    """When keyring module is absent, helper functions return gracefully without errors."""
    with patch.dict("sys.modules", {"keyring": None}):
        assert is_keyring_available() is False
        assert get_keyring_key("anthropic") is None
        assert set_keyring_key("anthropic", "test-key") is False
        assert delete_keyring_key("anthropic") is False

