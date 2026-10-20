"""Cockpit Shell Router and Command Classifier.

Classifies terminal cockpit input into pure routing directives:
- SWARM_GOAL: Multi-agent swarm objectives
- SHELL_SIMPLE: Safe, non-compound local shell commands
- SHELL_EXPLICIT: Explicit user shell commands (!cmd or $cmd)
- SLASH_COMMAND: Cockpit built-in directives (/help, /model, etc.)
- EMPTY: Whitespace or no-op input

Implements safety gates for:
- Destructive command detection (rm, rmdir, mv, cp -r, chmod -R, sudo, git reset --hard, etc.)
- Parent traversal (..) and out-of-workspace absolute paths
- Compound operator blocking (pipes, redirects, ;, &&, ||, subshells, newlines)
- Disambiguation of natural language goals vs. shell commands
- Command execution with non-blocking confirmation and 64KB output truncation
- Command history logging with 0600 file permissions
- OCTOFLOW_LEGACY_ROUTER=1 escape hatch
"""

import json
import logging
import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger("octoflow.router")


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
    ambiguous: bool = False
    paste_line_count: int = 1


PREFIXES_TO_STRIP: List[str] = [
    "octos ❯", "octos >", "octos:", "octo ❯", "octo >", "❯", ">", "#",
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

ALLOWED_SIMPLE_SHELL_COMMANDS: Set[str] = {
    "mkdir", "touch", "ls", "pwd", "cat", "open", "rm", "cp", "mv",
    "echo", "which", "find", "grep", "curl", "chmod", "kill", "ps", "cd", "git", "rmdir"
}

DESTRUCTIVE_COMMANDS: Set[str] = {
    "rm", "rmdir", "mv", "chown", "dd", "mkfs", "sudo"
}

PROSE_CHECK_COMMANDS: Set[str] = {
    "mkdir", "touch", "rm", "ls", "cd", "cat", "open", "find", "grep", "make"
}

# English prose stopwords indicating natural-language intent rather than shell arguments
PROSE_WORDS: Set[str] = {
    "a", "an", "the", "my", "your", "our", "all", "some", "any", "this", "that",
    "these", "those", "up", "down", "in", "out", "on", "off", "for", "with",
    "about", "to", "from", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "code", "requirements",
    "issues", "analyzer", "files", "everything", "something", "project", "app",
    "model", "data", "test", "please", "can", "could", "would", "should", "want",
    "need", "like", "me", "us", "them", "it", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "and", "or",
    "but", "if", "because", "as", "until", "while", "of", "at", "by"
}

COMPOUND_REGEX = re.compile(r"(\|{1,2}|&&|;|`|\$\(|\r|\n|>|<|&)")

# Maximum captured shell output size (64 KB)
MAX_CAPTURE_BYTES = 64 * 1024

# In-memory session command history
SESSION_COMMAND_HISTORY: List[Dict[str, Any]] = []


def strip_prompt_prefixes(line: str) -> str:
    """Strip accidental copy-pasted prompt prefixes (e.g. 'octos ❯', etc.)."""
    cleaned = line.strip()
    while True:
        prev_len = len(cleaned)
        for prefix in PREFIXES_TO_STRIP:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        if len(cleaned) == prev_len:
            break
    return cleaned


def has_compound_operators(command: str) -> bool:
    """Check if command contains shell chaining, pipes, redirects, or substitution operators outside quotes."""
    in_single = False
    in_double = False
    escaped = False

    i = 0
    n = len(command)
    while i < n:
        c = command[i]
        if escaped:
            escaped = False
            i += 1
            continue

        if c == "\\":
            escaped = True
            i += 1
            continue

        if c == "'" and not in_double:
            in_single = not in_single
            i += 1
            continue

        if c == '"' and not in_single:
            in_double = not in_double
            i += 1
            continue

        if not in_single and not in_double:
            # Check compound operators: ;, \n, \r, `, &, |, >, <, $(
            if c in [";", "\n", "\r", "`"]:
                return True
            if c in ["&", "|", ">", "<"]:
                return True
            if c == "$" and i + 1 < n and command[i + 1] == "(":
                return True

        i += 1

    return False


def is_prose_argument(token: str) -> bool:
    """Check if an argument token resembles English prose rather than a path, flag, or identifier."""
    clean = token.lower().strip(".,:;!?'\"")
    return clean in PROSE_WORDS


def is_destructive_command(
    command: str,
    argv: Optional[List[str]] = None,
    workspace: Optional[Union[str, Path]] = None,
) -> Tuple[bool, str]:
    """Evaluates whether a command contains destructive operations requiring y/N confirmation.

    Returns (is_destructive, reason).
    """
    cmd = command.strip()
    tokens = argv if argv is not None else cmd.split()
    if not tokens:
        return False, ""

    # Clean tokens for inspection (stripping chaining punctuation)
    cleaned_tokens = [t.strip(";;&|`$()'\"") for t in tokens if t.strip(";;&|`$()'\"")]
    if not cleaned_tokens:
        return False, ""

    head = cleaned_tokens[0].lower()

    # 1. Base destructive commands (checked at head and across all tokens for compound commands)
    for t in cleaned_tokens:
        t_low = t.lower()
        if t_low in DESTRUCTIVE_COMMANDS or t_low.startswith("mkfs."):
            return True, f"command contains '{t_low}' which modifies or deletes filesystem resources"

    # 2. Recursive copy: cp -r, cp -R, cp --recursive
    if "cp" in [t.lower() for t in cleaned_tokens]:
        cp_idx = [t.lower() for t in cleaned_tokens].index("cp")
        for t in cleaned_tokens[cp_idx + 1:]:
            if t in ["-r", "-R", "--recursive"] or (t.startswith("-") and ("r" in t or "R" in t)):
                return True, "recursive copy ('cp -r') may overwrite files"

    # 3. Recursive permissions: chmod -R
    if "chmod" in [t.lower() for t in cleaned_tokens]:
        chmod_idx = [t.lower() for t in cleaned_tokens].index("chmod")
        for t in cleaned_tokens[chmod_idx + 1:]:
            if t in ["-R", "--recursive"] or (t.startswith("-") and "R" in t):
                return True, "recursive permissions ('chmod -R') modifies filesystem permissions"

    # 4. Destructive Git commands
    for idx, t in enumerate(cleaned_tokens):
        if t.lower() == "git" and idx + 1 < len(cleaned_tokens):
            git_sub = cleaned_tokens[idx + 1].lower()
            git_args = [x.lower() for x in cleaned_tokens[idx + 2:]]

            if git_sub == "reset" and ("--hard" in git_args):
                return True, "'git reset --hard' discards uncommitted workspace changes"

            if git_sub == "clean":
                return True, "'git clean' permanently removes untracked files"

            if git_sub == "push" and any(a in ["--force", "-f", "--force-with-lease"] for a in git_args):
                return True, "'git push --force' overwrites remote history"

            if git_sub in ["checkout", "restore"] and any(a in [".", "-- .", "-f", "--force"] for a in git_args):
                return True, f"'git {git_sub} .' discards working tree modifications"

            if git_sub == "branch" and any(a in ["-d", "-D", "--delete"] for a in git_args):
                return True, "'git branch -D' deletes a repository branch"

    # 5. Parent directory traversal (..)
    for t in cleaned_tokens[1:]:
        if t == ".." or "/../" in t or t.startswith("../") or t.endswith("/.."):
            return True, f"argument '{t}' traverses parent directory ('..')"

    # 6. Absolute path outside active workspace
    ws_path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    for t in cleaned_tokens[1:]:
        if t.startswith("/") or t.startswith("~"):
            try:
                resolved = Path(os.path.expanduser(t)).resolve()
                # Check if target is outside active workspace
                if not (resolved == ws_path or ws_path in resolved.parents):
                    return True, f"path '{t}' points outside active workspace '{ws_path}'"
            except Exception:
                return True, f"unresolvable path argument '{t}'"

    return False, ""


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
    if first_tok in ALLOWED_SIMPLE_SHELL_COMMANDS:
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


def classify_input(
    line: str,
    workspace: Optional[Union[str, Path]] = None,
    is_multiline_paste: bool = False,
    paste_line_count: int = 1,
) -> Route:
    """Pure classifier routing terminal input into Swarm Goal, Simple Shell, Explicit Shell, or Slash Command.

    Enforces:
    - P1.3 Safe Routing: No compound execution without confirmation.
    - Destructive command safety with y/N confirmation.
    - Disambiguation of prose goals ('make a resume analyzer', 'list the requirements') from shell commands.
    - Multi-line bracketed-paste protection.
    - Deprecated legacy escape hatch via OCTOFLOW_LEGACY_ROUTER=1.
    """
    raw_input = line

    # 1. Legacy router escape hatch
    if os.getenv("OCTOFLOW_LEGACY_ROUTER") == "1":
        logger.warning("[DEPRECATION] OCTOFLOW_LEGACY_ROUTER=1 is active. This unhardened fallback is deprecated and will be removed in a future release.")
        return classify_input_legacy(line, workspace=workspace)

    # 2. Check for empty input
    cleaned = strip_prompt_prefixes(line)
    if not cleaned:
        return Route(kind=RouteKind.EMPTY, raw_input=raw_input, reason="empty input")

    # 3. Handle multi-line pasted content (Task 6)
    has_newlines = ("\n" in line or "\r" in line)
    effective_multiline = is_multiline_paste or has_newlines
    effective_line_count = paste_line_count if paste_line_count > 1 else (len(line.splitlines()) if has_newlines else 1)

    if effective_multiline and effective_line_count > 1:
        if cleaned.startswith("!") or cleaned.startswith("$"):
            cmd = cleaned[1:].strip()
            is_dest, dest_reason = is_destructive_command(cmd, workspace=workspace)
            return Route(
                kind=RouteKind.SHELL_EXPLICIT,
                command=cmd,
                argv=cmd.split(),
                destructive=is_dest,
                compound=True,
                reason=f"multi-line pasted explicit command ({effective_line_count} lines)",
                raw_input=raw_input,
                needs_confirmation=True,
                paste_line_count=effective_line_count,
            )
        else:
            # Multi-line text without explicit ! prefix is treated as a single SWARM_GOAL
            return Route(
                kind=RouteKind.SWARM_GOAL,
                command=cleaned,
                argv=[],
                destructive=False,
                compound=True,
                reason=f"multi-line paste treated as swarm goal ({effective_line_count} lines)",
                raw_input=raw_input,
                needs_confirmation=False,
                paste_line_count=effective_line_count,
            )

    # 4. Explicit shell commands (! or $) (Task 3)
    if cleaned.startswith("!") or cleaned.startswith("$"):
        cmd = cleaned[1:].strip()
        if not cmd:
            return Route(kind=RouteKind.EMPTY, raw_input=raw_input, reason="empty explicit shell command")

        is_comp = has_compound_operators(cmd)
        try:
            parsed_argv = shlex.split(cmd)
        except Exception:
            parsed_argv = cmd.split()
            is_comp = True

        is_dest, dest_reason = is_destructive_command(cmd, argv=parsed_argv, workspace=workspace)
        return Route(
            kind=RouteKind.SHELL_EXPLICIT,
            command=cmd,
            argv=parsed_argv,
            destructive=is_dest,
            compound=is_comp,
            reason="explicit shell command (! or $ prefix)" + (f": {dest_reason}" if is_dest else ""),
            raw_input=raw_input,
            needs_confirmation=True,  # Explicit shell commands ALWAYS require confirmation
        )

    # 5. Explicit /sh or /bash commands
    if cleaned.startswith("/sh ") or cleaned.startswith("/bash "):
        cmd = cleaned.split(maxsplit=1)[1].strip()
        is_comp = has_compound_operators(cmd)
        try:
            parsed_argv = shlex.split(cmd)
        except Exception:
            parsed_argv = cmd.split()
            is_comp = True

        is_dest, dest_reason = is_destructive_command(cmd, argv=parsed_argv, workspace=workspace)
        return Route(
            kind=RouteKind.SHELL_EXPLICIT,
            command=cmd,
            argv=parsed_argv,
            destructive=is_dest,
            compound=is_comp,
            reason="explicit /sh or /bash command" + (f": {dest_reason}" if is_dest else ""),
            raw_input=raw_input,
            needs_confirmation=True,
        )

    # 6. Slash commands
    if cleaned.startswith("/"):
        parts = cleaned.split()
        return Route(
            kind=RouteKind.SLASH_COMMAND,
            command=cleaned,
            argv=parts,
            destructive=False,
            compound=False,
            reason="slash command",
            raw_input=raw_input,
            needs_confirmation=False,
        )

    first_word = cleaned.split()[0].lower() if cleaned.split() else ""
    if first_word in KNOWN_SLASH_COMMANDS:
        return Route(
            kind=RouteKind.SLASH_COMMAND,
            command="/" + cleaned,
            argv=["/" + cleaned.split()[0]] + cleaned.split()[1:],
            destructive=False,
            compound=False,
            reason="auto-normalized slashless command",
            raw_input=raw_input,
            needs_confirmation=False,
        )

    # 7. Simple shell command classification (Task 2)
    first_token = first_word.rstrip(";;&|").lower()

    if first_token not in ALLOWED_SIMPLE_SHELL_COMMANDS:
        # Commands not matching allowed shell commands route to SWARM_GOAL (e.g. "make a resume analyzer", "list the requirements")
        return Route(
            kind=RouteKind.SWARM_GOAL,
            command=cleaned,
            argv=[],
            destructive=False,
            compound=False,
            reason="natural language swarm objective",
            raw_input=raw_input,
            needs_confirmation=False,
        )

    # Check for compound operators (pipes, redirects, ;, &&, ||, subshells)
    is_compound = has_compound_operators(cleaned)
    if is_compound:
        # A compound command matching a shell head is classified as compound explicit shell and requires confirmation
        try:
            parsed_argv = shlex.split(cleaned)
        except Exception:
            parsed_argv = cleaned.split()
        is_dest, dest_reason = is_destructive_command(cleaned, argv=parsed_argv, workspace=workspace)
        return Route(
            kind=RouteKind.SHELL_EXPLICIT,
            command=cleaned,
            argv=parsed_argv,
            destructive=is_dest,
            compound=True,
            reason="compound shell command containing chaining/redirection operators requires confirmation",
            raw_input=raw_input,
            needs_confirmation=True,
        )

    # Parse with shlex as a single command
    try:
        parsed_argv = shlex.split(cleaned)
    except ValueError:
        # Unclosed quotes or syntax error in natural language
        return Route(
            kind=RouteKind.SWARM_GOAL,
            command=cleaned,
            argv=[],
            destructive=False,
            compound=False,
            reason="syntax parse error, routed to swarm goal",
            raw_input=raw_input,
            needs_confirmation=False,
        )

    remaining_tokens = parsed_argv[1:]

    # 8. Prose vs. Argument heuristic (Task 2)
    # For mkdir, touch, rm, ls, cd, cat, open, find, grep: verify remaining tokens look like paths/flags, not prose
    if first_token in PROSE_CHECK_COMMANDS and remaining_tokens:
        prose_hits = [t for t in remaining_tokens if is_prose_argument(t)]
        if prose_hits:
            return Route(
                kind=RouteKind.SWARM_GOAL,
                command=cleaned,
                argv=[],
                destructive=False,
                compound=False,
                reason=f"argument '{prose_hits[0]}' matches natural language prose, routed to swarm goal",
                raw_input=raw_input,
                needs_confirmation=False,
            )

        # If there are > 2 remaining arguments without flags or path characters (e.g. touch user profile card)
        non_flag_non_path = [
            t for t in remaining_tokens
            if not t.startswith("-") and "/" not in t and "\\" not in t and "." not in t
        ]
        if len(non_flag_non_path) >= 3:
            return Route(
                kind=RouteKind.SWARM_GOAL,
                command=cleaned,
                argv=[],
                destructive=False,
                compound=False,
                reason="multiple plain word arguments detected, routed to swarm goal",
                raw_input=raw_input,
                needs_confirmation=False,
            )

    # 9. Destructive check for SHELL_SIMPLE
    is_dest, dest_reason = is_destructive_command(cleaned, argv=parsed_argv, workspace=workspace)

    return Route(
        kind=RouteKind.SHELL_SIMPLE,
        command=cleaned,
        argv=parsed_argv,
        destructive=is_dest,
        compound=False,
        reason=f"simple shell command: {first_token}" + (f" ({dest_reason})" if is_dest else ""),
        raw_input=raw_input,
        needs_confirmation=is_dest,
    )


def log_command_history(
    command: str,
    workspace: Optional[Union[str, Path]] = None,
    success: bool = True,
    kind: str = "SHELL",
) -> None:
    """Logs executed command with timestamp in memory and ~/.octoflow/history (mode 0600)."""
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": now,
        "time": time.time(),
        "kind": kind,
        "command": command,
        "workspace": str(workspace) if workspace else str(Path.cwd()),
        "success": success,
    }
    SESSION_COMMAND_HISTORY.append(record)

    try:
        hist_dir = Path.home() / ".octoflow"
        hist_dir.mkdir(parents=True, exist_ok=True)
        hist_file = hist_dir / "history"

        # Ensure file exists with 0600 permissions before appending
        if not hist_file.exists():
            hist_file.touch(mode=0o600)
        else:
            try:
                os.chmod(hist_file, 0o600)
            except Exception:
                pass

        with open(hist_file, "a", encoding="utf-8") as f:
            f.write(f"{now} | {record['workspace']} | {command}\n")

        try:
            os.chmod(hist_file, 0o600)
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"Could not persist command history to ~/.octoflow/history: {e}")


