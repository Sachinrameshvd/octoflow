"""Targeted unit tests for octoflow/settings.py to exceed 80% line coverage."""

import json
from pathlib import Path

import pytest
from octoflow.settings import (
    ConfigurationError,
    Settings,
    _apply_cli_overrides,
    _warn_extras_once,
    get_default_config_dir,
    get_default_config_path,
    load_settings,
    mask_secret_value,
    save_settings,
    set_config_value,
)
from pydantic import SecretStr


@pytest.mark.unit
def test_default_config_dir_and_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    cfg_dir = get_default_config_dir()
    assert cfg_dir.exists()
    assert cfg_dir.name == ".octoflow"

    cfg_path = get_default_config_path()
    assert cfg_path.name == "config.json"
    assert cfg_path.parent == cfg_dir


@pytest.mark.unit
def test_mask_secret_value_branches():
    assert mask_secret_value(None) == ""
    assert mask_secret_value("") == ""
    assert mask_secret_value("abc") == "****"
    assert mask_secret_value("1234") == "****"
    assert mask_secret_value("sk-123456789") == "sk-****"
    assert mask_secret_value(SecretStr("my-secret-key")) == "my-****"


@pytest.mark.unit
def test_settings_providers_as_list():
    raw_config = {
        "providers": [
            {"provider": "openai", "api_key": "test-key-1"},
            {"name": "anthropic", "provider": "anthropic", "api_key": "test-key-2"},
        ]
    }
    s = Settings.model_validate(raw_config)
    assert "openai" in s.providers
    assert "anthropic" in s.providers


@pytest.mark.unit
def test_env_overrides_ui_and_server(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOFLOW_THEME", "matrix")
    monkeypatch.setenv("OCTOFLOW_ANIMATION", "1")
    monkeypatch.setenv("OCTOFLOW_COLOR", "true")
    monkeypatch.setenv("OCTOFLOW_ASCII", "yes")
    monkeypatch.setenv("OCTOFLOW_HOST", "127.0.0.1")
    monkeypatch.setenv("OCTOFLOW_WS_PORT", "9191")
    monkeypatch.setenv("OCTOFLOW_HTTP_PORT", "9192")
    monkeypatch.setenv("OCTOFLOW_WEBHOOK_URL", "https://hooks.slack.com/services/xyz")

    s = load_settings(cfg_path=tmp_path / "nonexistent.json")
    assert s.ui.theme == "matrix"
    assert s.ui.animation is True
    assert s.ui.color is True
    assert s.ui.ascii is True
    assert s.server.host == "127.0.0.1"
    assert s.server.ws_port == 9191
    assert s.server.http_port == 9192
    assert s.webhook_url == "https://hooks.slack.com/services/xyz"


@pytest.mark.unit
def test_env_overrides_invalid_integers(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOFLOW_WS_PORT", "not-an-int")
    with pytest.raises(ConfigurationError, match="Invalid integer for OCTOFLOW_WS_PORT"):
        load_settings(cfg_path=tmp_path / "nonexistent.json")

    monkeypatch.delenv("OCTOFLOW_WS_PORT")
    monkeypatch.setenv("OCTOFLOW_HTTP_PORT", "not-an-int")
    with pytest.raises(ConfigurationError, match="Invalid integer for OCTOFLOW_HTTP_PORT"):
        load_settings(cfg_path=tmp_path / "nonexistent.json")

    monkeypatch.delenv("OCTOFLOW_HTTP_PORT")
    monkeypatch.setenv("OCTOFLOW_SCALE", "not-an-int")
    with pytest.raises(ConfigurationError, match="Invalid integer for OCTOFLOW_SCALE"):
        load_settings(cfg_path=tmp_path / "nonexistent.json")


@pytest.mark.unit
def test_env_overrides_generic_prefix(monkeypatch, tmp_path):
    monkeypatch.setenv("OCTOFLOW_DEFAULTS_DEFAULT_SCALE", "3")
    monkeypatch.setenv("OCTOFLOW_DEFAULTS_ENCODER_BACKEND", "torch")
    monkeypatch.setenv("OCTOFLOW_UI_ANIMATION", "false")
    s = load_settings(cfg_path=tmp_path / "nonexistent.json")
    assert s.defaults.default_scale == 3
    assert s.defaults.encoder_backend == "torch"
    assert s.ui.animation is False


@pytest.mark.unit
def test_cli_overrides_nested_dict():
    data = {"server": {"host": "0.0.0.0", "ws_port": 8765}}
    _apply_cli_overrides(data, {"server": {"ws_port": 9999}})
    assert data["server"]["ws_port"] == 9999
    assert data["server"]["host"] == "0.0.0.0"


@pytest.mark.unit
def test_corrupted_config_file_raises_error(tmp_path):
    bad_cfg = tmp_path / "bad_config.json"
    bad_cfg.write_text("{ this is broken json }", encoding="utf-8")

    with pytest.raises(
        ConfigurationError,
        match="(Failed to load config file|Failed to read existing configuration)",
    ):
        load_settings(cfg_path=bad_cfg)


@pytest.mark.unit
def test_validation_error_hints(tmp_path):
    cfg_file = tmp_path / "cfg.json"

    # Invalid port
    cfg_file.write_text(json.dumps({"server": {"ws_port": 999999}}), encoding="utf-8")
    with pytest.raises(ConfigurationError) as exc_port:
        load_settings(cfg_path=cfg_file)
    assert exc_port.value.hint == "Ports must be between 1 and 65535"

    # Invalid provider
    cfg_file.write_text(
        json.dumps({"defaults": {"default_provider": "unknown_ai"}}), encoding="utf-8"
    )
    with pytest.raises(ConfigurationError) as exc_prov:
        load_settings(cfg_path=cfg_file)
    assert "Allowed providers" in (exc_prov.value.hint or "")

    # Invalid scale
    cfg_file.write_text(json.dumps({"defaults": {"default_scale": 0}}), encoding="utf-8")
    with pytest.raises(ConfigurationError) as exc_scale:
        load_settings(cfg_path=cfg_file)
    assert exc_scale.value.hint == "Scale must be at least 1 octopus"


@pytest.mark.unit
def test_save_and_set_config_value(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    s = Settings()
    s.ui.theme = "cyberpunk"
    save_settings(s, cfg_path=cfg_file)
    assert cfg_file.exists()

    # set_config_value with boolean, int, string
    s_updated = set_config_value("ui.animation", "false", cfg_path=cfg_file)
    assert s_updated.ui.animation is False

    s_updated = set_config_value("budget.max_tokens", "500000", cfg_path=cfg_file)
    assert s_updated.budget.max_tokens == 500000

    s_updated = set_config_value("ui.theme", "minimal", cfg_path=cfg_file)
    assert s_updated.ui.theme == "minimal"


@pytest.mark.unit
def test_extras_warning_printed(capsys):
    _warn_extras_once({"unrecognized_key_1": "val", "unrecognized_key_2": 42})
    captured = capsys.readouterr()
    assert "Warning: Preserving unknown configuration keys under extras" in captured.err
