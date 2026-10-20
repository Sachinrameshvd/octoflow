"""Cockpit Shell Router and Command Classifier.

Classifies terminal cockpit input into pure routing directives:
- SWARM_GOAL: Multi-agent swarm objectives
- SHELL_SIMPLE: Safe, non-compound local shell commands
- SHELL_EXPLICIT: Explicit user shell commands (!cmd or $cmd)
- SLASH_COMMAND: Cockpit built-in directives (/help, /model, etc.)
- EMPTY: Whitespace or no-op input
"""

import os
import re
import shlex
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set, Union


class RouteKind(str, Enum):
    SWARM_GOAL = "SWARM_GOAL"
    SHELL_SIMPLE = "SHELL_SIMPLE"
    SHELL_EXPLICIT = "SHELL_EXPLICIT"
    SLASH_COMMAND = "SLASH_COMMAND"
    EMPTY = "EMPTY"


@dataclass
class Route:
    kind: RouteKind
    argv: List[str] = field(default_factory=list)
    destructive: bool = False
    compound: bool = False
    reason: str = ""
    command: str = ""
    raw_input: str = ""
    needs_confirmation: bool = False


PREFIXES_TO_STRIP = [
    "octos ❯", "octos >", "octos:", "octo ❯", "octo >", "❯", ">", "$", "#",
    "./octos ", "./octo ", "octos ", "octo ",
]

KNOWN_SLASH_COMMANDS: Set[str] = {
    "help", "manual", "docs", "setup", "doctor", "init", "init-ide",
    "init-action", "ci", "review-pr", "heal", "triage", "notify", "audit",
    "eject", "federation", "install-claude", "plan", "ask", "talk", "theme",
    "model", "octos", "guild", "bench", "monorepo", "record", "runner",
    "guard", "hooks", "rag", "budget", "ignite", "diff", "commit", "rollback",
    "undo", "ui", "memory", "status", "llm", "clear", "exit", "quit",
    "screensaver", "banner", "play"
}

LEGACY_SHELL_COMMANDS: Set[str] = {
    "mkdir", "touch", "ls", "pwd", "cat", "open", "rm", "cp", "mv",
    "echo", "which", "find", "grep", "curl", "chmod", "kill", "ps", "cd"
}


def strip_prompt_prefixes(line: str) -> str:
    """Strip accidental copy-pasted prompt prefixes (e.g. 'octos ❯', '$ ', etc.)."""
    cleaned = line.strip()
    while True:
        prev_len = len(cleaned)
        for prefix in PREFIXES_TO_STRIP:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        if len(cleaned) == prev_len:
            break
    return cleaned


def classify_input_legacy(line: str, workspace: Optional[Union[str, Path]] = None) -> Route:
    """Characterization implementation of the unhardened pre-P1.3 cockpit router."""
    raw = line
    cleaned = strip_prompt_prefixes(line)
    if not cleaned:
        return Route(kind=RouteKind.EMPTY, raw_input=raw, reason="empty input")

    if cleaned.startswith("!") or cleaned.startswith("$"):
        cmd = cleaned[1:].strip()
        return Route(
            kind=RouteKind.SHELL_EXPLICIT,
            command=cmd,
            argv=cmd.split(),
            raw_input=raw,
            reason="explicit shell prefix",
        )

    if cleaned.startswith("/sh ") or cleaned.startswith("/bash "):
        cmd = cleaned.split(maxsplit=1)[1].strip()
        return Route(
            kind=RouteKind.SHELL_EXPLICIT,
            command=cmd,
            argv=cmd.split(),
            raw_input=raw,
            reason="explicit /sh or /bash command",
        )

    first_tok = cleaned.split()[0].lower() if cleaned.split() else ""
    if first_tok in LEGACY_SHELL_COMMANDS:
        return Route(
            kind=RouteKind.SHELL_SIMPLE,
            command=cleaned,
            argv=cleaned.split(),
            raw_input=raw,
            reason=f"legacy shell passthrough for {first_tok}",
        )

    if cleaned.startswith("/"):
        return Route(
            kind=RouteKind.SLASH_COMMAND,
            command=cleaned,
            argv=cleaned.split(),
            raw_input=raw,
            reason="slash command",
        )

    if first_tok in KNOWN_SLASH_COMMANDS:
        return Route(
            kind=RouteKind.SLASH_COMMAND,
            command="/" + cleaned,
            argv=["/" + cleaned.split()[0]] + cleaned.split()[1:],
            raw_input=raw,
            reason="auto-normalized slashless command",
        )

    return Route(
        kind=RouteKind.SWARM_GOAL,
        command=cleaned,
        raw_input=raw,
        reason="natural language swarm objective",
    )


def classify_input(line: str, workspace: Optional[Union[str, Path]] = None) -> Route:
    """Primary entry point for classifying cockpit input.
    
    If OCTOFLOW_LEGACY_ROUTER=1 is set, delegates to legacy router.
    """
    if os.getenv("OCTOFLOW_LEGACY_ROUTER") == "1":
        return classify_input_legacy(line, workspace=workspace)
    return classify_input_legacy(line, workspace=workspace)
