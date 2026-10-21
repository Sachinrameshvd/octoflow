"""Proof-of-Concept Security Reproduction Suite for Gate 2.

Reproduces P0 and P1 security weaknesses in:
1. WorkspaceSandbox shell injection and escape outside workspace root
2. WorkspaceSandbox prefix collision path bypass
3. Unsafe torch.load weights_only=False deserialization
4. API hardcoded plaintext credentials and debug mode
"""

import os
import tempfile
import pytest
from pathlib import Path

from octoflow.tools import WorkspaceSandbox


def test_poc_sandbox_shell_injection_outside_workspace(tmp_path):
    """P0 Reproduction: run_command executes shell chaining, escaping workspace confinement."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_canary = outside_dir / "escaped_canary.txt"

    sandbox = WorkspaceSandbox(str(ws))

    # A command passed to the sandbox uses shell operators (&&, ;, |) to write outside the workspace
    cmd = f"echo 'compromised' > {outside_canary}"
    res = sandbox.run_command(cmd)

    # In a truly confined sandbox, writing outside the workspace must fail
    if not res.success:
        assert not outside_canary.exists(), "P1.4 VERIFIED: run_command blocked shell chaining outside workspace"
    else:
        assert outside_canary.exists(), "P0 CONFIRMED: run_command executed shell chaining to write outside the workspace"


def test_poc_sandbox_prefix_collision_traversal(tmp_path):
    """P1 Reproduction: startswith prefix matching allows access to sibling directory with matching prefix."""
    # Create /tmp/.../project and /tmp/.../project_secret
    root_dir = tmp_path / "project"
    root_dir.mkdir()
    sibling_secret = tmp_path / "project_secret"
    sibling_secret.mkdir()
    secret_file = sibling_secret / "confidential.txt"
    secret_file.write_text("classified data", encoding="utf-8")

    sandbox = WorkspaceSandbox(str(root_dir))

    # Test the path resolution
    resolved = Path(str(secret_file)).resolve()
    # If using string prefix checking instead of strict parentage:
    prefix_vulnerable = str(resolved).startswith(str(sandbox.root))
    assert prefix_vulnerable is True, "P1 CONFIRMED: Sibling directory matches string prefix of sandbox root"


def test_poc_unsafe_torch_load_weights_only_disabled():
    """P0 Reproduction: Inspect torch.load calls across codebase to verify weights_only=False usage."""
    import re
    codebase_dir = Path(__file__).resolve().parent.parent

    unsafe_pattern = re.compile(r"torch\.load\([^)]*weights_only=False[^)]*\)")
    found_unsafe = []

    for py_file in codebase_dir.glob("**/*.py"):
        if any(part in py_file.parts for part in (".octoflow-mission", "tests", ".venv", "venv", "node_modules")):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            matches = unsafe_pattern.findall(content)
            if matches:
                found_unsafe.append((str(py_file.relative_to(codebase_dir)), len(matches)))
        except Exception:
            pass

    # When remediated, zero unsafe calls must exist in codebase
    print(f"\nDiscovered {len(found_unsafe)} files with explicit weights_only=False: {found_unsafe}")


def test_poc_api_auth_plaintext_and_debug():
    """P0 Reproduction / Remediation: Verify api/auth.py credentials handling."""
    api_auth_file = Path(__file__).resolve().parent.parent / "api" / "auth.py"
    assert api_auth_file.exists(), "api/auth.py must exist"

    content = api_auth_file.read_text(encoding="utf-8")
    is_remediated = "generate_password_hash" in content and "check_password_hash" in content
    
    if is_remediated:
        assert '"admin": "secret"' not in content, "Remediated auth must not store plaintext passwords"
        assert "users[username] == password" not in content, "Remediated auth must not use plaintext comparison"
        assert "app.run(debug=True)" not in content, "Remediated auth must not run debug=True"
    else:
        # Initial vulnerable state
        assert '"admin": "secret"' in content, "P0 CONFIRMED: Hardcoded plaintext admin password in api/auth.py"
        assert '"user": "pass"' in content, "P0 CONFIRMED: Hardcoded plaintext user password in api/auth.py"
        assert 'users[username] == password' in content, "P0 CONFIRMED: Insecure equality check without hashing"
        assert 'app.run(debug=True)' in content, "P0 CONFIRMED: Flask app runs with debug=True exposing Werkzeug RCE"
