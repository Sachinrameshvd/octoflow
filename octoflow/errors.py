"""Canonical error hierarchy and exception taxonomy for OctoFlow.

Standardized format: message + optional hint + exit code.
Exit code contract:
- 0: Success
- 1: Generic runtime error, ToolError, WorkspaceError, BudgetExceeded
- 2: ProviderError family (ProviderAuthError, ProviderRateLimitError, ProviderExhaustedError, etc.)
- 3: ConfigError, UsageError
- 70: Internal unexpected fatal error
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional


def redact_secrets(text: Optional[str]) -> str:
    """Sanitize secrets, API keys, and Bearer tokens from text, exceptions, and logs."""
    if not text:
        return ""
    text = str(text)
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


class OctoFlowError(Exception):
    """Base exception for all OctoFlow operational and runtime errors.

    Attributes:
        message: Primary user-facing description of what failed.
        hint: Actionable advice instructing the user how to fix it.
        exit_code: Standardized process exit code (default 1).
    """

    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        exit_code: int = 1,
    ):
        self.message = redact_secrets(message)
        self.hint = redact_secrets(hint) if hint else None
        self.exit_code = exit_code
        full_msg = self.message
        if self.hint:
            full_msg += f"\nHint: {self.hint}"
        super().__init__(full_msg)

    def format_one_liner(self) -> str:
        """Single line representation for concise reporting."""
        msg = f"Error: {self.message}"
        if self.hint:
            msg += f" (Hint: {self.hint})"
        return msg

    def format_cli(self) -> str:
        """Format the error and hint for CLI display in standard style."""
        prefix = "" if self.message.startswith("Error:") else "Error: "
        lines = [f"{prefix}{self.message}"]
        if self.hint:
            lines.append(f"Hint: {self.hint}")
        return "\n".join(lines)


class ConfigError(OctoFlowError):
    """Configuration error: invalid schema, bad keys, or corrupted file (exit 3)."""

    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        exit_code: int = 3,
        loc: Optional[str] = None,
    ):
        self.loc = loc or ""
        clean_msg = message
        if loc and not message.startswith(f"Configuration error in '{loc}'"):
            clean_msg = f"Configuration error in '{loc}': {message}"
        super().__init__(clean_msg, hint=hint, exit_code=exit_code)


# Alias for compatibility with P2.3 settings module
ConfigurationError = ConfigError


class UsageError(OctoFlowError):
    """CLI syntax, flag, or argument usage error (exit 3)."""

    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        exit_code: int = 3,
    ):
        super().__init__(message, hint=hint, exit_code=exit_code)


class ToolError(OctoFlowError):
    """Sandbox tool execution, confinement, or timeout error (exit 1)."""

    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        exit_code: int = 1,
        tool_name: Optional[str] = None,
    ):
        self.tool_name = tool_name
        super().__init__(message, hint=hint, exit_code=exit_code)


class WorkspaceError(OctoFlowError):
    """Workspace boundary escape, permission, or missing directory error (exit 1)."""

    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        exit_code: int = 1,
        path: Optional[str] = None,
    ):
        self.path = path
        super().__init__(message, hint=hint, exit_code=exit_code)


class BudgetExceeded(OctoFlowError):
    """Execution budget limit reached (exit 1). Placeholder for P3.5."""

    def __init__(
        self,
        message: str = "Mission execution budget limit exceeded.",
        hint: Optional[str] = "Increase max budget with --budget or adjust max_budget_dollars in ~/.octoflow/config.json",
        exit_code: int = 1,
        budget: Optional[float] = None,
        cost: Optional[float] = None,
    ):
        self.budget = budget
        self.cost = cost
        super().__init__(message, hint=hint, exit_code=exit_code)


# -----------------------------------------------------------------------------
# Provider Error Family (Re-parented P1.2 classes with exit code 2)
# -----------------------------------------------------------------------------

class ProviderError(OctoFlowError):
    """Base error for all LLM provider failures (exit code 2)."""

    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        exit_code: int = 2,
        provider: str = "unknown",
        status: Optional[int] = None,
        **kwargs: Any,
    ):
        # Support legacy positional / keyword arguments
        if "hint" in kwargs and hint is None:
            hint = kwargs.pop("hint")
        if "provider" in kwargs and provider == "unknown":
            provider = kwargs.pop("provider")
        if "status" in kwargs and status is None:
            status = kwargs.pop("status")

        self.provider = provider
        self.status = status
        self.raw_message = message

        clean_msg = redact_secrets(message)
        clean_hint = redact_secrets(hint) if hint else ""

        full_msg = f"[{provider}]"
        if status is not None:
            full_msg += f" (HTTP {status})"
        full_msg += f" {clean_msg}"

        super().__init__(full_msg, hint=clean_hint if clean_hint else None, exit_code=exit_code)


class ProviderAuthError(ProviderError):
    """Authentication or authorization failure: 401, 403, or invalid API key."""
    pass


class ProviderRateLimitError(ProviderError):
    """Rate limit or quota exhaustion: 429 error honoring Retry-After headers."""

    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        exit_code: int = 2,
        provider: str = "unknown",
        status: Optional[int] = 429,
        retry_after: Optional[float] = None,
        **kwargs: Any,
    ):
        self.retry_after = retry_after
        super().__init__(
            message,
            hint=hint,
            exit_code=exit_code,
            provider=provider,
            status=status,
            **kwargs,
        )


class ProviderTransientError(ProviderError):
    """Transient service disruptions: 5xx errors, timeouts, and network drops."""
    pass


class ProviderRequestError(ProviderError):
    """Client request errors: 4xx errors, invalid payload, or context window exceeded."""
    pass


class ProviderUnavailableError(ProviderError):
    """Daemon or endpoint unavailable: Ollama daemon offline or model missing."""
    pass


class ProviderExhaustedError(ProviderError):
    """Raised when all configured LLM providers fail or credentials exhausted."""

    def __init__(
        self,
        message: str,
        failures: Optional[List[Dict[str, Any]]] = None,
        hint: Optional[str] = None,
        exit_code: int = 2,
    ):
        self.failures = failures or []
        formatted_failures = []
        for f in self.failures:
            cls_name = f.get("error_class") or "ProviderError"
            prov = f.get("provider") or f.get("name") or "unknown"
            f_hint = f.get("hint") or ""
            reason = f.get("reason") or "Failed"
            entry = f"• [{prov}] {cls_name}: {reason}"
            if f_hint:
                entry += f" (Hint: {f_hint})"
            formatted_failures.append(entry)

        full_msg = message
        if formatted_failures and "\n• [" not in message:
            full_msg += "\n" + "\n".join(formatted_failures)

        super().__init__(
            full_msg,
            hint=hint or "Check API keys in ~/.octoflow/config.json or pass --dry-run for mock simulation.",
            exit_code=exit_code,
            provider="all",
        )
