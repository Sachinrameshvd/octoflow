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
from typing import Any


def redact_secrets(text: str | None) -> str:
    """Sanitize secrets, API keys, and Bearer tokens from text, exceptions, and logs."""
    if not text:
        return ""
    text = str(text)
    # Authorization header with Bearer token (e.g. Authorization: Bearer <token>)
    text = re.sub(
        r"Authorization:\s*Bearer\s+\S+",
        "Authorization: Bearer [REDACTED_TOKEN]",
        text,
        flags=re.IGNORECASE,
    )
    # Standalone Bearer tokens (e.g. Bearer <token>)
    text = re.sub(
        r"(?<!Authorization:\s)(?<!Authorization:)\bBearer\s+[a-zA-Z0-9_\-\.]{10,}",
        "Bearer [REDACTED_TOKEN]",
        text,
        flags=re.IGNORECASE,
    )
    # Non-bearer Authorization header values (e.g. Basic, Token, etc.)
    text = re.sub(
        r"Authorization:\s*(?!\s*Bearer\s+\[REDACTED_TOKEN\])[^\r\n]+",
        "Authorization: [REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    # API keys: Anthropic, OpenAI, Grok, etc. (sk-...)
    text = re.sub(r"sk-[a-zA-Z0-9_\-]{16,}", "[REDACTED_KEY]", text)
    # Google AI keys (AIza...)
    text = re.sub(r"AIza[0-9A-Za-z\-_]{30,}", "[REDACTED_KEY]", text)
    # GitHub personal access tokens
    text = re.sub(r"(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{20,}", "[REDACTED_GITHUB_TOKEN]", text)
    # Key-value query/header assignments
    text = re.sub(
        r'(api_key|apikey|key|token|secret|password)=([^\s&"\']+)',
        r"\1=[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    return text


class OctoFlowError(Exception):
    """Base exception for all OctoFlow operational and runtime errors.

    Attributes:
        message: Primary user-facing description of what failed.
        hint: Actionable advice instructing the user how to fix it.
        exit_code: Standardized process exit code (default 1).
        code: Stable catalog error code (default E-GENERAL).
    """

    code: str = "E-GENERAL"
    default_exit_code: int = 1

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        exit_code: int = 1,
        code: str | None = None,
    ):
        self.message = redact_secrets(message)
        self.hint = redact_secrets(hint) if hint else None
        self.exit_code = exit_code
        if code:
            self.code = code
        full_msg = self.message
        if self.hint:
            full_msg += f"\nHint: {self.hint}"
        super().__init__(full_msg)

    def format_one_liner(self) -> str:
        """Single line representation for concise reporting."""
        prefix = f"{self.code}: " if self.code else "Error: "
        msg = f"{prefix}{self.message}"
        if self.hint:
            msg += f" (Hint: {self.hint})"
        return msg

    def format_cli(self) -> str:
        """Format the error and hint for CLI display in standard style."""
        code_prefix = f"{self.code} " if self.code else ""
        clean_msg = self.message
        if clean_msg.startswith(f"{self.code} "):
            msg_line = clean_msg
        else:
            msg_line = f"{code_prefix}{clean_msg}"
        lines = [msg_line]
        if self.hint:
            lines.append(f"Hint: {self.hint}")
        return "\n".join(lines)


class ConfigError(OctoFlowError):
    """Configuration error: invalid schema, bad keys, or corrupted file (exit 3)."""

    code = "E-CONFIG-INVALID"
    default_exit_code = 3

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        exit_code: int = 3,
        loc: str | None = None,
        code: str | None = None,
    ):
        self.loc = loc or ""
        clean_msg = message
        if loc and not message.startswith(f"Configuration error in '{loc}'"):
            clean_msg = f"Configuration error in '{loc}': {message}"
        super().__init__(clean_msg, hint=hint, exit_code=exit_code, code=code or self.code)


# Alias for compatibility with P2.3 settings module
ConfigurationError = ConfigError


class UsageError(OctoFlowError):
    """CLI syntax, flag, or argument usage error (exit 3)."""

    code = "E-USAGE-INVALID"
    default_exit_code = 3

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        exit_code: int = 3,
        code: str | None = None,
    ):
        super().__init__(message, hint=hint, exit_code=exit_code, code=code or self.code)


class ToolError(OctoFlowError):
    """Sandbox tool execution, confinement, or timeout error (exit 1)."""

    code = "E-TOOL-DENIED"
    default_exit_code = 1

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        exit_code: int = 1,
        tool_name: str | None = None,
        code: str | None = None,
    ):
        self.tool_name = tool_name
        super().__init__(message, hint=hint, exit_code=exit_code, code=code or self.code)


