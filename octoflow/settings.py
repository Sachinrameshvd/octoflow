"""Typed, versioned, validated configuration settings system for OctoFlow.

Follows Pydantic v2 validation with clear precedence:
defaults < config file < environment variables < CLI flags.
Includes atomic writes, automatic migration, secret masking, and 0600 file permissions.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)

from octoflow.budget import RunBudget

CURRENT_SCHEMA_VERSION = 1

VALID_PROVIDERS: set[str] = {
    "anthropic",
    "openai",
    "gemini",
    "grok",
    "deepseek",
    "ollama",
    "mock",
    "fake",
}

_WARNED_EXTRAS: set[str] = set()


class ConfigurationError(Exception):
    """Raised when configuration validation or loading fails."""

    def __init__(self, message: str, loc: str | None = None, hint: str | None = None):
        super().__init__(message)
        self.message = message
        self.loc = loc or ""
        self.hint = hint or ""

    def format_one_liner(self) -> str:
        loc_str = f" in '{self.loc}'" if self.loc else ""
        s = f"Configuration error{loc_str}: {self.message}"
        if self.hint:
            s += f" (Hint: {self.hint})"
        return s


def get_default_config_dir() -> Path:
    """Return default directory ~/.octoflow with 0700 permissions."""
    home = Path.home()
    cfg_dir = home / ".octoflow"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    try:
        cur_mode = cfg_dir.stat().st_mode & 0o777
        if (cur_mode & ~0o700) != 0:
            cfg_dir.chmod(0o700)
    except OSError:
        pass
    return cfg_dir


def get_default_config_path() -> Path:
    """Return default config file path ~/.octoflow/config.json."""
    return get_default_config_dir() / "config.json"


def mask_secret_value(val: str | SecretStr | None) -> str:
    """Mask secret credential for display, showing first 3 characters followed by ****."""
    if val is None:
        return ""
    raw = val.get_secret_value() if isinstance(val, SecretStr) else str(val).strip()
    if not raw:
        return ""
    if len(raw) <= 4:
        return "****"
    return raw[:3] + "****"


def _warn_extras_once(extras: dict[str, Any]) -> None:
    """Print a one-time warning for unknown keys preserved under extras."""
    unwarned = [k for k in extras.keys() if k not in _WARNED_EXTRAS]
    if unwarned:
        for k in unwarned:
            _WARNED_EXTRAS.add(k)
        print(
            f"Warning: Preserving unknown configuration keys under extras: {', '.join(unwarned)}",
            file=sys.stderr,
        )


class ProviderSettings(BaseModel):
    """Configuration for an individual LLM provider core."""

    name: str
    enabled: bool = True
    model: str | None = None
    base_url: str | None = None
    api_key: SecretStr | None = None
    timeout: float = 60.0

    @model_validator(mode="before")
    @classmethod
    def normalize_provider_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "name" not in data and "provider" in data:
                data["name"] = data["provider"]
        return data

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v_clean = str(v).strip().lower()
        if v_clean not in VALID_PROVIDERS:
            raise ValueError(
                f"Unknown provider name '{v}'. Allowed providers: {', '.join(sorted(VALID_PROVIDERS))}"
            )
        return v_clean

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Timeout must be a positive number of seconds.")
        return v


class UISettings(BaseModel):
    """Configuration for terminal user interface and visual preferences."""

    theme: str = "catppuccin"
    animation: bool = True
    color: bool = True
    ascii: bool = False


class ServerSettings(BaseModel):
    """Configuration for localhost telemetry WebSocket and HTTP server."""

    host: str = "127.0.0.1"
    ws_port: int = 8088
    http_port: int = 8089

    @field_validator("ws_port", "http_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class DefaultsSettings(BaseModel):
    """Default runtime execution parameters for the swarm."""

    default_provider: str = "anthropic"
    default_model: str | None = "claude-3-5-sonnet-20241022"
    default_scale: int = 1
    encoder_backend: str = "numpy"
    gate_mode: str = "gated"

    @field_validator("gate_mode")
    @classmethod
    def validate_gate_mode(cls, v: str) -> str:
        v_clean = str(v).strip().lower()
        if v_clean in ("always_escalate", "ungated"):
            return "always_escalate"
        if v_clean in ("gated", "normal"):
            return "gated"
        raise ValueError(f"Unknown gate_mode '{v}'. Allowed modes: 'gated', 'always_escalate'")

    @field_validator("encoder_backend")
    @classmethod
    def validate_encoder_backend(cls, v: str) -> str:
        v_clean = str(v).strip().lower()
        if v_clean not in ("auto", "numpy", "torch"):
            raise ValueError(
                f"Unknown encoder_backend '{v}'. Allowed backends: 'auto', 'numpy', 'torch'"
            )
        return v_clean

    @field_validator("default_provider")
    @classmethod
    def validate_default_provider(cls, v: str) -> str:
        v_clean = str(v).strip().lower()
        if v_clean not in VALID_PROVIDERS:
            raise ValueError(
                f"Unknown provider name '{v}'. Allowed providers: {', '.join(sorted(VALID_PROVIDERS))}"
            )
        return v_clean

    @field_validator("default_scale")
    @classmethod
    def validate_scale(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Default scale must be at least 1 octopus.")
        return v


class Settings(BaseModel):
    """Root typed configuration container for OctoFlow (Schema Version 1)."""

    schema_version: int = CURRENT_SCHEMA_VERSION
    defaults: DefaultsSettings = Field(default_factory=DefaultsSettings)
    ui: UISettings = Field(default_factory=UISettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    budget: RunBudget = Field(default_factory=RunBudget)
    providers: dict[str, ProviderSettings] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)
    webhook_url: str | None = None
    llm_pool: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def capture_unknown_extras(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        known_keys = {
            "schema_version",
            "defaults",
            "ui",
            "server",
            "budget",
            "providers",
            "extras",
            "webhook_url",
            "llm_pool",
        }

        # Normalize providers if provided as list or dictionary without names
        if "providers" in data and isinstance(data["providers"], dict):
            norm_providers = {}
            for k, val in data["providers"].items():
                if isinstance(val, dict):
                    val_copy = dict(val)
                    if "name" not in val_copy:
                        val_copy["name"] = k
                    norm_providers[k] = val_copy
                else:
                    norm_providers[k] = val
            data["providers"] = norm_providers
        elif "providers" in data and isinstance(data["providers"], list):
            norm_providers = {}
            for item in data["providers"]:
                if isinstance(item, dict):
                    p_name = item.get("name") or item.get("provider")
                    if p_name:
                        norm_providers[str(p_name)] = item
            data["providers"] = norm_providers

        raw_extras = dict(data.get("extras", {})) if isinstance(data.get("extras"), dict) else {}
        clean_data = {}
        for k, v in data.items():
            if k in known_keys:
                clean_data[k] = v
            else:
                raw_extras[k] = v
        clean_data["extras"] = raw_extras
        return clean_data

    def to_dict(self, mask_secrets: bool = False) -> dict[str, Any]:
        """Serialize settings to dictionary, optionally masking secret keys."""
        dumped = self.model_dump(mode="python")

        # Process providers
        if "providers" in dumped and isinstance(dumped["providers"], dict):
            for _p_name, p_data in dumped["providers"].items():
                if isinstance(p_data, dict) and "api_key" in p_data:
                    raw_k = p_data["api_key"]
                    if raw_k is not None:
                        if mask_secrets:
                            p_data["api_key"] = mask_secret_value(raw_k)
                        else:
                            p_data["api_key"] = (
                                raw_k.get_secret_value()
                                if isinstance(raw_k, SecretStr)
                                else str(raw_k)
                            )

        # Mask secrets in extras if requested
        if mask_secrets and "extras" in dumped and isinstance(dumped["extras"], dict):
            for k, v in dumped["extras"].items():
                if any(
                    term in k.lower() for term in ("key", "secret", "token", "password")
                ) and isinstance(v, str):
                    dumped["extras"][k] = mask_secret_value(v)

        return dumped


def atomic_write_config(path: Path, content: str) -> None:
    """Atomically write content to path with mode 0600 using a temp file and os.replace."""
    path = path.resolve()
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Ensure parent directory is 0700
    try:
        cur_parent_mode = parent.stat().st_mode & 0o777
        if (cur_parent_mode & ~0o700) != 0:
            parent.chmod(0o700)
    except OSError:
        pass

    # Create temporary file in the same directory to guarantee same filesystem for os.replace
    prefix = f".{path.name}.tmp_"
    fd, tmp_path_str = tempfile.mkstemp(dir=str(parent), prefix=prefix)
    tmp_path = Path(tmp_path_str)
    try:
        # Enforce 0600 on the temp file descriptor immediately
        os.chmod(tmp_path_str, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace
        os.replace(tmp_path, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except Exception:
        # Clean up temp file on failure so it does not linger
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def create_config_backup(cfg_path: Path) -> Path:
    """Create timestamped backup config.json.bak-YYYYmmddHHMMSS with 0600 permissions."""
    cfg_path = cfg_path.resolve()
    if not cfg_path.exists():
        raise FileNotFoundError(f"Cannot back up non-existent config: {cfg_path}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    bak_path = cfg_path.parent / f"{cfg_path.name}.bak-{timestamp}"

    # Read existing content and write to backup with 0600
    content = cfg_path.read_text(encoding="utf-8")
    atomic_write_config(bak_path, content)

    # Verify backup exists and is readable
    if not bak_path.exists() or not os.access(bak_path, os.R_OK):
        raise RuntimeError(f"Backup verification failed for {bak_path}")

    return bak_path


def restore_config_backup(cfg_path: Path | None = None) -> Path:
    """Restore configuration from the latest config.json.bak-* file."""
    if cfg_path is None:
        cfg_path = get_default_config_path()
    cfg_path = cfg_path.resolve()
    parent = cfg_path.parent

    pattern = f"{cfg_path.name}.bak-*"
    backups = sorted(parent.glob(pattern), reverse=True)
    if not backups:
        raise FileNotFoundError(f"No backup file found matching {pattern} in {parent}")

    latest_bak = backups[0]
    content = latest_bak.read_text(encoding="utf-8")
    atomic_write_config(cfg_path, content)
    return latest_bak


def transform_legacy_config_data(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Transform legacy flat config dict into structured Settings dict."""
    consumed_keys = set()

    # Defaults
    defaults: dict[str, Any] = {}
    if "default_provider" in raw_data:
        defaults["default_provider"] = raw_data["default_provider"]
        consumed_keys.add("default_provider")
    elif "model_provider" in raw_data:
        defaults["default_provider"] = raw_data["model_provider"]
        consumed_keys.add("model_provider")
    elif "default_model" in raw_data and raw_data["default_model"] in VALID_PROVIDERS:
        defaults["default_provider"] = raw_data["default_model"]

    if "default_model" in raw_data:
        defaults["default_model"] = raw_data["default_model"]
        consumed_keys.add("default_model")
    elif "model_name" in raw_data:
        defaults["default_model"] = raw_data["model_name"]
        consumed_keys.add("model_name")

    if "default_scale" in raw_data:
        defaults["default_scale"] = int(raw_data["default_scale"])
        consumed_keys.add("default_scale")

    if "encoder_backend" in raw_data:
        defaults["encoder_backend"] = str(raw_data["encoder_backend"]).strip().lower()
        consumed_keys.add("encoder_backend")

    # UI
    ui: dict[str, Any] = {}
    if "default_theme" in raw_data:
        ui["theme"] = raw_data["default_theme"]
        consumed_keys.add("default_theme")
    elif "theme" in raw_data:
        ui["theme"] = raw_data["theme"]
        consumed_keys.add("theme")

    for k in ("animation", "color", "ascii"):
        if k in raw_data:
            ui[k] = bool(raw_data[k])
            consumed_keys.add(k)

    # Server
    server: dict[str, Any] = {}
    if "host" in raw_data:
        server["host"] = str(raw_data["host"])
        consumed_keys.add("host")
    if "ws_port" in raw_data:
        server["ws_port"] = int(raw_data["ws_port"])
        consumed_keys.add("ws_port")
    elif "telemetry_port" in raw_data:
        server["ws_port"] = int(raw_data["telemetry_port"])
        consumed_keys.add("telemetry_port")
    if "http_port" in raw_data:
        server["http_port"] = int(raw_data["http_port"])
        consumed_keys.add("http_port")

    # Providers
    providers: dict[str, Any] = {}
    provider_keys_map = {
        "anthropic": "anthropic_api_key",
        "openai": "openai_api_key",
        "gemini": "gemini_api_key",
        "grok": "grok_api_key",
        "deepseek": "deepseek_api_key",
    }
    for p_name, key_field in provider_keys_map.items():
        if key_field in raw_data and raw_data[key_field]:
            providers[p_name] = {
                "name": p_name,
                "api_key": raw_data[key_field],
                "enabled": True,
            }
            consumed_keys.add(key_field)

    if "ollama_base_url" in raw_data:
        providers["ollama"] = {
            "name": "ollama",
            "base_url": raw_data["ollama_base_url"],
            "enabled": True,
        }
        consumed_keys.add("ollama_base_url")

    # Preserve llm_pool if present
    llm_pool = []
    if "llm_pool" in raw_data and isinstance(raw_data["llm_pool"], list):
        llm_pool = raw_data["llm_pool"]
        consumed_keys.add("llm_pool")
        for entry in llm_pool:
            if isinstance(entry, dict):
                p_id = entry.get("provider") or entry.get("name")
                if p_id and p_id in VALID_PROVIDERS and p_id not in providers:
                    providers[p_id] = {
                        "name": p_id,
                        "model": entry.get("model"),
                        "base_url": entry.get("base_url"),
                        "api_key": entry.get("api_key"),
                        "enabled": entry.get("enabled", True),
                    }

    # Webhook
    webhook_url = None
    if "webhook_url" in raw_data:
        webhook_url = raw_data["webhook_url"]
        consumed_keys.add("webhook_url")

    # Check for existing providers section
    if "providers" in raw_data and isinstance(raw_data["providers"], dict):
        for pk, pv in raw_data["providers"].items():
            providers[pk] = pv
        consumed_keys.add("providers")

    # Nested sections if already present
    if "defaults" in raw_data and isinstance(raw_data["defaults"], dict):
        defaults.update(raw_data["defaults"])
        consumed_keys.add("defaults")
    if "ui" in raw_data and isinstance(raw_data["ui"], dict):
        ui.update(raw_data["ui"])
        consumed_keys.add("ui")
    if "server" in raw_data and isinstance(raw_data["server"], dict):
        server.update(raw_data["server"])
        consumed_keys.add("server")
    budget = {
        "max_tokens": 200_000,
        "max_llm_calls": 200,
        "max_wall_seconds": 1800,
        "max_heal_iterations": 5,
        "max_files_written": 200,
        "no_limits": False,
    }
    if "budget" in raw_data and isinstance(raw_data["budget"], dict):
        budget.update(raw_data["budget"])
        consumed_keys.add("budget")

    # Extras: anything not consumed
    extras = {}
    for k, v in raw_data.items():
        if k not in consumed_keys and k != "schema_version":
            extras[k] = v

    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "defaults": defaults,
        "ui": ui,
        "server": server,
        "budget": budget,
        "providers": providers,
        "extras": extras,
        "webhook_url": webhook_url,
        "llm_pool": llm_pool,
    }