def execute_shell_route(
    route: Route,
    workspace: Union[str, Path],
    timeout: int = 60,
) -> Tuple[int, str, str]:
    """Executes a classified shell route with 64KB output truncation and safety enforcement.

    - SHELL_SIMPLE: executed with shell=False using argv.
    - SHELL_EXPLICIT: executed with shell=True only after confirmation.
    - Captures stdout/stderr and truncates to 64 KB.
    - Logs execution to history.
    """
    ws = Path(workspace).resolve()

    if route.kind == RouteKind.SHELL_SIMPLE:
        argv = route.argv if route.argv else shlex.split(route.command)
        res = subprocess.run(
            argv,
            shell=False,
            cwd=str(ws),
            timeout=timeout,
            capture_output=True,
            text=True,
        )
    elif route.kind == RouteKind.SHELL_EXPLICIT:
        res = subprocess.run(
            route.command,
            shell=True,
            cwd=str(ws),
            timeout=timeout,
            capture_output=True,
            text=True,
        )
    else:
        raise ValueError(f"Cannot execute non-shell route kind: {route.kind}")

    stdout = res.stdout or ""
    stderr = res.stderr or ""

    # Truncate to 64 KB
    if len(stdout.encode("utf-8", errors="ignore")) > MAX_CAPTURE_BYTES:
        stdout = stdout[:MAX_CAPTURE_BYTES] + "\n... [OUTPUT TRUNCATED AT 64 KB] ..."
    if len(stderr.encode("utf-8", errors="ignore")) > MAX_CAPTURE_BYTES:
        stderr = stderr[:MAX_CAPTURE_BYTES] + "\n... [STDERR TRUNCATED AT 64 KB] ..."

    success = (res.returncode == 0)
    log_command_history(route.command, workspace=ws, success=success, kind=route.kind.value)

    return res.returncode, stdout, stderr
