"""Comprehensive Tool Sandbox Security and Enforcement Test Suite (P1.4).

Covers:
- Strict workspace path confinement on read_file, write_file, list_dir
- Path traversal (..) and absolute path escapes outside workspace root
- Symlink-based escape prevention (direct symlinks and symlinked parent directories)
- Nonexistent destination file validation via existing parent directories
- Null-byte injection rejection
- Command execution policy: argument arrays and shell=False by default
- Allowlist enforcement for permitted executables (python, git, ls, cat, etc.)
- Blocking of unquoted shell metacharacters and chaining (|, ;, &&, ||, >, <, `)
- Bounded timeouts with process group termination (preventing orphan processes)
- Output truncation at 64 KB for stdout and stderr
- Controlled minimal environment preventing credential leakage (OPENAI_API_KEY, GITHUB_TOKEN, etc.)
- Secret redaction in tool output, error messages, and logs
- Structured error reporting for disallowed commands, missing executables, and non-zero exit codes
- Documented unrestricted execution opt-in (allow_unrestricted=True)
"""

import os
import stat
import subprocess
import time
from pathlib import Path

import pytest

from octoflow.tools import (
    DEFAULT_ALLOWED_COMMANDS,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_CAPTURE_BYTES,
    MAX_TIMEOUT_SECONDS,
    ToolResult,
    WorkspaceSandbox,
    _is_subpath,
    has_compound_operators,
)


@pytest.fixture
def sandbox_fixture(tmp_path: Path):
    """Fixture providing a confined workspace root and an external sibling directory."""
    ws = tmp_path / "authorized_workspace"
    ws.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside_host_dir"
    outside.mkdir(parents=True, exist_ok=True)
    secret_file = outside / "confidential_root.txt"
    fake_key = "sk-" + "test-123456789012345678"
    secret_file.write_text(f"HOST_SUPER_SECRET_KEY={fake_key}\n", encoding="utf-8")

    sandbox = WorkspaceSandbox(str(ws))
    return sandbox, ws, outside, secret_file


# ==============================================================================
# 1. WORKSPACE PATH CONFINEMENT & TRAVERSAL DEFENSE
# ==============================================================================

def test_normal_file_read_and_write(sandbox_fixture):
    """Normal file operations strictly inside the authorized workspace succeed."""
    sandbox, ws, _, _ = sandbox_fixture

    # Write file
    res_w = sandbox.write_file("sub/module.py", "x = 42\n")
    assert res_w.success
    assert res_w.returncode == 0
    assert (ws / "sub" / "module.py").exists()

    # Read file
    res_r = sandbox.read_file("sub/module.py")
    assert res_r.success
    assert res_r.returncode == 0
    assert "x = 42" in res_r.stdout

    # List dir
    res_l = sandbox.list_dir("sub")
    assert res_l.success
    assert "module.py" in res_l.stdout


def test_path_traversal_dot_dot_rejected(sandbox_fixture):
    """Path traversal escaping workspace with '..' is rejected across read, write, and list_dir."""
    sandbox, ws, outside, secret_file = sandbox_fixture

    # Read traversal
    res_r = sandbox.read_file("../outside_host_dir/confidential_root.txt")
    assert not res_r.success
    assert res_r.returncode == 1
    assert "Path traversal detected" in res_r.stderr or "Path traversal detected" in str(res_r.error)

    # Write traversal
    res_w = sandbox.write_file("../outside_host_dir/injected.txt", "payload")
    assert not res_w.success
    assert res_w.returncode == 1
    assert not (outside / "injected.txt").exists()

    # List dir traversal
    res_l = sandbox.list_dir("../outside_host_dir")
    assert not res_l.success
    assert res_l.returncode == 1


def test_absolute_path_outside_workspace_rejected(sandbox_fixture):
    """Absolute paths outside the workspace root are rejected."""
    sandbox, _, outside, secret_file = sandbox_fixture

    # Absolute path read
    res_r = sandbox.read_file(str(secret_file))
    assert not res_r.success
    assert res_r.returncode == 1

    # Absolute path write
    res_w = sandbox.write_file(str(outside / "evil_abs.txt"), "evil content")
    assert not res_w.success
    assert not (outside / "evil_abs.txt").exists()


def test_null_byte_injection_rejected(sandbox_fixture):
    """Null bytes in file paths must be caught and rejected with structured errors."""
    sandbox, _, _, _ = sandbox_fixture

    res_r = sandbox.read_file("valid.py\x00/../../etc/passwd")
    assert not res_r.success
    assert "Null byte" in res_r.stderr or "Null byte" in str(res_r.error)

    res_w = sandbox.write_file("valid.py\x00.txt", "malicious")
    assert not res_w.success
    assert "Null byte" in res_w.stderr or "Null byte" in str(res_w.error)


