"""Workspace Sandbox & Tool Execution Environment.

Provides safe filesystem and terminal command tools with strict boundary enforcement,
path containment, advisory file locks, command allowlists, timeout process group kills,
controlled environments, and secret redaction.
"""

import asyncio
import contextlib
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

from octoflow.provider import redact_secrets
from octoflow.logging_config import get_logger

logger = get_logger("tools")


class ToolResult(BaseModel):
    """Normalized result of an arm tool execution."""
    tool_name: str
    target: str
    success: bool
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    diff_lines: int = 0
    error: Optional[str] = None


DEFAULT_ALLOWED_COMMANDS: Set[str] = {
    # Core language runtimes, test runners, linters & formatters
    "python", "python3", "pytest", "coverage", "mypy", "ruff", "flake8", "black",
    "node", "npm", "npx", "vite", "cargo", "rustc", "go",
    # Version control
    "git",
    # Safe inspect & text processing tools
    "ls", "cat", "echo", "pwd", "grep", "find", "mkdir", "touch",
    "cp", "mv", "which", "diff", "head", "tail", "wc", "sort", "uniq",
    # Build tools
    "make", "docker",
}

DEFAULT_TIMEOUT_SECONDS: float = 60.0
MAX_TIMEOUT_SECONDS: float = 300.0
MAX_CAPTURE_BYTES: int = 64 * 1024  # 64 KB

SAFE_ENV_PASSTHROUGH: Set[str] = {
    # System execution paths
    "PATH", "SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR",
    # User / Shell info
    "HOME", "USER", "LOGNAME", "SHELL", "TERM",
    # Temporary directory paths
    "TMPDIR", "TEMP", "TMP",
    # Locale & encoding
    "LANG", "LC_ALL", "LC_CTYPE", "LC_MESSAGES", "PYTHONIOENCODING", "PYTHONUTF8",
    # Python & runtime environment
    "PYTHONPATH", "VIRTUAL_ENV", "PYTHONDONTWRITEBYTECODE",
    # Node environment
    "NODE_PATH", "NODE_ENV", "NPM_CONFIG_PREFIX",
    # Cargo / Rust / Go paths
    "CARGO_HOME", "RUSTUP_HOME", "GOPATH", "GOROOT",
    # CI detection flags
    "CI", "GITHUB_ACTIONS",
}


def _is_subpath(target: Path, base: Path) -> bool:
    """Check if target path is strictly within base path."""
    try:
        return target.resolve().is_relative_to(base.resolve())
    except (ValueError, AttributeError):
        try:
            return os.path.commonpath([str(base.resolve()), str(target.resolve())]) == str(base.resolve())
        except ValueError:
            return False


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
            if c in (";", "\n", "\r", "`"):
                return True
            if c in ("&", "|", ">", "<"):
                return True
            if c == "$" and i + 1 < n and command[i + 1] == "(":
                return True

        i += 1

    return False


