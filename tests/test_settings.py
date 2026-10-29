"""Tests for OctoFlow typed, versioned, validated configuration settings (P2.3).

Covers:
- Precedence matrix (defaults < file < env < cli)
- Automatic migration from legacy schema with timestamped backup
- Atomic-write crash safety (interruption between temp write and os.replace)
- Strict 0600 file permissions and 0700 directory permissions
- Secret masking in serialization and 'config show'
- Validation errors with field paths, human hints, and exit code 3 (no traceback)
- Subcommands: config path, show, set, validate, migrate (--down)
"""

from __future__ import annotations
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict
import pytest
from typer.testing import CliRunner
from pydantic import SecretStr, ValidationError

pytestmark = pytest.mark.unit

from octoflow.settings import (
    CURRENT_SCHEMA_VERSION,
    ConfigurationError,
    DefaultsSettings,
    ProviderSettings,
    ServerSettings,
    Settings,
    UISettings,
    atomic_write_config,
    create_config_backup,
    load_settings,
    mask_secret_value,
    migrate_config_if_needed,
    restore_config_backup,
    save_settings,
    set_config_value,
)
from octoflow.cli import app


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Fixture providing an isolated temporary ~/.octoflow directory."""
    cfg_dir = tmp_path / ".octoflow"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


@pytest.fixture
def temp_config_file(temp_config_dir: Path) -> Path:
    """Fixture providing an isolated temporary config.json path."""
    return temp_config_dir / "config.json"


@pytest.fixture
def cli_runner() -> CliRunner:
    """Typer CLI runner for testing config subcommands."""
    return CliRunner()


# ---------------------------------------------------------------------------
# 1. Pydantic Models & Field Validation Tests
# ---------------------------------------------------------------------------

def test_defaults_settings_validation():
    """Verify default values and constraints for DefaultsSettings."""
    defaults = DefaultsSettings()
    assert defaults.default_provider == "anthropic"
    assert defaults.default_scale == 1

    # Valid custom provider
    d2 = DefaultsSettings(default_provider="openai", default_scale=4)
    assert d2.default_provider == "openai"
    assert d2.default_scale == 4

    # Invalid scale < 1
    with pytest.raises(ValidationError) as exc:
        DefaultsSettings(default_scale=0)
    assert "default_scale" in str(exc.value)

    # Unknown provider
    with pytest.raises(ValidationError) as exc:
        DefaultsSettings(default_provider="invalid_ai_xyz")
    assert "default_provider" in str(exc.value)
    assert "Allowed providers" in str(exc.value)


def test_server_settings_port_validation():
    """Verify port constraints on ServerSettings."""
    srv = ServerSettings()
    assert srv.ws_port == 8088
    assert srv.http_port == 8089
    assert srv.host == "127.0.0.1"

    # Out of range ports
    with pytest.raises(ValidationError) as exc:
        ServerSettings(ws_port=99999)
    assert "ws_port" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ServerSettings(http_port=0)
    assert "http_port" in str(exc.value)


def test_provider_settings_and_secret_str():
    """Verify ProviderSettings with SecretStr and validation."""
    p = ProviderSettings(name="anthropic", api_key=SecretStr("sk-ant-testkey12345"))
    assert p.name == "anthropic"
    assert p.api_key.get_secret_value() == "sk-ant-testkey12345"
    assert "sk-ant-testkey12345" not in repr(p.api_key)

    # Invalid timeout
    with pytest.raises(ValidationError) as exc:
        ProviderSettings(name="openai", timeout=-5.0)
    assert "timeout" in str(exc.value)

    # Unknown provider
    with pytest.raises(ValidationError) as exc:
        ProviderSettings(name="unknown_core")
    assert "name" in str(exc.value)


# ---------------------------------------------------------------------------
# 2. Secret Masking Tests
# ---------------------------------------------------------------------------

def test_mask_secret_value_function():
    """Verify secret masking behavior."""
    assert mask_secret_value(None) == ""
    assert mask_secret_value("") == ""
    assert mask_secret_value("abc") == "****"
    assert mask_secret_value("sk-ant-123456789") == "sk-****"
    assert mask_secret_value(SecretStr("AIzaSySecret999")) == "AIz****"


def test_settings_to_dict_masking():
    """Verify settings.to_dict(mask_secrets=True) conceals all secret keys."""
    settings = Settings(
        providers={
            "anthropic": ProviderSettings(
                name="anthropic",
                api_key=SecretStr("sk-ant-supersecret12345"),
            ),
            "gemini": ProviderSettings(
                name="gemini",
                api_key=SecretStr("AIzaSyMySecretKey"),
            ),
        },
        extras={"custom_api_key": "custom-secret-value-123"},
    )

    unmasked = settings.to_dict(mask_secrets=False)
    assert unmasked["providers"]["anthropic"]["api_key"] == "sk-ant-supersecret12345"
    assert unmasked["providers"]["gemini"]["api_key"] == "AIzaSyMySecretKey"
    assert unmasked["extras"]["custom_api_key"] == "custom-secret-value-123"

    masked = settings.to_dict(mask_secrets=True)
    assert "supersecret" not in json.dumps(masked)
    assert masked["providers"]["anthropic"]["api_key"].startswith("sk-")
    assert masked["providers"]["anthropic"]["api_key"].endswith("****")
    assert masked["providers"]["gemini"]["api_key"].startswith("AIz")
    assert masked["providers"]["gemini"]["api_key"].endswith("****")
    assert masked["extras"]["custom_api_key"] == "cus****"


# ---------------------------------------------------------------------------
# 3. Precedence Matrix Tests
# ---------------------------------------------------------------------------

def test_precedence_defaults(temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Level 1: When no config file and no env exist, default settings apply."""
    monkeypatch.delenv("OCTOFLOW_THEME", raising=False)
    monkeypatch.delenv("OCTOFLOW_WS_PORT", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    settings = load_settings(cfg_path=temp_config_file)
    assert settings.schema_version == CURRENT_SCHEMA_VERSION
    assert settings.ui.theme == "catppuccin"
    assert settings.server.ws_port == 8088
    assert settings.defaults.default_provider == "anthropic"


def test_precedence_file_overrides_defaults(temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Level 2: Config file overrides defaults."""
    monkeypatch.delenv("OCTOFLOW_THEME", raising=False)
    monkeypatch.delenv("OCTOFLOW_WS_PORT", raising=False)

    file_data = {
        "schema_version": 1,
        "ui": {"theme": "dracula"},
        "server": {"ws_port": 8099},
        "defaults": {"default_provider": "openai"},
    }
    atomic_write_config(temp_config_file, json.dumps(file_data))

    settings = load_settings(cfg_path=temp_config_file)
    assert settings.ui.theme == "dracula"
    assert settings.server.ws_port == 8099
    assert settings.defaults.default_provider == "openai"


def test_precedence_env_overrides_file(temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Level 3: Environment variables override file and defaults."""
    file_data = {
        "schema_version": 1,
        "ui": {"theme": "dracula"},
        "server": {"ws_port": 8099},
        "defaults": {"default_provider": "openai"},
    }
    atomic_write_config(temp_config_file, json.dumps(file_data))

    monkeypatch.setenv("OCTOFLOW_THEME", "tokyo-night")
    monkeypatch.setenv("OCTOFLOW_WS_PORT", "9010")
    monkeypatch.setenv("OCTOFLOW_DEFAULT_PROVIDER", "gemini")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")

    settings = load_settings(cfg_path=temp_config_file)
    assert settings.ui.theme == "tokyo-night"
    assert settings.server.ws_port == 9010
    assert settings.defaults.default_provider == "gemini"
    assert "anthropic" in settings.providers
    assert settings.providers["anthropic"].api_key.get_secret_value() == "sk-ant-from-env"


def test_precedence_cli_overrides_env_and_file(temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Level 4: CLI overrides beat environment variables, file, and defaults."""
    file_data = {
        "schema_version": 1,
        "ui": {"theme": "dracula"},
        "server": {"ws_port": 8099},
    }
    atomic_write_config(temp_config_file, json.dumps(file_data))

    monkeypatch.setenv("OCTOFLOW_THEME", "tokyo-night")
    monkeypatch.setenv("OCTOFLOW_WS_PORT", "9010")

    cli_overrides = {
        "ui.theme": "abyssal",
        "server.ws_port": 9999,
        "defaults.default_provider": "ollama",
    }
    settings = load_settings(cli_overrides=cli_overrides, cfg_path=temp_config_file)
    assert settings.ui.theme == "abyssal"
    assert settings.server.ws_port == 9999
    assert settings.defaults.default_provider == "ollama"


# ---------------------------------------------------------------------------
# 4. Migration & Backup Tests
# ---------------------------------------------------------------------------

def test_migration_of_legacy_config_file(temp_config_file: Path):
    """Verify legacy flat config.json is backed up and migrated to schema_version 1."""
    legacy_payload = {
        "default_theme": "tokyo-night",
        "anthropic_api_key": "sk-ant-legacy-key-12345",
        "openai_api_key": "sk-legacy-openai",
        "default_model": "ollama",
        "ollama_base_url": "http://localhost:11434",
        "telemetry_port": 8095,
        "webhook_url": "https://hooks.slack.com/services/T00/B00/X00",
        "unknown_legacy_flag": "preserve_me",
    }
    temp_config_file.write_text(json.dumps(legacy_payload), encoding="utf-8")
    temp_config_file.chmod(0o600)

    migrated, bak_path = migrate_config_if_needed(temp_config_file)
    assert migrated is True
    assert bak_path is not None
    assert bak_path.exists()
    assert (bak_path.stat().st_mode & 0o777) == 0o600

    # Verify backup contains exact original content
    bak_content = json.loads(bak_path.read_text(encoding="utf-8"))
    assert bak_content == legacy_payload

    # Verify migrated file content structure
    migrated_content = json.loads(temp_config_file.read_text(encoding="utf-8"))
    assert migrated_content["schema_version"] == 1
    assert migrated_content["ui"]["theme"] == "tokyo-night"
    assert migrated_content["server"]["ws_port"] == 8095
    assert migrated_content["defaults"]["default_provider"] == "ollama"
    assert migrated_content["providers"]["anthropic"]["api_key"] == "sk-ant-legacy-key-12345"
    assert migrated_content["providers"]["openai"]["api_key"] == "sk-legacy-openai"
    assert migrated_content["providers"]["ollama"]["base_url"] == "http://localhost:11434"
    assert migrated_content["webhook_url"] == "https://hooks.slack.com/services/T00/B00/X00"
    assert migrated_content["extras"]["unknown_legacy_flag"] == "preserve_me"

    # Verify loading the migrated file works cleanly
    settings = load_settings(cfg_path=temp_config_file)
    assert settings.ui.theme == "tokyo-night"
    assert settings.extras["unknown_legacy_flag"] == "preserve_me"


def test_restore_from_backup(temp_config_file: Path):
    """Verify restoring a backup restores the exact pre-migration file."""
    original_data = {"default_theme": "abyssal", "anthropic_api_key": "sk-ant-orig"}
    temp_config_file.write_text(json.dumps(original_data), encoding="utf-8")

    # Migrate (creates backup)
    migrated, bak_path = migrate_config_if_needed(temp_config_file)
    assert migrated is True
    assert bak_path is not None

    # Modify migrated file
    set_config_value("ui.theme", "dracula", cfg_path=temp_config_file)
    assert load_settings(cfg_path=temp_config_file).ui.theme == "dracula"

    # Restore
    restored_bak = restore_config_backup(temp_config_file)
    assert restored_bak.resolve() == bak_path.resolve()
    restored_data = json.loads(temp_config_file.read_text(encoding="utf-8"))
    assert restored_data == original_data


# ---------------------------------------------------------------------------
# 5. Atomic-Write and Permissions Tests
# ---------------------------------------------------------------------------

def test_atomic_write_file_permissions(temp_config_file: Path):
    """Verify atomic write creates files with mode 0600 and directories with 0700."""
    content = json.dumps({"schema_version": 1})
    atomic_write_config(temp_config_file, content)

    file_mode = temp_config_file.stat().st_mode & 0o777
    assert file_mode == 0o600

    dir_mode = temp_config_file.parent.stat().st_mode & 0o777
    assert dir_mode == 0o700


def test_atomic_write_interruption_preserves_original(temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Simulate a crash/failure during atomic write (before os.replace).

    The original configuration file must remain unmodified and uncorrupted.
    """
    initial_content = json.dumps({"schema_version": 1, "ui": {"theme": "catppuccin"}})
    atomic_write_config(temp_config_file, initial_content)

    def failing_replace(src, dst):
        raise OSError("Simulated disk I/O failure or power loss before rename")

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError, match="Simulated disk I/O failure"):
        atomic_write_config(temp_config_file, json.dumps({"corrupted": True}))

    # Original file is intact and valid
    preserved_content = json.loads(temp_config_file.read_text(encoding="utf-8"))
    assert preserved_content["schema_version"] == 1
    assert preserved_content["ui"]["theme"] == "catppuccin"
    assert "corrupted" not in preserved_content


# ---------------------------------------------------------------------------
# 6. Validation Error Reporting & Exit Code 3
# ---------------------------------------------------------------------------

def test_validation_error_port_out_of_range(temp_config_file: Path):
    """Verify invalid port raises ConfigurationError with field path and hint."""
    bad_data = {
        "schema_version": 1,
        "server": {"ws_port": 99999},
    }
    atomic_write_config(temp_config_file, json.dumps(bad_data))

    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(cfg_path=temp_config_file)

    err = exc_info.value
    assert "server.ws_port" in err.loc
    assert "Port must be between 1 and 65535" in err.message or (err.hint and "1 and 65535" in err.hint)


def test_validation_error_unknown_provider(temp_config_file: Path):
    """Verify unknown provider raises ConfigurationError with allowed providers hint."""
    bad_data = {
        "schema_version": 1,
        "defaults": {"default_provider": "unknown_super_llm"},
    }
    atomic_write_config(temp_config_file, json.dumps(bad_data))

    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(cfg_path=temp_config_file)

    err = exc_info.value
    assert "defaults.default_provider" in err.loc
    assert "Unknown provider name" in err.message


# ---------------------------------------------------------------------------
# 7. CLI Subcommands Tests (config show, path, set, validate, migrate)
# ---------------------------------------------------------------------------

def test_cli_config_path(cli_runner: CliRunner, temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Test `octoflow config path` outputs config file path."""
    monkeypatch.setattr("octoflow.commands.config.get_default_config_path", lambda: temp_config_file)
    result = cli_runner.invoke(app, ["config", "path"])
    assert result.exit_code == 0
    assert str(temp_config_file) in result.output


def test_cli_config_show_masks_secrets(cli_runner: CliRunner, temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Test `octoflow config show` and `--json` never output plaintext secrets."""
    monkeypatch.setattr("octoflow.commands.config.get_default_config_path", lambda: temp_config_file)
    monkeypatch.setattr("octoflow.settings.get_default_config_path", lambda: temp_config_file)

    cfg = {
        "schema_version": 1,
        "providers": {
            "anthropic": {
                "name": "anthropic",
                "api_key": "sk-ant-api0123456789abcdef",
            }
        },
    }
    atomic_write_config(temp_config_file, json.dumps(cfg))

    # Table view
    res_table = cli_runner.invoke(app, ["config", "show"])
    assert res_table.exit_code == 0
    assert "sk-ant-api0123456789abcdef" not in res_table.output
    assert "sk-****" in res_table.output

    # JSON view
    res_json = cli_runner.invoke(app, ["config", "show", "--json"])
    assert res_json.exit_code == 0
    assert "sk-ant-api0123456789abcdef" not in res_json.output
    data = json.loads(res_json.output)
    assert data["providers"]["anthropic"]["api_key"] == "sk-****"


def test_cli_config_set_valid_and_invalid(cli_runner: CliRunner, temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Test `octoflow config set` updates valid keys and returns exit code 3 on invalid values."""
    monkeypatch.setattr("octoflow.commands.config.get_default_config_path", lambda: temp_config_file)
    monkeypatch.setattr("octoflow.settings.get_default_config_path", lambda: temp_config_file)

    # Valid set
    res = cli_runner.invoke(app, ["config", "set", "ui.theme", "dracula"])
    assert res.exit_code == 0
    assert "Successfully set" in res.output
    assert load_settings(cfg_path=temp_config_file).ui.theme == "dracula"

    # Invalid port (exit code 3, one-line error, no traceback)
    res_err = cli_runner.invoke(app, ["config", "set", "server.ws_port", "99999"])
    assert res_err.exit_code == 3
    assert "Traceback" not in res_err.output
    assert "server.ws_port" in res_err.output


def test_cli_config_validate(cli_runner: CliRunner, temp_config_file: Path, monkeypatch: pytest.MonkeyPatch):
    """Test `octoflow config validate` command."""
    monkeypatch.setattr("octoflow.commands.config.get_default_config_path", lambda: temp_config_file)
    monkeypatch.setattr("octoflow.settings.get_default_config_path", lambda: temp_config_file)

    # Valid config
    atomic_write_config(temp_config_file, json.dumps({"schema_version": 1}))
    res = cli_runner.invoke(app, ["config", "validate"])
    assert res.exit_code == 0
    assert "Configuration valid" in res.output

    # Corrupt/invalid config (exit code 3)
    atomic_write_config(temp_config_file, json.dumps({"schema_version": 1, "server": {"ws_port": -1}}))
    res_bad = cli_runner.invoke(app, ["config", "validate"])
    assert res_bad.exit_code == 3
    assert "Traceback" not in res_bad.output
    assert "server.ws_port" in res_bad.output
