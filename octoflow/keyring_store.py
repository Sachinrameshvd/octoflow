"""Keyring and Multi-Tier Credential Resolution Store for OctoFlow.

Enforces strict key resolution hierarchy:
1. Environment Variables (ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY/GOOGLE_API_KEY, etc.)
2. OS Keyring Store (if optional extra `octoflow[keyring]` is installed)
3. Local Configuration File (~/.octoflow/config.json, mode 0600)

Never imports `keyring` as a hard dependency; operates gracefully without it.
"""

import os
from typing import Any

SERVICE_NAME = "octoflow"
KEYRING_SERVICE_NAME = SERVICE_NAME

PROVIDER_ENV_VARS: dict[str, list[str]] = {
    "anthropic": ["ANTHROPIC_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "grok": ["XAI_API_KEY", "GROK_API_KEY"],
    "xai": ["XAI_API_KEY", "GROK_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
}


def is_keyring_available() -> bool:
    """Return True if keyring package is installed and has a functional backend."""
    try:
        import keyring
        from keyring.backend import KeyringBackend

        backend = keyring.get_keyring()
        if not backend or not isinstance(backend, KeyringBackend):
            return False
        # Some headless / test environments assign fail.Keyring
        backend_name = backend.__class__.__name__.lower()
        if "fail" in backend_name or "null" in backend_name:
            return False
        return True
    except Exception:
        return False


def get_keyring_key(provider: str) -> str | None:
    """Retrieve an API key from the OS Keyring if available."""
    try:
        import keyring

        val = keyring.get_password(SERVICE_NAME, provider.lower().strip())
        return val.strip() if val else None
    except Exception:
        return None


def set_keyring_key(provider: str, key: str) -> bool:
    """Store an API key securely in the OS Keyring."""
    try:
        import keyring

        keyring.set_password(SERVICE_NAME, provider.lower().strip(), key.strip())
        return True
    except Exception:
        return False


def delete_keyring_key(provider: str) -> bool:
    """Remove an API key from the OS Keyring."""
    try:
        import keyring

        keyring.delete_password(SERVICE_NAME, provider.lower().strip())
        return True
    except Exception:
        return False


def get_env_key(provider: str) -> str | None:
    """Resolve API key strictly from environment variables."""
    p_norm = provider.lower().strip()
    candidates = PROVIDER_ENV_VARS.get(p_norm, [f"{p_norm.upper()}_API_KEY", "API_KEY"])
    for var in candidates:
        val = os.getenv(var)
        if val and val.strip():
            return val.strip()
    return None


def get_config_key(provider: str, config: Any | None = None) -> str | None:
    """Resolve API key strictly from config object or ~/.octoflow/config.json."""
    p_norm = provider.lower().strip()

    # 1. From provided config object (dict, OctoFlowConfig, or Settings)
    if config is not None:
        if isinstance(config, dict):
            # Check direct provider key
            k1 = config.get(f"{p_norm}_api_key") or config.get("api_key")
            if k1 and str(k1).strip():
                return str(k1).strip()
            # Check providers dict
            providers_dict = config.get("providers", {})
            if isinstance(providers_dict, dict) and p_norm in providers_dict:
                prov_val = providers_dict[p_norm]
                if isinstance(prov_val, dict):
                    k2 = prov_val.get("api_key")
                    if k2 and str(k2).strip():
                        return str(k2).strip()
            # Check llm_pool
            for entry in config.get("llm_pool", []):
                if isinstance(entry, dict) and entry.get("provider") == p_norm:
                    k3 = entry.get("api_key")
                    if k3 and str(k3).strip():
                        return str(k3).strip()
        else:
            # Check object attributes
            val = getattr(config, f"{p_norm}_api_key", None) or getattr(config, "api_key", None)
            if val is not None:
                raw = val.get_secret_value() if hasattr(val, "get_secret_value") else str(val)
                if raw.strip():
                    return raw.strip()
            # Check providers attribute on Settings
            if hasattr(config, "providers") and isinstance(config.providers, dict):
                if p_norm in config.providers:
                    p_entry = config.providers[p_norm]
                    k_val = getattr(p_entry, "api_key", None)
                    if k_val:
                        raw = (
                            k_val.get_secret_value()
                            if hasattr(k_val, "get_secret_value")
                            else str(k_val)
                        )
                        if raw.strip():
                            return raw.strip()

    # 2. Fallback: inspect saved ~/.octoflow/config.json
    try:
        from octoflow.config import get_octoflow_dir, load_secure_config

        cfg_file = get_octoflow_dir() / "config.json"
        if cfg_file.exists():
            data = load_secure_config(cfg_file)
            val = data.get(f"{p_norm}_api_key") or data.get("api_key")
            if val and str(val).strip():
                return str(val).strip()
            for entry in data.get("llm_pool", []):
                if isinstance(entry, dict) and entry.get("provider") == p_norm:
                    entry_k = entry.get("api_key")
                    if entry_k and str(entry_k).strip():
                        return str(entry_k).strip()
    except Exception:
        pass

    return None


def resolve_api_key(
    provider: str, config: Any | None = None
) -> tuple[str | None, str]:
    """Resolve API key following the strict hierarchy: ENV > KEYRING > CONFIG.

    Returns:
        tuple[key_value, source_name] where source_name is one of:
        - "env"
        - "keyring"
        - "config"
        - "none"
    """
    p_norm = provider.lower().strip()

    # 1. Environment Variable First
    env_val = get_env_key(p_norm)
    if env_val:
        return env_val, "env"

    # 2. Keyring Store Second
    keyring_val = get_keyring_key(p_norm)
    if keyring_val:
        return keyring_val, "keyring"

    # 3. Config File Third
    config_val = get_config_key(p_norm, config=config)
    if config_val:
        return config_val, "config"

    return None, "none"