class WorkspaceSandbox:
    """Safe execution sandbox rooted in a specific workspace directory with optional Docker isolation."""

    def __init__(
        self,
        workspace_dir: str,
        sandbox_mode: str = "local",
        docker_image: str = "python:3.12-slim",
        dry_run: bool = False,
        allowed_commands: Optional[Set[str]] = None,
        default_timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_timeout_seconds: float = MAX_TIMEOUT_SECONDS,
        max_capture_bytes: int = MAX_CAPTURE_BYTES,
        allow_unrestricted: bool = False,
    ):
        self.dry_run = dry_run or (os.getenv("OCTOFLOW_DRY_RUN") == "1")
        self.target_root = Path(workspace_dir).expanduser().resolve()
        if self.dry_run:
            dry_dir = Path.home() / ".octoflow" / "dry-run"
            dry_dir.mkdir(parents=True, exist_ok=True)
            self.root = dry_dir.resolve()
        else:
            self.root = self.target_root
            self.root.mkdir(parents=True, exist_ok=True)
        self.sandbox_mode = sandbox_mode.lower()
        self.docker_image = docker_image
        self.allowed_commands = set(allowed_commands) if allowed_commands is not None else set(DEFAULT_ALLOWED_COMMANDS)
        self.default_timeout_seconds = default_timeout_seconds
        self.max_timeout_seconds = max_timeout_seconds
        self.max_capture_bytes = max_capture_bytes
        self.allow_unrestricted = allow_unrestricted or (os.getenv("OCTOFLOW_UNRESTRICTED_TOOLS") == "1")

        # Advisory locks: file_path_str -> holding_arm_id
        self._locks: Dict[str, int] = {}
        self._lock_mutex = threading.RLock()
        self.files_written: List[str] = []
        self.budget_tracker: Optional[Any] = None

    def set_budget_tracker(self, tracker: Optional[Any]) -> None:
        """Attach a BudgetTracker to enforce file writing limits."""
        self.budget_tracker = tracker

    def _resolve_safe(self, rel_path: str) -> Path:
        """Resolve a relative or absolute path safely within the workspace.

        Enforces:
        - Rejection of null bytes.
        - Canonical resolution against workspace root.
        - Rejection of '..' escaping outside the workspace.
        - Verification that symlinks (including in parent components) do not point outside root.
        - Safe validation of nonexistent destinations via existing parent directories.
        """
        raw_str = str(rel_path)
        if "\x00" in raw_str:
            raise ValueError(f"Null byte injection detected in path: '{repr(raw_str)}'")

        clean_path = raw_str.strip().strip("'\"").replace("\\", "/")
        if not clean_path:
            return self.root

        path_obj = Path(clean_path).expanduser()

        if path_obj.is_absolute():
            resolved = path_obj.resolve()
            if not _is_subpath(resolved, self.root):
                raise ValueError(f"Path traversal detected: '{rel_path}' resolves outside workspace root '{self.root}'")
            # Verify all existing ancestors are also confined
            curr = path_obj
            while curr != self.root and curr != curr.parent:
                if curr.exists():
                    curr_res = curr.resolve()
                    if not _is_subpath(curr_res, self.root):
                        raise ValueError(f"Symlink traversal detected: ancestor '{curr}' resolves outside workspace root '{self.root}'")
                curr = curr.parent
            return resolved

        # For relative paths, remove any leading slashes
        clean_path = clean_path.lstrip("/")
        candidate = self.root / clean_path
        resolved = candidate.resolve()

        if not _is_subpath(resolved, self.root):
            raise ValueError(f"Path traversal detected: '{rel_path}' resolves outside workspace root '{self.root}'")

        # Verify all existing ancestors along the candidate path
        curr = candidate
        while curr != self.root and curr != curr.parent:
            if curr.exists():
                curr_res = curr.resolve()
                if not _is_subpath(curr_res, self.root):
                    raise ValueError(f"Symlink traversal detected: ancestor '{curr}' resolves outside workspace root '{self.root}'")
            curr = curr.parent

        return resolved

    def _get_controlled_environment(self) -> Dict[str, str]:
        """Produce a minimal, sanitized environment for subprocess execution."""
        clean_env: Dict[str, str] = {}
        for var in SAFE_ENV_PASSTHROUGH:
            val = os.environ.get(var)
            if val is not None:
                clean_env[var] = val

        # Ensure PATH includes current Python environment directory
        py_bin = str(Path(sys.executable).parent)
        curr_path = clean_env.get("PATH", os.defpath)
        if py_bin not in curr_path.split(os.pathsep):
            clean_env["PATH"] = f"{py_bin}{os.pathsep}{curr_path}"
        else:
            clean_env["PATH"] = curr_path

        # Explicitly scrub any key that resembles a secret/credential even if in passthrough
        secret_indicators = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH", "APIKEY")
        for k in list(clean_env.keys()):
            upper_k = k.upper()
            if any(ind in upper_k for ind in secret_indicators):
                del clean_env[k]

        return clean_env

    def acquire_lock(self, rel_path: str, arm_id: int) -> bool:
        """Attempt to acquire an advisory file lock for an arm."""
        try:
            safe_path = str(self._resolve_safe(rel_path))
            with self._lock_mutex:
                current_holder = self._locks.get(safe_path)
                if current_holder is None or current_holder == arm_id:
                    self._locks[safe_path] = arm_id
                    return True
                return False
        except Exception as e:
            logger.debug("Failed acquiring lock on %s: %s", rel_path, e)  # best-effort: safe path resolution or invalid path
            return False

    def release_lock(self, rel_path: str, arm_id: int) -> bool:
        """Release an advisory file lock held by an arm."""
        try:
            safe_path = str(self._resolve_safe(rel_path))
            with self._lock_mutex:
                if self._locks.get(safe_path) == arm_id:
                    del self._locks[safe_path]
                    return True
                return False
        except Exception as e:
            logger.debug("Failed releasing lock on %s: %s", rel_path, e)  # best-effort: lock resolution or key missing
            return False

    @contextlib.contextmanager
    def file_lock(self, rel_path: str, arm_id: int):
        """Context manager to reliably acquire and release an advisory lock."""
        acquired = self.acquire_lock(rel_path, arm_id)
        if not acquired:
            raise RuntimeError(f"Could not acquire lock on '{rel_path}' for Arm {arm_id}")
        try:
            yield
        finally:
            self.release_lock(rel_path, arm_id)

    def read_file(self, rel_path: str) -> ToolResult:
        """Read a file from the workspace sandbox with confinement and secret redaction."""
        t0 = time.time()
        try:
            target = self._resolve_safe(rel_path)
            if not target.exists():
                return ToolResult(
                    tool_name="read_file",
                    target=rel_path,
                    success=False,
                    returncode=1,
                    error=f"FileNotFoundError: '{rel_path}' does not exist.",
                    stderr=f"FileNotFoundError: '{rel_path}' does not exist.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )
            if target.is_dir():
                return ToolResult(
                    tool_name="read_file",
                    target=rel_path,
                    success=False,
                    returncode=1,
                    error=f"IsADirectoryError: '{rel_path}' is a directory, not a file. Use list_dir instead.",
                    stderr=f"IsADirectoryError: '{rel_path}' is a directory, not a file. Use list_dir instead.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )
            if target.is_symlink() and not _is_subpath(target.resolve(), self.root):
                return ToolResult(
                    tool_name="read_file",
                    target=rel_path,
                    success=False,
                    returncode=1,
                    error=f"Symlink traversal detected: '{rel_path}' points outside workspace root.",
                    stderr=f"Symlink traversal detected: '{rel_path}' points outside workspace root.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

            content = target.read_text(encoding="utf-8", errors="replace")
            # Redact sensitive credentials in output
            content = redact_secrets(content)
            return ToolResult(
                tool_name="read_file",
                target=rel_path,
                success=True,
                returncode=0,
                stdout=content,
                execution_time_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            err_msg = redact_secrets(str(e))
            return ToolResult(
                tool_name="read_file",
                target=rel_path,
                success=False,
                returncode=1,
                error=err_msg,
                stderr=err_msg,
                execution_time_ms=(time.time() - t0) * 1000,
            )

    def write_file(self, rel_path: str, content: str, arm_id: int = -1, validate_syntax: bool = True) -> ToolResult:
        """Write content to a file inside the sandbox, creating parent dirs if needed.

        Performs pre-flight path validation, symlink traversal prevention, AST syntax
        validation on Python/JSON, advisory lock checks, and bounded writes.
        """
        t0 = time.time()
        try:
            target = self._resolve_safe(rel_path)
            str_path = str(target)

            if self.budget_tracker is not None:
                self.budget_tracker.check_and_record_file_write(rel_path)

            # Prevent writing through external symlinks
            if target.is_symlink() and not _is_subpath(target.resolve(), self.root):
                return ToolResult(
                    tool_name="write_file",
                    target=rel_path,
                    success=False,
                    returncode=1,
                    error=f"Symlink traversal detected: target '{rel_path}' points outside workspace root.",
                    stderr=f"Symlink traversal detected: target '{rel_path}' points outside workspace root.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

            # Pre-flight syntax validation
            if validate_syntax:
                if target.suffix == ".py":
                    import ast
                    try:
                        ast.parse(content, filename=rel_path)
                    except SyntaxError as syn_err:
                        return ToolResult(
                            tool_name="write_file",
                            target=rel_path,
                            success=False,
                            returncode=1,
                            error=f"PreFlightSyntaxError in '{rel_path}' at line {syn_err.lineno}, col {syn_err.offset}: {syn_err.msg}.",
                            stderr=f"PreFlightSyntaxError in '{rel_path}' at line {syn_err.lineno}, col {syn_err.offset}: {syn_err.msg}. Refactor and fix invalid syntax.",
                            execution_time_ms=(time.time() - t0) * 1000,
                        )
                elif target.suffix == ".json":
                    import json
                    try:
                        json.loads(content)
                    except json.JSONDecodeError as json_err:
                        return ToolResult(
                            tool_name="write_file",
                            target=rel_path,
                            success=False,
                            returncode=1,
                            error=f"PreFlightJSONError in '{rel_path}' at line {json_err.lineno}: {json_err.msg}.",
                            stderr=f"PreFlightJSONError in '{rel_path}' at line {json_err.lineno}: {json_err.msg}. Refactor to valid JSON.",
                            execution_time_ms=(time.time() - t0) * 1000,
                        )

            with self._lock_mutex:
                holder = self._locks.get(str_path)
                if holder is not None and holder != arm_id and arm_id != -1:
                    return ToolResult(
                        tool_name="write_file",
                        target=rel_path,
                        success=False,
                        returncode=1,
                        error=f"FileLockError: '{rel_path}' is currently locked by Arm {holder}.",
                        stderr=f"FileLockError: '{rel_path}' is currently locked by Arm {holder}.",
                        execution_time_ms=(time.time() - t0) * 1000,
                    )

                # Create parent directories safely and verify containment
                target.parent.mkdir(parents=True, exist_ok=True)
                if not _is_subpath(target.parent.resolve(), self.root):
                    return ToolResult(
                        tool_name="write_file",
                        target=rel_path,
                        success=False,
                        returncode=1,
                        error=f"Path traversal detected in parent directory: '{target.parent}' resolves outside workspace.",
                        stderr=f"Path traversal detected in parent directory: '{target.parent}' resolves outside workspace.",
                        execution_time_ms=(time.time() - t0) * 1000,
                    )

                diff_lines = len(content.splitlines())
                target.write_text(content, encoding="utf-8")
                if not self.dry_run:
                    rel_clean = str(rel_path).lstrip("./")
                    if rel_clean not in self.files_written:
                        self.files_written.append(rel_clean)

            return ToolResult(
                tool_name="write_file",
                target=rel_path,
                success=True,
                returncode=0,
                stdout=f"Wrote {len(content)} bytes ({diff_lines} lines) to {rel_path}.",
                diff_lines=diff_lines,
                execution_time_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            err_msg = redact_secrets(str(e))
            return ToolResult(
                tool_name="write_file",
                target=rel_path,
                success=False,
                returncode=1,
                error=err_msg,
                stderr=err_msg,
                execution_time_ms=(time.time() - t0) * 1000,
            )

    def run_command(
        self,
        command: str,
        timeout_seconds: Optional[float] = None,
        allow_unrestricted: bool = False,
    ) -> ToolResult:
        """Execute a shell command inside the workspace directory with sandboxed boundaries.

        Enforces:
        - Rejection of dangerous hardcoded patterns (rm -rf /, forkbombs, mkfs).
        - Rejection of shell metacharacters and chaining (pipes, redirects, ;, &&, ||, subshells).
        - Allowlist check for permitted executables unless allow_unrestricted=True is explicitly set.
        - Confinement of argument file paths within the workspace root.
        - Argument array execution using shell=False.
        - Controlled minimal environment without leaking API keys/credentials.
        - Configurable timeout with process group SIGKILL to prevent orphan/zombie processes.
        - 64 KB bounded output capture and secret redaction on stdout/stderr.
        """
        t0 = time.time()
        timeout = float(timeout_seconds) if timeout_seconds is not None else self.default_timeout_seconds
        timeout = min(max(timeout, 0.1), self.max_timeout_seconds)

        # 1. Security sanitization: block known destructive root-level patterns
        blocked_patterns = ["rm -rf /", ":(){ :|:& };:", "dd if=/dev/zero", "mkfs."]
        for pattern in blocked_patterns:
            if pattern in command:
                return ToolResult(
                    tool_name="run_command",
                    target=command,
                    success=False,
                    returncode=126,
                    error=f"SecurityError: Blocked dangerous command pattern '{pattern}'",
                    stderr=f"SecurityError: Blocked dangerous command pattern '{pattern}'",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

        is_unrestricted = allow_unrestricted or self.allow_unrestricted or (os.getenv("OCTOFLOW_UNRESTRICTED_TOOLS") == "1")

        # 2. Strict command parse and allowlist policy (unless explicitly unrestricted)
        if not is_unrestricted:
            # Check for shell metacharacters and command chaining
            if has_compound_operators(command):
                return ToolResult(
                    tool_name="run_command",
                    target=command,
                    success=False,
                    returncode=126,
                    error="DisallowedShellConstruct: Shell metacharacters (|, ;, &, >, <, `) and command chaining are blocked in sandbox tool calls.",
                    stderr="DisallowedShellConstruct: Shell metacharacters (|, ;, &, >, <, `) and command chaining are blocked in sandbox tool calls.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

            try:
                argv = shlex.split(command)
            except ValueError as val_err:
                return ToolResult(
                    tool_name="run_command",
                    target=command,
                    success=False,
                    returncode=126,
                    error=f"InvalidCommandSyntax: {val_err}",
                    stderr=f"InvalidCommandSyntax: {val_err}",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

            if not argv:
                return ToolResult(
                    tool_name="run_command",
                    target=command,
                    success=False,
                    returncode=126,
                    error="EmptyCommand: Command cannot be empty.",
                    stderr="EmptyCommand: Command cannot be empty.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

            # Check allowlist
            head = Path(argv[0]).name.lower()
            if head not in self.allowed_commands:
                return ToolResult(
                    tool_name="run_command",
                    target=command,
                    success=False,
                    returncode=126,
                    error=f"DisallowedCommandError: Command '{head}' is not permitted by the sandbox execution policy.",
                    stderr=f"DisallowedCommandError: Command '{head}' is not permitted by the sandbox execution policy. Allowed commands: {', '.join(sorted(self.allowed_commands))}",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

            # Check argument paths stay within workspace
            prev_token = ""
            for arg in argv[1:]:
                # Skip flags
                if arg.startswith("-"):
                    prev_token = arg
                    continue
                # Skip inline code strings
                if prev_token in ("-c", "-e", "--eval"):
                    prev_token = arg
                    continue
                # Allowed system paths / URLs
                if arg in ("/dev/null", "/dev/zero", "/dev/stdout", "/dev/stderr") or arg.startswith(("http://", "https://", "git://", "ssh://")):
                    prev_token = arg
                    continue

                if "/" in arg or "\\" in arg or ".." in arg or arg.startswith("~"):
                    try:
                        resolved_arg = Path(os.path.expanduser(arg)).resolve()
                        if not _is_subpath(resolved_arg, self.root):
                            return ToolResult(
                                tool_name="run_command",
                                target=command,
                                success=False,
                                returncode=126,
                                error=f"PathTraversalError: Command argument '{arg}' targets path outside workspace root.",
                                stderr=f"PathTraversalError: Command argument '{arg}' targets path outside workspace root.",
                                execution_time_ms=(time.time() - t0) * 1000,
                            )
                    except Exception as e:
                        logger.debug("Path resolution failed for arg %s: %s", arg, e)  # best-effort: malformed path argument
                prev_token = arg
        else:
            # Unrestricted opt-in mode
            try:
                argv = shlex.split(command)
            except Exception as e:
                logger.debug("shlex.split failed for command %r: %s", command, e)  # best-effort: fallback to split on unclosed quotes
                argv = command.split()

        # 3. Check executable existence on PATH
        if argv and self.sandbox_mode != "docker":
            exec_name = argv[0]
            if not shutil.which(exec_name) and not Path(exec_name).is_file():
                return ToolResult(
                    tool_name="run_command",
                    target=command,
                    success=False,
                    returncode=127,
                    error=f"FileNotFoundError: Command executable '{exec_name}' not found on PATH.",
                    stderr=f"FileNotFoundError: Command executable '{exec_name}' not found on PATH.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

        clean_env = self._get_controlled_environment()

        # 4. Execute command
        try:
            if self.sandbox_mode == "docker":
                chk = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=5)
                if chk.returncode == 0:
                    docker_exec = [
                        "docker", "run", "--rm",
                        "-v", f"{self.root}:/workspace",
                        "-w", "/workspace",
                        self.docker_image,
                    ] + argv
                    proc = subprocess.run(
                        docker_exec,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                    )
                else:
                    proc = subprocess.run(
                        argv,
                        shell=False,
                        cwd=str(self.root),
                        env=clean_env,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        start_new_session=True,
                    )
            else:
                proc = subprocess.run(
                    argv,
                    shell=False,
                    cwd=str(self.root),
                    env=clean_env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    start_new_session=True,
                )

            elapsed = (time.time() - t0) * 1000
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""

            # Bounded output capture (64 KB limit)
            if len(stdout.encode("utf-8", errors="ignore")) > self.max_capture_bytes:
                stdout = stdout[:self.max_capture_bytes] + "\n... [OUTPUT TRUNCATED AT 64 KB] ..."
            if len(stderr.encode("utf-8", errors="ignore")) > self.max_capture_bytes:
                stderr = stderr[:self.max_capture_bytes] + "\n... [STDERR TRUNCATED AT 64 KB] ..."

            # Redact secrets from output
            stdout = redact_secrets(stdout)
            stderr = redact_secrets(stderr)

            success = (proc.returncode == 0)
            err_msg = None if success else (stderr.strip() or f"Command failed with exit code {proc.returncode}")

            return ToolResult(
                tool_name="run_command",
                target=command,
                success=success,
                returncode=proc.returncode,
                stdout=stdout,
                stderr=stderr,
                error=err_msg,
                execution_time_ms=elapsed,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="run_command",
                target=command,
                success=False,
                returncode=124,
                error=f"TimeoutExpired: Command timed out after {timeout} seconds.",
                stderr=f"TimeoutExpired: Command timed out after {timeout} seconds.",
                execution_time_ms=(time.time() - t0) * 1000,
            )

        except Exception as e:
            err_str = redact_secrets(str(e))
            return ToolResult(
                tool_name="run_command",
                target=command,
                success=False,
                returncode=1,
                error=err_str,
                stderr=err_str,
                execution_time_ms=(time.time() - t0) * 1000,
            )

    def list_dir(self, rel_path: str = ".") -> ToolResult:
        """List files and subdirectories within a sandbox directory with strict confinement."""
        t0 = time.time()
        try:
            target = self._resolve_safe(rel_path)
            if not target.exists() or not target.is_dir():
                return ToolResult(
                    tool_name="list_dir",
                    target=rel_path,
                    success=False,
                    returncode=1,
                    error=f"NotADirectoryError: '{rel_path}' is not a directory.",
                    stderr=f"NotADirectoryError: '{rel_path}' is not a directory.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )
            entries = []
            for item in sorted(target.iterdir()):
                prefix = "[DIR]  " if item.is_dir() else "[FILE] "
                clean_name = redact_secrets(item.name)
                entries.append(f"{prefix}{clean_name}")
            return ToolResult(
                tool_name="list_dir",
                target=rel_path,
                success=True,
                returncode=0,
                stdout="\n".join(entries),
                execution_time_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            err_msg = redact_secrets(str(e))
            return ToolResult(
                tool_name="list_dir",
                target=rel_path,
                success=False,
                returncode=1,
                error=err_msg,
                stderr=err_msg,
                execution_time_ms=(time.time() - t0) * 1000,
            )

    async def aread_file(self, rel_path: str) -> ToolResult:
        """Asynchronously read a file from the workspace sandbox."""
        return await asyncio.to_thread(self.read_file, rel_path)

    async def awrite_file(self, rel_path: str, content: str, arm_id: int = -1, validate_syntax: bool = True) -> ToolResult:
        """Asynchronously write a file to the workspace sandbox."""
        return await asyncio.to_thread(self.write_file, rel_path, content, arm_id, validate_syntax)

    async def arun_command(self, command: str, timeout_seconds: Optional[float] = None, allow_unrestricted: bool = False) -> ToolResult:
        """Asynchronously run a command inside the workspace sandbox."""
        return await asyncio.to_thread(self.run_command, command, timeout_seconds, allow_unrestricted)

    async def alist_dir(self, rel_path: str = ".") -> ToolResult:
        """Asynchronously list directory contents."""
        return await asyncio.to_thread(self.list_dir, rel_path)