def migrate_config_if_needed(cfg_path: Path) -> tuple[bool, Path | None]:
    """Detect missing or older schema_version, backup, transform, and write atomically.

    Returns (was_migrated, backup_path).
    """
    cfg_path = cfg_path.resolve()
    if not cfg_path.exists():
        return False, None

    try:
        raw_text = cfg_path.read_text(encoding="utf-8")
        raw_data = json.loads(raw_text) if raw_text.strip() else {}
    except Exception as e:
        raise ConfigurationError(f"Failed to read existing configuration at {cfg_path}: {e}") from e

    if not isinstance(raw_data, dict):
        raw_data = {}

    schema_version = raw_data.get("schema_version")
    if schema_version == CURRENT_SCHEMA_VERSION:
        # Already on current schema version
        return False, None

    # Backup existing configuration before touching it
    bak_path = create_config_backup(cfg_path)

    # Transform legacy structure
    transformed = transform_legacy_config_data(raw_data)

    # Validate new structure
    try:
        settings_obj = Settings.model_validate(transformed)
    except ValidationError as e:
        first_err = e.errors()[0]
        loc = ".".join(str(p) for p in first_err["loc"])
        msg = first_err["msg"]
        hint = None
        if "port" in loc.lower():
            hint = "Ports must be between 1 and 65535"
        elif "provider" in loc.lower():
            hint = f"Allowed providers: {', '.join(sorted(VALID_PROVIDERS))}"
        elif "scale" in loc.lower():
            hint = "Scale must be at least 1 octopus"
        raise ConfigurationError(msg, loc=loc, hint=hint) from e

    # Write migrated structure atomically
    migrated_json = json.dumps(settings_obj.to_dict(mask_secrets=False), indent=2)
    atomic_write_config(cfg_path, migrated_json)

    if settings_obj.extras:
        _warn_extras_once(settings_obj.extras)

    return True, bak_path