class WorkspaceError(OctoFlowError):
    """Workspace boundary escape, permission, or missing directory error (exit 1)."""

    code = "E-WORKSPACE-ESCAPE"
    default_exit_code = 1

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        exit_code: int = 1,
        path: str | None = None,
        code: str | None = None,
    ):
        self.path = path
        super().__init__(message, hint=hint, exit_code=exit_code, code=code or self.code)


class GitError(OctoFlowError):
    """Git repository missing or Git operation failed (exit 1)."""

    code = "E-NOGIT"
    default_exit_code = 1

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        exit_code: int = 1,
        code: str | None = None,
    ):
        super().__init__(
            message,
            hint=hint or "Run 'git init' to initialize version control or run 'octoflow doctor --fix'.",
            exit_code=exit_code,
            code=code or self.code,
        )


class BudgetExceeded(OctoFlowError):
    """Execution budget limit reached (exit 1)."""

    code = "E-BUDGET"
    default_exit_code = 1

    def __init__(
        self,
        limit_name: str = "budget",
        used: Any | None = None,
        limit: Any | None = None,
        message: str | None = None,
        hint: str | None = None,
        exit_code: int = 1,
        budget: float | None = None,
        cost: float | None = None,
        code: str | None = None,
    ):
        self.limit_name = limit_name
        self.used = used
        self.limit = limit
        self.budget = budget or limit
        self.cost = cost or used

        if message is None:
            if used is not None and limit is not None:
                message = f"Budget limit '{limit_name}' exceeded: {used}/{limit}."
            else:
                message = f"Budget limit exceeded: {limit_name}."

        if hint is None:
            hint = f"Increase {limit_name} limit via CLI flags (--max-tokens, --max-calls, --timeout, --max-heal) or use --no-limits."

        super().__init__(message, hint=hint, exit_code=exit_code, code=code or self.code)


# -----------------------------------------------------------------------------
# Provider Error Family (Re-parented P1.2 classes with exit code 2)
# -----------------------------------------------------------------------------


class ProviderError(OctoFlowError):
    """Base error for all LLM provider failures (exit code 2)."""

    code = "E-PROV-FAILED"
    default_exit_code = 2

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        exit_code: int = 2,
        provider: str = "unknown",
        status: int | None = None,
        code: str | None = None,
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

        super().__init__(
            full_msg,
            hint=clean_hint if clean_hint else None,
            exit_code=exit_code,
            code=code or self.code,
        )


class ProviderAuthError(ProviderError):
    """Authentication or authorization failure: 401, 403, or invalid API key."""

    code = "E-PROV-AUTH"
    default_exit_code = 2


class ProviderRateLimitError(ProviderError):
    """Rate limit or quota exhaustion: 429 error honoring Retry-After headers."""

    code = "E-PROV-RATE"
    default_exit_code = 2

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        exit_code: int = 2,
        provider: str = "unknown",
        status: int | None = 429,
        retry_after: float | None = None,
        code: str | None = None,
        **kwargs: Any,
    ):
        self.retry_after = retry_after
        super().__init__(
            message,
            hint=hint,
            exit_code=exit_code,
            provider=provider,
            status=status,
            code=code or self.code,
            **kwargs,
        )


class ProviderTransientError(ProviderError):
    """Transient service disruptions: 5xx errors, timeouts, and network drops."""

    code = "E-PROV-TRANSIENT"
    default_exit_code = 2


class ProviderRequestError(ProviderError):
    """Client request errors: 4xx errors, invalid payload, or context window exceeded."""

    code = "E-PROV-REQUEST"
    default_exit_code = 2


class ProviderUnavailableError(ProviderError):
    """Daemon or endpoint unavailable: Ollama daemon offline or model missing."""

    code = "E-OLLAMA-DOWN"
    default_exit_code = 2


class ProviderExhaustedError(ProviderError):
    """Raised when all configured LLM providers fail or credentials exhausted."""

    code = "E-PROV-EXHAUSTED"
    default_exit_code = 2

    def __init__(
        self,
        message: str,
        failures: list[dict[str, Any]] | None = None,
        hint: str | None = None,
        exit_code: int = 2,
        code: str | None = None,
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
            hint=hint
            or "Check API keys in ~/.octoflow/config.json or pass --dry-run for mock simulation.",
            exit_code=exit_code,
            provider="all",
            code=code or self.code,
        )
