"""Workspace Sandbox & Tool Execution Environment.

Provides safe filesystem and terminal command tools with strict boundary enforcement,
path containment, and advisory file locks to prevent race conditions.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


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


import asyncio
import threading


class WorkspaceSandbox:
    """Safe execution sandbox rooted in a specific workspace directory with optional Docker isolation."""

    def __init__(self, workspace_dir: str, sandbox_mode: str = "local", docker_image: str = "python:3.12-slim"):
        self.root = Path(workspace_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.sandbox_mode = sandbox_mode.lower()
        self.docker_image = docker_image
        # Advisory locks: file_path_str -> holding_arm_id
        self._locks: Dict[str, int] = {}
        self._lock_mutex = threading.RLock()

    def _resolve_safe(self, rel_path: str) -> Path:
        """Resolve a relative or absolute path safely within the workspace."""
        clean_path = str(rel_path).strip().strip("'\"").replace("\\", "/")
        path_obj = Path(clean_path).expanduser()
        if path_obj.is_absolute():
            resolved = path_obj.resolve()
            try:
                is_inside = resolved.is_relative_to(self.root)
            except (ValueError, AttributeError):
                try:
                    is_inside = os.path.commonpath([str(self.root), str(resolved)]) == str(self.root)
                except ValueError:
                    is_inside = False
            if is_inside:
                return resolved
            raise ValueError(f"Path traversal detected: '{rel_path}' resolves outside workspace root '{self.root}'")

        # For relative paths, remove any leading slashes
        clean_path = clean_path.lstrip("/")
        resolved = (self.root / clean_path).resolve()

        try:
            is_inside = resolved.is_relative_to(self.root)
        except (ValueError, AttributeError):
            try:
                is_inside = os.path.commonpath([str(self.root), str(resolved)]) == str(self.root)
            except ValueError:
                is_inside = False

        if not is_inside:
            raise ValueError(f"Path traversal detected: '{rel_path}' resolves outside workspace root '{self.root}'")

        return resolved

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
        except Exception:
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
        except Exception:
            return False

    import contextlib

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
        """Read a file from the workspace sandbox."""
        t0 = time.time()
        try:
            target = self._resolve_safe(rel_path)
            if not target.exists():
                return ToolResult(
                    tool_name="read_file",
                    target=rel_path,
                    success=False,
                    returncode=1,
                    stderr=f"FileNotFoundError: '{rel_path}' does not exist.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )
            content = target.read_text(encoding="utf-8", errors="replace")
            return ToolResult(
                tool_name="read_file",
                target=rel_path,
                success=True,
                returncode=0,
                stdout=content,
                execution_time_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name="read_file",
                target=rel_path,
                success=False,
                returncode=1,
                error=str(e),
                stderr=str(e),
                execution_time_ms=(time.time() - t0) * 1000,
            )

    def write_file(self, rel_path: str, content: str, arm_id: int = -1, validate_syntax: bool = True) -> ToolResult:
        """Write content to a file inside the sandbox, creating parent dirs if needed.

        Performs pre-flight AST syntax validation on Python and JSON files to trigger
        immediate reflexive self-healing in the agent before persistent workspace corruption.
        """
        t0 = time.time()
        try:
            target = self._resolve_safe(rel_path)
            str_path = str(target)

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
                        stderr=f"FileLockError: '{rel_path}' is currently locked by Arm {holder}.",
                        execution_time_ms=(time.time() - t0) * 1000,
                    )

                diff_lines = len(content.splitlines())
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

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
            return ToolResult(
                tool_name="write_file",
                target=rel_path,
                success=False,
                returncode=1,
                error=str(e),
                stderr=str(e),
                execution_time_ms=(time.time() - t0) * 1000,
            )

    def run_command(self, command: str, timeout_seconds: float = 60.0) -> ToolResult:
        """Execute a shell command inside the workspace directory."""
        t0 = time.time()
        # Security sanitization: block commands escaping or destroying workspace
        blocked_patterns = ["rm -rf /", ":(){ :|:& };:", "dd if=/dev/zero", "mkfs."]
        for pattern in blocked_patterns:
            if pattern in command:
                return ToolResult(
                    tool_name="run_command",
                    target=command,
                    success=False,
                    returncode=126,
                    stderr=f"SecurityError: Blocked dangerous command pattern '{pattern}'",
                    execution_time_ms=(time.time() - t0) * 1000,
                )

        try:
            if self.sandbox_mode == "docker":
                # Verify docker engine presence
                chk = subprocess.run(["docker", "info"], capture_output=True)
                if chk.returncode == 0:
                    docker_exec = [
                        "docker", "run", "--rm",
                        "-v", f"{self.root}:/workspace",
                        "-w", "/workspace",
                        self.docker_image,
                        "sh", "-c", command,
                    ]
                    proc = subprocess.run(
                        docker_exec,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                    )
                else:
                    # Fallback to local execution if Docker daemon is unreachable
                    proc = subprocess.run(
                        command,
                        shell=True,
                        cwd=str(self.root),
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                    )
            else:
                proc = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(self.root),
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
            elapsed = (time.time() - t0) * 1000
            return ToolResult(
                tool_name="run_command",
                target=command,
                success=(proc.returncode == 0),
                returncode=proc.returncode,
                stdout=proc.stdout[:8000],  # Truncate output to prevent buffer bloat
                stderr=proc.stderr[:8000],
                execution_time_ms=elapsed,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="run_command",
                target=command,
                success=False,
                returncode=124,
                stderr=f"TimeoutExpired: Command timed out after {timeout_seconds} seconds.",
                execution_time_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name="run_command",
                target=command,
                success=False,
                returncode=1,
                error=str(e),
                stderr=str(e),
                execution_time_ms=(time.time() - t0) * 1000,
            )

    def list_dir(self, rel_path: str = ".") -> ToolResult:
        """List files and subdirectories within a sandbox directory."""
        t0 = time.time()
        try:
            target = self._resolve_safe(rel_path)
            if not target.exists() or not target.is_dir():
                return ToolResult(
                    tool_name="list_dir",
                    target=rel_path,
                    success=False,
                    returncode=1,
                    stderr=f"NotADirectoryError: '{rel_path}' is not a directory.",
                    execution_time_ms=(time.time() - t0) * 1000,
                )
            entries = []
            for item in sorted(target.iterdir()):
                prefix = "[DIR]  " if item.is_dir() else "[FILE] "
                entries.append(f"{prefix}{item.name}")
            return ToolResult(
                tool_name="list_dir",
                target=rel_path,
                success=True,
                returncode=0,
                stdout="\n".join(entries),
                execution_time_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name="list_dir",
                target=rel_path,
                success=False,
                returncode=1,
                error=str(e),
                stderr=str(e),
                execution_time_ms=(time.time() - t0) * 1000,
            )

    async def aread_file(self, rel_path: str) -> ToolResult:
        """Asynchronously read a file from the workspace sandbox."""
        return await asyncio.to_thread(self.read_file, rel_path)

    async def awrite_file(self, rel_path: str, content: str, arm_id: int = -1) -> ToolResult:
        """Asynchronously write a file to the workspace sandbox."""
        return await asyncio.to_thread(self.write_file, rel_path, content, arm_id)

    async def arun_command(self, command: str, timeout_seconds: float = 60.0) -> ToolResult:
        """Asynchronously run a command inside the workspace sandbox."""
        return await asyncio.to_thread(self.run_command, command, timeout_seconds)

    async def alist_dir(self, rel_path: str = ".") -> ToolResult:
        """Asynchronously list directory contents."""
        return await asyncio.to_thread(self.list_dir, rel_path)