def _deep_merge_dict(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Recursively merge source dictionary into target dictionary."""
    for key, val in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(val, dict):
            _deep_merge_dict(target[key], val)
        else:
            target[key] = val


def _apply_env_overrides(data: dict[str, Any]) -> None:
    """Apply environment variables over data with proper precedence."""
    env = os.environ

    # UI Settings
    if "OCTOFLOW_THEME" in env:
        data.setdefault("ui", {})["theme"] = env["OCTOFLOW_THEME"]
    if "OCTOFLOW_ANIMATION" in env:
        data.setdefault("ui", {})["animation"] = env["OCTOFLOW_ANIMATION"].lower() in (
            "1",
            "true",
            "yes",
        )
    if "OCTOFLOW_COLOR" in env:
        data.setdefault("ui", {})["color"] = env["OCTOFLOW_COLOR"].lower() in ("1", "true", "yes")
    if "OCTOFLOW_ASCII" in env:
        data.setdefault("ui", {})["ascii"] = env["OCTOFLOW_ASCII"].lower() in ("1", "true", "yes")

    # Server Settings
    if "OCTOFLOW_HOST" in env:
        data.setdefault("server", {})["host"] = env["OCTOFLOW_HOST"]
    for ws_var in ("OCTOFLOW_WS_PORT", "OCTOFLOW_PORT", "OCTOFLOW_TELEMETRY_PORT"):
        if ws_var in env:
            try:
                data.setdefault("server", {})["ws_port"] = int(env[ws_var])
                break
            except ValueError as err:
                raise ConfigurationError(
                    f"Invalid integer for {ws_var}: '{env[ws_var]}'", loc="server.ws_port"
                ) from err
    if "OCTOFLOW_HTTP_PORT" in env:
        try:
            data.setdefault("server", {})["http_port"] = int(env["OCTOFLOW_HTTP_PORT"])
        except ValueError as err:
            raise ConfigurationError(
                f"Invalid integer for OCTOFLOW_HTTP_PORT: '{env['OCTOFLOW_HTTP_PORT']}'",
                loc="server.http_port",
            ) from err

    # Defaults Settings
    for prov_var in ("OCTOFLOW_DEFAULT_PROVIDER", "OCTOFLOW_PROVIDER"):
        if prov_var in env:
            data.setdefault("defaults", {})["default_provider"] = env[prov_var]
            break
    for model_var in ("OCTOFLOW_DEFAULT_MODEL", "OCTOFLOW_MODEL"):
        if model_var in env:
            data.setdefault("defaults", {})["default_model"] = env[model_var]
            break
    for scale_var in ("OCTOFLOW_DEFAULT_SCALE", "OCTOFLOW_SCALE"):
        if scale_var in env:
            try:
                data.setdefault("defaults", {})["default_scale"] = int(env[scale_var])
                break
            except ValueError as err:
                raise ConfigurationError(
                    f"Invalid integer for {scale_var}: '{env[scale_var]}'",
                    loc="defaults.default_scale",
                ) from err
    for backend_var in ("OCTOFLOW_ENCODER_BACKEND", "ENCODER_BACKEND"):
        if backend_var in env:
            data.setdefault("defaults", {})["encoder_backend"] = env[backend_var].strip().lower()
            break

    # Webhook
    for wh_var in ("OCTOFLOW_WEBHOOK_URL", "SLACK_WEBHOOK_URL", "DISCORD_WEBHOOK_URL"):
        if wh_var in env:
            data["webhook_url"] = env[wh_var]
            break

    # Well-known provider API keys & URLs
    providers = data.setdefault("providers", {})

    if "ANTHROPIC_API_KEY" in env:
        p = providers.setdefault("anthropic", {"name": "anthropic"})
        p["api_key"] = env["ANTHROPIC_API_KEY"]

    if "OPENAI_API_KEY" in env:
        p = providers.setdefault("openai", {"name": "openai"})
        p["api_key"] = env["OPENAI_API_KEY"]
    if "OPENAI_BASE_URL" in env:
        p = providers.setdefault("openai", {"name": "openai"})
        p["base_url"] = env["OPENAI_BASE_URL"]

    gemini_key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY")
    if gemini_key:
        p = providers.setdefault("gemini", {"name": "gemini"})
        p["api_key"] = gemini_key

    grok_key = env.get("XAI_API_KEY") or env.get("GROK_API_KEY")
    if grok_key:
        p = providers.setdefault("grok", {"name": "grok"})
        p["api_key"] = grok_key

    if "DEEPSEEK_API_KEY" in env:
        p = providers.setdefault("deepseek", {"name": "deepseek"})
        p["api_key"] = env["DEEPSEEK_API_KEY"]

    if "OLLAMA_BASE_URL" in env:
        p = providers.setdefault("ollama", {"name": "ollama"})
        p["base_url"] = env["OLLAMA_BASE_URL"]

    # Generic OCTOFLOW_<SECTION>_<KEY>
    for k, v in env.items():
        if k.startswith("OCTOFLOW_") and k not in (
            "OCTOFLOW_DRY_RUN",
            "OCTOFLOW_FORCE_LIVE",
            "OCTOFLOW_TESTING",
            "OCTOFLOW_LEGACY_ROUTER",
            "OCTOFLOW_DEV",
            "OCTOFLOW_UNRESTRICTED_TOOLS",
        ):
            parts = k[len("OCTOFLOW_") :].lower().split("_", 1)
            if len(parts) == 2:
                sec, prop = parts
                if sec in ("ui", "server", "defaults", "budget"):
                    cur_sec = data.setdefault(sec, {})
                    # Type coerce if integer or boolean
                    if v.isdigit():
                        cur_sec[prop] = int(v)
                    elif v.lower() in ("true", "false"):
                        cur_sec[prop] = v.lower() == "true"
                    else:
                        cur_sec[prop] = v


def _apply_cli_overrides(data: dict[str, Any], cli_overrides: dict[str, Any]) -> None:
    """Apply CLI overrides (supporting dotted keys like 'server.ws_port') over data."""
    for key, val in cli_overrides.items():
        if "." in key:
            parts = key.split(".")
            curr = data
            for part in parts[:-1]:
                curr = curr.setdefault(part, {})
            curr[parts[-1]] = val
        elif isinstance(val, dict) and key in data and isinstance(data[key], dict):
            _deep_merge_dict(data[key], val)
        else:
            data[key] = val


def load_settings(
    cli_overrides: dict[str, Any] | None = None,
    cfg_path: Path | None = None,
) -> Settings:
    """Load, validate, and return the application settings with full precedence.

    Precedence order:
    defaults < config file < environment variables < CLI flags.
    """
    if cfg_path is None:
        cfg_path = get_default_config_path()
    cfg_path = cfg_path.resolve()

    # 1. Base defaults
    merged_data: dict[str, Any] = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "defaults": {
            "default_provider": "anthropic",
            "default_model": "claude-3-5-sonnet-20241022",
            "default_scale": 1,
        },
        "ui": {
            "theme": "catppuccin",
            "animation": True,
            "color": True,
            "ascii": False,
        },
        "server": {
            "host": "127.0.0.1",
            "ws_port": 8088,
            "http_port": 8089,
        },
        "budget": {
            "max_tokens": 200_000,
            "max_llm_calls": 200,
            "max_wall_seconds": 1800,
            "max_heal_iterations": 5,
            "max_files_written": 200,
            "no_limits": False,
        },
        "providers": {},
        "extras": {},
    }

    # 2. Config file
    if cfg_path.exists():
        try:
            cur_parent_mode = cfg_path.parent.stat().st_mode & 0o777
            if (cur_parent_mode & ~0o700) != 0:
                cfg_path.parent.chmod(0o700)
                print(
                    f"Notice: Hardened permissions on {cfg_path.parent} to {oct(0o700)} (was {oct(cur_parent_mode)})."
                )
        except OSError:
            pass

        try:
            cur_file_mode = cfg_path.stat().st_mode & 0o777
            if (cur_file_mode & ~0o600) != 0:
                cfg_path.chmod(0o600)
                print(
                    f"Notice: Hardened permissions on {cfg_path} to {oct(0o600)} (was {oct(cur_file_mode)})."
                )
        except OSError:
            pass

        migrate_config_if_needed(cfg_path)
        try:
            raw_text = cfg_path.read_text(encoding="utf-8")
            file_data = json.loads(raw_text) if raw_text.strip() else {}
            if isinstance(file_data, dict):
                _deep_merge_dict(merged_data, file_data)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file {cfg_path}: {e}") from e

    # 3. Environment variables
    _apply_env_overrides(merged_data)

    # 4. CLI flags / overrides
    if cli_overrides:
        _apply_cli_overrides(merged_data, cli_overrides)

    # 5. Validation
    try:
        settings_obj = Settings.model_validate(merged_data)
    except ValidationError as e:
        first_err = e.errors()[0]
        loc = ".".join(str(p) for p in first_err["loc"])
        msg = first_err["msg"]
        hint = None
        if "port" in loc.lower():
            hint = "Ports must be between 1 and 65535"
        elif "provider" in loc.lower():
            hint = f"Allowed providers: {', '.join(sorted(VALID_PROVIDERS))}"
        elif "scale" in loc.lower():
            hint = "Scale must be at least 1 octopus"
        raise ConfigurationError(msg, loc=loc, hint=hint) from e

    if settings_obj.extras:
        _warn_extras_once(settings_obj.extras)

    return settings_obj


def save_settings(settings: Settings, cfg_path: Path | None = None) -> Path:
    """Save settings atomically to config file with mode 0600."""
    if cfg_path is None:
        cfg_path = get_default_config_path()
    cfg_path = cfg_path.resolve()

    serialized = json.dumps(settings.to_dict(mask_secrets=False), indent=2)
    atomic_write_config(cfg_path, serialized)
    return cfg_path


def set_config_value(key_path: str, value_str: str, cfg_path: Path | None = None) -> Settings:
    """Set a single configuration key path to a value, validate, and write atomically."""
    if cfg_path is None:
        cfg_path = get_default_config_path()
    cfg_path = cfg_path.resolve()

    # Load existing file raw data or defaults
    current_data = load_settings(cfg_path=cfg_path).to_dict(mask_secrets=False)

    # Type coercion for common primitives
    val: Any = value_str
    if value_str.lower() in ("true", "yes"):
        val = True
    elif value_str.lower() in ("false", "no"):
        val = False
    else:
        try:
            val = int(value_str)
        except ValueError:
            try:
                val = float(value_str)
            except ValueError:
                val = value_str

    # Apply override
    _apply_cli_overrides(current_data, {key_path: val})

    # Validate
    try:
        validated = Settings.model_validate(current_data)
    except ValidationError as e:
        first_err = e.errors()[0]
        loc = ".".join(str(p) for p in first_err["loc"])
        msg = first_err["msg"]
        hint = None
        if "port" in loc.lower():
            hint = "Ports must be between 1 and 65535"
        elif "provider" in loc.lower():
            hint = f"Allowed providers: {', '.join(sorted(VALID_PROVIDERS))}"
        raise ConfigurationError(msg, loc=loc, hint=hint) from e

    # Write atomically
    save_settings(validated, cfg_path)
    return validated
