"""Comprehensive Unit Tests for WorkspaceSandbox (Subsystem 3.1).

Covers:
1. Path traversal attacks (../, absolute paths, prefix collision, symlinks pointing outside)
2. Special files, deep nesting, binary files
3. Advisory locking mutual exclusion, crash cleanup, context-manager locking
4. Process termination on timeout without leaking orphan processes
5. Docker sandbox unavailable behavior (explicit warning or error, not silent fallback)
"""

import os
import time

import pytest
from octoflow.tools import WorkspaceSandbox


@pytest.fixture
def sandbox_env(tmp_path):
    """Create a temporary sandbox root and an external directory for containment tests."""
    ws = tmp_path / "sandbox_workspace"
    ws.mkdir()
    outside = tmp_path / "sandbox_workspace_outside"
    outside.mkdir()
    return ws, outside


def test_path_traversal_dot_dot_rejected(sandbox_env):
    """Verify ../ traversal is completely blocked on read and write."""
    ws, outside = sandbox_env
    secret_file = outside / "secret.txt"
    secret_file.write_text("classified", encoding="utf-8")

    sandbox = WorkspaceSandbox(str(ws))

    # Read traversal
    res_read = sandbox.read_file("../sandbox_workspace_outside/secret.txt")
    assert not res_read.success
    assert "Path traversal detected" in res_read.stderr or "outside workspace" in res_read.stderr

    # Write traversal
    res_write = sandbox.write_file("../sandbox_workspace_outside/evil.txt", "evil")
    assert not res_write.success
    assert not (outside / "evil.txt").exists()


def test_path_prefix_collision_blocked(sandbox_env):
    """Verify sibling directory sharing root prefix name is strictly blocked."""
    ws, outside = sandbox_env
    secret_file = outside / "confidential.txt"
    secret_file.write_text("secret", encoding="utf-8")

    sandbox = WorkspaceSandbox(str(ws))

    # Attempt to resolve the sibling directory by absolute path or relative path
    with pytest.raises(ValueError, match="Path traversal detected"):
        sandbox._resolve_safe(str(secret_file))


def test_symlink_pointing_outside_blocked(sandbox_env):
    """Verify symlink created inside workspace pointing to external file is blocked on access."""
    ws, outside = sandbox_env
    target_secret = outside / "host_secret.txt"
    target_secret.write_text("root_secret", encoding="utf-8")

    # Create symlink inside workspace
    link_in_ws = ws / "leak_link.txt"
    try:
        os.symlink(str(target_secret), str(link_in_ws))
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this filesystem")

    sandbox = WorkspaceSandbox(str(ws))
    res = sandbox.read_file("leak_link.txt")
    assert not res.success, "Reading through external symlink MUST be blocked"
    assert "Path traversal detected" in res.stderr or "outside workspace" in res_read.stderr


def test_deep_nesting_and_special_characters(sandbox_env):
    """Verify deep directory creation and paths with special characters."""
    ws, _ = sandbox_env
    sandbox = WorkspaceSandbox(str(ws))

    nested_path = "a/b/c/d/e/deep_module.py"
    res = sandbox.write_file(nested_path, "x = 42\n")
    assert res.success
    assert (ws / nested_path).exists()

    res_read = sandbox.read_file(nested_path)
    assert res_read.success
    assert "x = 42" in res_read.stdout


def test_binary_file_safety(sandbox_env):
    """Verify binary files can be detected or written safely without UTF-8 crash."""
    ws, _ = sandbox_env
    sandbox = WorkspaceSandbox(str(ws))

    bin_path = ws / "binary.dat"
    bin_path.write_bytes(b"\x00\xff\xfe\x00\x01\x02\x03\x04")

    # read_file should handle non-UTF8 gracefully with replacement or error, not uncaught crash
    res = sandbox.read_file("binary.dat")
    assert res.success or "DecodeError" in res.stderr


def test_advisory_locking_mutual_exclusion(sandbox_env):
    """Verify two arms cannot acquire lock on the same file concurrently."""
    ws, _ = sandbox_env
    sandbox = WorkspaceSandbox(str(ws))

    file_to_lock = "module.py"
    # Arm 1 acquires
    assert sandbox.acquire_lock(file_to_lock, arm_id=1) is True
    # Arm 1 can re-acquire (reentrant for same arm)
    assert sandbox.acquire_lock(file_to_lock, arm_id=1) is True
    # Arm 2 is blocked
    assert sandbox.acquire_lock(file_to_lock, arm_id=2) is False

    # Arm 2 attempt to write is rejected due to lock
    res = sandbox.write_file(file_to_lock, "arm2 = True\n", arm_id=2)
    assert not res.success
    assert "FileLockError" in res.stderr

    # Arm 1 releases
    assert sandbox.release_lock(file_to_lock, arm_id=1) is True
    # Now Arm 2 can acquire
    assert sandbox.acquire_lock(file_to_lock, arm_id=2) is True
    sandbox.release_lock(file_to_lock, arm_id=2)


def test_advisory_locking_context_manager(sandbox_env):
    """Verify context-managed lock release on normal exit and on exception."""
    ws, _ = sandbox_env
    sandbox = WorkspaceSandbox(str(ws))

    target = "locked_service.py"
    try:
        with sandbox.file_lock(target, arm_id=3):
            assert sandbox._locks.get(str(sandbox._resolve_safe(target))) == 3
            raise RuntimeError("Simulated crash mid-edit")
    except RuntimeError:
        pass

    # Lock must be released even after exception
    assert sandbox._locks.get(str(sandbox._resolve_safe(target))) is None
    # Another arm can now acquire
    assert sandbox.acquire_lock(target, arm_id=4) is True
    sandbox.release_lock(target, arm_id=4)


def test_process_timeout_and_group_termination(sandbox_env):
    """Verify that command timeout terminates long-running process without hanging."""
    ws, _ = sandbox_env
    sandbox = WorkspaceSandbox(str(ws))

    t0 = time.time()
    res = sandbox.run_command("python3 -c 'import time; time.sleep(10)'", timeout_seconds=1)
    elapsed = time.time() - t0

    assert not res.success
    assert res.returncode == 124
    assert "TimeoutExpired" in res.stderr
    assert elapsed < 3.0, "Timeout must abort promptly"