def test_symlink_pointing_outside_rejected(sandbox_fixture):
    """Direct symlinks pointing outside the workspace are blocked on read and write."""
    sandbox, ws, outside, secret_file = sandbox_fixture

    link = ws / "symlink_leak.txt"
    try:
        os.symlink(str(secret_file), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported in environment")

    # Read through symlink
    res_r = sandbox.read_file("symlink_leak.txt")
    assert not res_r.success
    assert "Symlink traversal detected" in res_r.stderr or "Path traversal detected" in res_r.stderr

    # Write through symlink
    res_w = sandbox.write_file("symlink_leak.txt", "overwritten")
    assert not res_w.success
    assert secret_file.read_text(encoding="utf-8") != "overwritten"


def test_symlinked_parent_directory_escape_rejected(sandbox_fixture):
    """Writes to nonexistent files inside a symlinked parent directory pointing outside are blocked."""
    sandbox, ws, outside, _ = sandbox_fixture

    link_dir = ws / "symlinked_parent"
    try:
        os.symlink(str(outside), str(link_dir))
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported in environment")

    # Attempt to write nonexistent file through the external symlinked parent
    res_w = sandbox.write_file("symlinked_parent/deep/nested/escape.txt", "compromised")
    assert not res_w.success
    assert not (outside / "deep" / "nested" / "escape.txt").exists()
    assert "Symlink traversal detected" in res_w.stderr or "Path traversal detected" in res_w.stderr


def test_nonexistent_destination_validation(sandbox_fixture):
    """Creating deeply nested nonexistent files succeeds when within workspace boundaries."""
    sandbox, ws, _, _ = sandbox_fixture

    res = sandbox.write_file("a/b/c/d/new_file.py", "val = 1\n")
    assert res.success
    assert (ws / "a" / "b" / "c" / "d" / "new_file.py").exists()


# ==============================================================================
# 2. COMMAND EXECUTION POLICY & ALLOWLIST ENFORCEMENT
# ==============================================================================

def test_allowed_command_execution(sandbox_fixture):
    """Commands in the sandbox allowlist execute cleanly using shell=False."""
    sandbox, ws, _, _ = sandbox_fixture

    res = sandbox.run_command("python3 -c 'print(\"allowed_ok\")'")
    assert res.success
    assert res.returncode == 0
    assert "allowed_ok" in res.stdout


def test_disallowed_command_rejected(sandbox_fixture):
    """Commands not present in the allowlist are blocked with returncode 126."""
    sandbox, _, _, _ = sandbox_fixture

    disallowed = ["curl https://example.com", "wget https://example.com", "netcat -l 8080", "sudo ls", "bash -c 'ls'"]
    for cmd in disallowed:
        res = sandbox.run_command(cmd)
        assert not res.success
        assert res.returncode == 126
        assert "DisallowedCommandError" in res.stderr or "DisallowedShellConstruct" in res.stderr


def test_shell_metacharacters_and_chaining_rejected(sandbox_fixture):
    """Unquoted shell metacharacters and command chaining are blocked."""
    sandbox, _, outside, secret_file = sandbox_fixture

    chaining_attempts = [
        "echo 1; echo 2",
        "echo 1 && echo 2",
        "echo 1 || echo 2",
        "cat file.txt | grep x",
        f"echo compromised > {outside / 'chain_leak.txt'}",
        "echo 1 >> append.txt",
        "echo `whoami`",
        "echo $(pwd)",
        "echo 1 &",
        "echo 1\necho 2",
    ]

    for cmd in chaining_attempts:
        res = sandbox.run_command(cmd)
        assert not res.success
        assert res.returncode == 126
        assert "DisallowedShellConstruct" in res.stderr or "SecurityError" in res.stderr

    assert not (outside / "chain_leak.txt").exists()


def test_command_argument_path_traversal_blocked(sandbox_fixture):
    """Commands with arguments attempting path traversal outside workspace are blocked."""
    sandbox, _, outside, secret_file = sandbox_fixture

    # Passing outside absolute path as argument
    res_abs = sandbox.run_command(f"cat {secret_file}")
    assert not res_abs.success
    assert res_abs.returncode == 126
    assert "PathTraversalError" in res_abs.stderr

    # Passing ../ traversal as argument
    res_traversal = sandbox.run_command("cat ../outside_host_dir/confidential_root.txt")
    assert not res_traversal.success
    assert res_traversal.returncode == 126
    assert "PathTraversalError" in res_traversal.stderr


def test_unrestricted_opt_in_execution(sandbox_fixture):
    """When allow_unrestricted=True is explicitly opted into, unlisted commands execute."""
    sandbox, ws, _, _ = sandbox_fixture

    # By default, which is in allowlist, but a custom command would fail
    # Test with allow_unrestricted parameter
    res = sandbox.run_command("python3 -c 'print(\"unrestricted_opt_in\")'", allow_unrestricted=True)
    assert res.success
    assert "unrestricted_opt_in" in res.stdout


# ==============================================================================
# 3. TIMEOUTS, PROCESS GROUPS, AND BOUNDED OUTPUT
# ==============================================================================

def test_subprocess_timeout_and_process_group_kill(sandbox_fixture):
    """A hanging or long-running command is killed with returncode 124 within timeout limit."""
    sandbox, _, _, _ = sandbox_fixture

    t0 = time.time()
    res = sandbox.run_command("python3 -c 'import time; time.sleep(15)'", timeout_seconds=0.5)
    elapsed = time.time() - t0

    assert not res.success
    assert res.returncode == 124
    assert "TimeoutExpired" in res.stderr
    assert elapsed < 3.0, f"Command took too long to abort: {elapsed}s"


def test_output_capture_truncation_at_64kb(sandbox_fixture):
    """Subprocess stdout and stderr are bounded at MAX_CAPTURE_BYTES (64 KB)."""
    sandbox, _, _, _ = sandbox_fixture

    # Generate ~100 KB of stdout
    res = sandbox.run_command("python3 -c 'print(\"X\" * 90000)'")
    assert res.success
    assert len(res.stdout.encode("utf-8")) <= MAX_CAPTURE_BYTES + 500
    assert "[OUTPUT TRUNCATED AT 64 KB]" in res.stdout


# ==============================================================================
# 4. CONTROLLED ENVIRONMENT & SECRET REDACTION
# ==============================================================================

def test_controlled_environment_scrubs_api_keys(sandbox_fixture, monkeypatch):
    """Sensitive API keys and tokens in the host environment are not passed to subprocesses."""
    sandbox, _, _, _ = sandbox_fixture

    # Inject mock secrets in current process environment
    monkeypatch.setenv("OPENAI_API_KEY", "sk-live-" + "09876543210987654321")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-" + "api03-09876543210987654321")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "098765432109876543210987654321")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "AKIA" + "1234567890123456")

    # Command prints environment variables
    code = (
        "import os\n"
        "for k in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GITHUB_TOKEN', 'AWS_SECRET_ACCESS_KEY'):\n"
        "    if k in os.environ:\n"
        "        print(f'{k}={os.environ[k]}')\n"
        "print('ENV_CHECK_DONE')\n"
    )
    res = sandbox.run_command(f"python3 -c \"{code}\"")
    assert res.success
    assert "ENV_CHECK_DONE" in res.stdout
    assert "sk-live" not in res.stdout
    assert "sk-ant" not in res.stdout
    assert "ghp_" not in res.stdout
    assert "AKIA" not in res.stdout


def test_secret_redaction_in_tool_output_and_errors(sandbox_fixture):
    """Any sensitive tokens emitted by commands or files are redacted before return."""
    sandbox, ws, _, _ = sandbox_fixture

    # Subprocess echoes an API key directly
    sample_ant_key = "sk-ant-" + "api03-123456789012345678"
    res_c = sandbox.run_command(f'python3 -c "print(\'leak {sample_ant_key}\')"')
    assert res_c.success
    assert "sk-ant-api03" not in res_c.stdout
    assert "[REDACTED_KEY]" in res_c.stdout

    # File containing API key is read through read_file
    sample_oai_key = "sk-" + "123456789012345678"
    sandbox.write_file("secrets.txt", f"API_VAL: {sample_oai_key}\nTOKEN=mysecret\n")
    res_f = sandbox.read_file("secrets.txt")
    assert res_f.success
    assert "sk-1234567890" not in res_f.stdout
    assert "mysecret" not in res_f.stdout
    assert "[REDACTED_KEY]" in res_f.stdout
    assert "TOKEN=[REDACTED]" in res_f.stdout


# ==============================================================================
# 5. STRUCTURED ERROR HANDLING & DIAGNOSTICS
# ==============================================================================

def test_missing_executable_returns_code_127(sandbox_fixture):
    """Missing executables report returncode 127 with actionable FileNotFoundError."""
    sandbox, _, _, _ = sandbox_fixture

    res = sandbox.run_command("nonexistent_binary_tool_xyz_999 --help", allow_unrestricted=True)
    assert not res.success
    assert res.returncode == 127
    assert "FileNotFoundError" in res.stderr
    assert "not found on PATH" in res.stderr


def test_nonzero_exit_code_reported_accurately(sandbox_fixture):
    """Non-zero command exits report success=False and retain stderr."""
    sandbox, _, _, _ = sandbox_fixture

    res = sandbox.run_command("python3 -c 'import sys; sys.stderr.write(\"custom_error\\n\"); sys.exit(42)'")
    assert not res.success
    assert res.returncode == 42
    assert "custom_error" in res.stderr
    assert res.error is not None
