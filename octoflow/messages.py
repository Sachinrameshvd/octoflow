"""Canonical error message catalog, empty states, and UX help strings for OctoFlow.

P6.2 UX Standard:
- Every error message states cause in plain language, consequence, and concrete next step command.
- Standard prefix: E-XXXX message + hint on next line.
- Empty states: one friendly line + one command to try.
- Plain-language help summary + metaphor glossary.
- Unknown command suggestions via difflib.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from octoflow.errors import (
    BudgetExceeded,
    ConfigError,
    ConfigurationError,
    GitError,
    OctoFlowError,
    ProviderAuthError,
    ProviderError,
    ProviderExhaustedError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderTransientError,
    ProviderUnavailableError,
    ToolError,
    UsageError,
    WorkspaceError,
)


@dataclass(frozen=True)
class CatalogEntry:
    """Canonical entry in the OctoFlow error catalog."""

    code: str
    error_class: type[OctoFlowError]
    title: str
    cause: str
    consequence: str
    next_step: str
    hint: str
    docs_anchor: str

    def format_cli(self, message: str | None = None, hint: str | None = None) -> str:
        """Format as standard CLI two-liner: 'E-XXXX message\\nHint: hint'."""
        msg = message or self.cause
        h = hint or self.hint
        return f"{self.code} {msg}\nHint: {h}"


# -----------------------------------------------------------------------------
# 1. Error Message Catalog
# -----------------------------------------------------------------------------

ERROR_CATALOG: dict[str, CatalogEntry] = {
    "E-PROV-AUTH": CatalogEntry(
        code="E-PROV-AUTH",
        error_class=ProviderAuthError,
        title="Authentication or Authorization Failure",
        cause="The inference provider rejected your credentials (HTTP 401 or 403).",
        consequence="OctoFlow cannot authenticate requests with the selected AI model provider.",
        next_step="Run 'octoflow setup' or export a valid API key (e.g. export ANTHROPIC_API_KEY='sk-...').",
        hint="Run 'octoflow setup' to configure valid credentials or export the required environment variable.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-prov-auth",
    ),
    "E-PROV-RATE": CatalogEntry(
        code="E-PROV-RATE",
        error_class=ProviderRateLimitError,
        title="Provider Rate Limit or Quota Exhaustion",
        cause="The inference provider throttled requests due to rate limits or exhausted account credits (HTTP 429).",
        consequence="Current model requests are paused or rejected until the quota window resets.",
        next_step="Wait for the provider quota reset or switch provider using 'octoflow config set llm_provider ollama'.",
        hint="Wait for your quota window to reset or switch providers using 'octoflow config set llm_provider <name>'.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-prov-rate",
    ),
    "E-OLLAMA-DOWN": CatalogEntry(
        code="E-OLLAMA-DOWN",
        error_class=ProviderUnavailableError,
        title="Local Inference Daemon Offline or Model Missing",
        cause="The local Ollama service is unreachable at http://127.0.0.1:11434 or requested model is missing.",
        consequence="Local model inference cannot proceed.",
        next_step="Start the daemon with 'ollama serve' or pull the model with 'ollama pull qwen2.5-coder:7b'.",
        hint="Run 'ollama serve' to start local inference or run 'ollama pull <model>' to download required weights.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-ollama-down",
    ),
    "E-PROV-TRANSIENT": CatalogEntry(
        code="E-PROV-TRANSIENT",
        error_class=ProviderTransientError,
        title="Transient Provider Network Failure",
        cause="The remote provider experienced a temporary server error (HTTP 5xx), connection drop, or network timeout.",
        consequence="The current inference attempt failed after automatic retry attempts.",
        next_step="Check internet connectivity and provider status page, then re-run with 'octoflow run'.",
        hint="Verify network connection and provider service status, then retry the mission.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-prov-transient",
    ),
    "E-PROV-REQUEST": CatalogEntry(
        code="E-PROV-REQUEST",
        error_class=ProviderRequestError,
        title="Invalid Provider Request Payload or Context Exceeded",
        cause="The request payload was rejected (HTTP 4xx) or prompt length exceeded the model's context window.",
        consequence="The model refused the payload and generation was halted.",
        next_step="Reduce workspace context or configure a larger context model with 'octoflow config set model <name>'.",
        hint="Prune large context files or choose a model with a larger context window.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-prov-request",
    ),
    "E-PROV-EXHAUSTED": CatalogEntry(
        code="E-PROV-EXHAUSTED",
        error_class=ProviderExhaustedError,
        title="All Configured Inference Providers Failed",
        cause="All configured LLM providers in the fallback cascade failed or had exhausted credentials.",
        consequence="OctoFlow cannot complete autonomous code generation.",
        next_step="Run 'octoflow setup' to configure working provider credentials or pass '--dry-run' for mock simulation.",
        hint="Configure healthy inference credentials with 'octoflow setup' or test with '--dry-run'.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-prov-exhausted",
    ),
    "E-PROV-FAILED": CatalogEntry(
        code="E-PROV-FAILED",
        error_class=ProviderError,
        title="Inference Provider Generic Failure",
        cause="An unclassified operational error occurred while communicating with the AI model provider.",
        consequence="Model inference failed and swarm generation stopped.",
        next_step="Inspect logs in ~/.octoflow/logs/octoflow.log or re-run with '--trace'.",
        hint="Run 'octoflow doctor' to diagnose environment health or run with '--trace'.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-prov-failed",
    ),
    "E-CONFIG-INVALID": CatalogEntry(
        code="E-CONFIG-INVALID",
        error_class=ConfigError,
        title="Invalid or Corrupted Configuration",
        cause="The settings file ~/.octoflow/config.json contains invalid keys, types, or syntax.",
        consequence="OctoFlow cannot load operational settings.",
        next_step="Inspect settings with 'octoflow config show' or reset configuration with 'octoflow setup'.",
        hint="Run 'octoflow config show' to view current keys or run 'octoflow setup' to regenerate configuration.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-config-invalid",
    ),
    "E-USAGE-INVALID": CatalogEntry(
        code="E-USAGE-INVALID",
        error_class=UsageError,
        title="Invalid Command Line Syntax or Argument",
        cause="An unrecognized command, unknown flag, or invalid argument combination was provided.",
        consequence="The command could not be dispatched.",
        next_step="Run 'octoflow --help' to see valid syntax and available options.",
        hint="Run 'octoflow --help' to inspect valid CLI options and command syntax.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-usage-invalid",
    ),
    "E-TOOL-DENIED": CatalogEntry(
        code="E-TOOL-DENIED",
        error_class=ToolError,
        title="Tool Execution Confinement or Timeout",
        cause="A tool action violated security sandbox policies, exceeded execution timeout, or returned a failure code.",
        consequence="The tool execution was blocked to preserve workspace safety.",
        next_step="Review tool parameters or increase timeout with 'octoflow config set tool_timeout 60'.",
        hint="Review tool security constraints or increase timeout via CLI flags.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-tool-denied",
    ),
    "E-WORKSPACE-ESCAPE": CatalogEntry(
        code="E-WORKSPACE-ESCAPE",
        error_class=WorkspaceError,
        title="Workspace Boundary Confinement Violation",
        cause="A file path operation attempted to access files outside the designated workspace directory.",
        consequence="The operation was blocked to prevent reading or modifying files outside the project root.",
        next_step="Use relative paths within the workspace or specify a target directory with '--dir <path>'.",
        hint="Ensure all file paths stay within the workspace boundary or pass '--dir <path>'.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-workspace-escape",
    ),
    "E-BUDGET": CatalogEntry(
        code="E-BUDGET",
        error_class=BudgetExceeded,
        title="Mission Execution Budget Exceeded",
        cause="The mission exceeded its configured token count, LLM call count, cost ceiling, or wall-clock timeout.",
        consequence="Swarm execution was halted to prevent unintended resource consumption.",
        next_step="Increase limits via '--budget <amount>', '--max-tokens <n>', '--timeout <sec>', or pass '--no-limits'.",
        hint="Increase budget limits via CLI flags (--budget, --max-tokens, --timeout) or pass '--no-limits'.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-budget",
    ),
    "E-NOGIT": CatalogEntry(
        code="E-NOGIT",
        error_class=GitError,
        title="Git Repository Missing or Operation Failed",
        cause="The current workspace is not a Git repository or a Git checkpoint operation failed.",
        consequence="Automatic branch snapshotting and safe rollback cannot be performed.",
        next_step="Initialize version control with 'git init' or run 'octoflow doctor --fix'.",
        hint="Run 'git init' to initialize version control or run 'octoflow doctor --fix'.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-nogit",
    ),
    "E-GENERAL": CatalogEntry(
        code="E-GENERAL",
        error_class=OctoFlowError,
        title="General OctoFlow Operational Error",
        cause="An unexpected operational error occurred during OctoFlow execution.",
        consequence="The requested operation failed.",
        next_step="Inspect logs in ~/.octoflow/logs/octoflow.log or re-run with '--trace'.",
        hint="Run 'octoflow doctor' to diagnose system issues or re-run with '--trace'.",
        docs_anchor="docs/TROUBLESHOOTING.md#e-general",
    ),
}

# Mapping from Exception Class to Catalog Entry
CLASS_TO_ENTRY: dict[type[OctoFlowError], CatalogEntry] = {
    entry.error_class: entry for entry in ERROR_CATALOG.values()
}
# Alias compatibility
CLASS_TO_ENTRY[ConfigurationError] = ERROR_CATALOG["E-CONFIG-INVALID"]


def get_catalog_entry_for_class(exc_cls: type[OctoFlowError]) -> CatalogEntry:
    """Retrieve catalog entry for an exception class, walking MRO if necessary."""
    if exc_cls in CLASS_TO_ENTRY:
        return CLASS_TO_ENTRY[exc_cls]
    for base in exc_cls.__mro__:
        if base in CLASS_TO_ENTRY:
            return CLASS_TO_ENTRY[base]
    return ERROR_CATALOG["E-GENERAL"]


def get_catalog_entry(code_or_cls: str | type[OctoFlowError]) -> CatalogEntry:
    """Lookup catalog entry by code string or exception class."""
    if isinstance(code_or_cls, str):
        if code_or_cls in ERROR_CATALOG:
            return ERROR_CATALOG[code_or_cls]
        raise KeyError(f"Unknown error code '{code_or_cls}'")
    return get_catalog_entry_for_class(code_or_cls)


# -----------------------------------------------------------------------------
# 2. Empty States
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class EmptyState:
    """Structured empty state with friendly message and concrete command."""

    key: str
    friendly_line: str
    command_to_try: str

    def format_cli(self) -> str:
        """Format as friendly plain-text message and command."""
        return f"{self.friendly_line}\nTry: {self.command_to_try}"

    def format_rich(self, theme=None) -> str:
        """Format with rich color styling."""
        primary = theme.rich_primary if theme else "cyan"
        dim_style = "dim"
        return f"[{dim_style}]{self.friendly_line}[/{dim_style}]\nTry: [{primary}]{self.command_to_try}[/{primary}]"


EMPTY_STATES: dict[str, EmptyState] = {
    "no_runs": EmptyState(
        key="no_runs",
        friendly_line="No recorded OctoFlow runs found for this workspace.",
        command_to_try='octoflow "create a hello world script"',
    ),
    "no_memory": EmptyState(
        key="no_memory",
        friendly_line="Vertical Lobe memory is empty; no learned heuristics recorded yet.",
        command_to_try='octoflow run "build feature"',
    ),
    "no_reports": EmptyState(
        key="no_reports",
        friendly_line="No mission reports generated yet for this workspace.",
        command_to_try="octoflow report",
    ),
    "no_providers": EmptyState(
        key="no_providers",
        friendly_line="No LLM inference providers configured.",
        command_to_try="octoflow setup",
    ),
    "no_ollama": EmptyState(
        key="no_ollama",
        friendly_line="Local Ollama daemon is unreachable at http://127.0.0.1:11434.",
        command_to_try="ollama serve",
    ),
    "not_git_repo": EmptyState(
        key="not_git_repo",
        friendly_line="Current workspace directory is not a Git repository.",
        command_to_try="git init",
    ),
    "no_tests_found": EmptyState(
        key="no_tests_found",
        friendly_line="No test suite or testing framework detected in workspace.",
        command_to_try="pytest",
    ),
}


def get_empty_state(key: str) -> EmptyState:
    """Retrieve empty state by key."""
    if key not in EMPTY_STATES:
        raise KeyError(f"Unknown empty state '{key}'. Available: {list(EMPTY_STATES.keys())}")
    return EMPTY_STATES[key]


def format_empty_state(key: str) -> str:
    """Convenience string formatter for an empty state."""
    return get_empty_state(key).format_cli()


# -----------------------------------------------------------------------------
# 3. Plain Language Help & Metaphor Glossary
# -----------------------------------------------------------------------------

PLAIN_LANGUAGE_SUMMARY = (
    "OctoFlow is an autonomous multi-agent coding framework that plans, develops, "
    "and tests software projects using coordinated AI specialists. It combines local "
    "change detection with checkpoint safety to implement goals while keeping you in full control."
)

GLOSSARY: dict[str, str] = {
    "Conductor": "Planner coordinating high-level objectives and task graph execution",
    "Arm": "Specialist agent executing targeted code and test operations",
    "Gate": "Change detector measuring sensory surprise on file edits",
    "Bus": "Message channel enabling low-latency agent-to-agent events",
    "Vertical Lobe": "Memory system retaining heuristics and learned patterns across runs",
}


def render_glossary_table(console: Console | None = None) -> Table:
    """Create a rich Table presenting the metaphor glossary in plain language."""
    table = Table(title="◈ OctoFlow Architecture Glossary", border_style="cyan")
    table.add_column("Metaphor", style="bold cyan", width=18)
    table.add_column("Plain Language Meaning", style="white")

    for metaphor, meaning in GLOSSARY.items():
        table.add_row(metaphor, meaning)
    return table


def get_glossary_text() -> str:
    """Plain-text formatted glossary string."""
    lines = [
        "◈ OctoFlow Architecture Glossary",
        "",
        "Metaphor          Plain Language Meaning",
        "─" * 16 + "  " + "─" * 60,
    ]
    for term, definition in GLOSSARY.items():
        lines.append(f"{term:<16}  {definition}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# 4. Command Suggestions via difflib
# -----------------------------------------------------------------------------


def suggest_command(
    entered: str,
    valid_commands: Sequence[str],
    n: int = 3,
    cutoff: float = 0.5,
) -> list[str]:
    """Find closest matching commands using difflib."""
    clean = entered.strip()
    return difflib.get_close_matches(clean, valid_commands, n=n, cutoff=cutoff)


def format_unknown_command(entered: str, valid_commands: Sequence[str]) -> str:
    """Format helpful suggestion string for an unknown command or subcommand."""
    matches = suggest_command(entered, valid_commands)
    if matches:
        return f"Unknown command '{entered}'. Did you mean '{matches[0]}'?"
    return f"Unknown command '{entered}'. Type '/help' for a list of available commands."


# -----------------------------------------------------------------------------
# 5. Documentation Generator for docs/reference/errors.md
# -----------------------------------------------------------------------------


def generate_reference_markdown() -> str:
    """Generate Markdown reference documentation for docs/reference/errors.md."""
    lines = [
        "# Error Code Reference",
        "",
        "OctoFlow uses standardized error codes in the format `E-XXXX`. Every error specifies",
        "the plain-language cause, the operational consequence, and a concrete next-step command.",
        "",
        "## Error Catalog Summary",
        "",
        "| Error Code | Class | Exit Code | Title | Docs Anchor |",
        "| :--- | :--- | :---: | :--- | :--- |",
    ]

    for code, entry in sorted(ERROR_CATALOG.items()):
        cls_name = entry.error_class.__name__
        exit_code = getattr(entry.error_class, "default_exit_code", 1)
        lines.append(
            f"| `{entry.code}` | `{cls_name}` | `{exit_code}` | {entry.title} | [{entry.docs_anchor}]({entry.docs_anchor}) |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Error Catalog",
        "",
    ])

    for code, entry in sorted(ERROR_CATALOG.items()):
        cls_name = entry.error_class.__name__
        anchor = entry.code.lower()
        lines.extend([
            f'### <a id="{anchor}"></a>{entry.code} — {entry.title}',
            "",
            f"- **Class**: `{cls_name}`",
            f"- **Troubleshooting Anchor**: [{entry.docs_anchor}]({entry.docs_anchor})",
            f"- **Cause**: {entry.cause}",
            f"- **Consequence**: {entry.consequence}",
            f"- **Next Step**: `{entry.next_step}`",
            "",
            "```text",
            f"{entry.code} {entry.cause}",
            f"Hint: {entry.hint}",
            "```",
            "",
        ])

    return "\n".join(lines)

