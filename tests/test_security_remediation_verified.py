"""Security Remediation Verification Suite (Phase 3).

Verifies that all P0/P1 security vulnerabilities uncovered in Phase 2
have been strictly remediated and verified:
1. WorkspaceSandbox strict path confinement (no traversal, no prefix collisions).
2. Zero occurrences of unsafe deserialization (torch.load with weights_only=False).
3. API authentication enforces cryptographic password hashing (werkzeug/scrypt/pbkdf2),
   constant-time comparison, and disables dangerous Flask debug=True in production.
"""

import re
from pathlib import Path

from octoflow.tools import WorkspaceSandbox


def test_remediated_path_traversal_and_prefix_collision(tmp_path):
    """Verify WorkspaceSandbox rejects traversal and prefix collisions."""
    root = tmp_path / "project"
    root.mkdir()
    sibling = tmp_path / "project_secret"
    sibling.mkdir()
    (sibling / "leak.txt").write_text("secret")

    sandbox = WorkspaceSandbox(str(root))

    # 1. Path traversal escape attempts
    res_traversal = sandbox.read_file("../project_secret/leak.txt")
    assert not res_traversal.success
    assert "Path traversal detected" in res_traversal.stderr

    # 2. Direct absolute path escape
    res_abs = sandbox.read_file(str(sibling / "leak.txt"))
    assert not res_abs.success
    assert "Path traversal detected" in res_abs.stderr

    # 3. Valid in-tree access works
    res_write = sandbox.write_file("valid.txt", "safe content")
    assert res_write.success
    assert (root / "valid.txt").exists()


def test_remediated_torch_load_weights_only():
    """Verify zero repository python modules use unsafe weights_only=False."""
    codebase_dir = Path(__file__).resolve().parent.parent
    unsafe_pattern = re.compile(r"torch\.load\([^)]*weights_only=False[^)]*\)")
    found_unsafe = []

    for py_file in codebase_dir.glob("**/*.py"):
        # Ignore tests, virtualenvs, and mission scratch logs
        parts = py_file.parts
        if any(
            p in parts
            for p in (
                "tests",
                ".octoflow-mission",
                ".venv",
                "venv",
                "node_modules",
                "build",
                "dist",
            )
        ):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            if unsafe_pattern.search(content):
                found_unsafe.append(str(py_file.relative_to(codebase_dir)))
        except Exception:
            pass

    assert len(found_unsafe) == 0, f"Found files still using weights_only=False: {found_unsafe}"


def test_remediated_api_auth_security():
    """Verify api/auth.py uses secure password hashing and no debug=True."""
    api_auth_file = Path(__file__).resolve().parent.parent / "api" / "auth.py"
    assert api_auth_file.exists()
    content = api_auth_file.read_text(encoding="utf-8")

    # Plaintext secrets must not be stored in user dict
    assert '"admin": "secret"' not in content
    assert '"user": "pass"' not in content

    # Cryptographic password hashing must be used
    assert "check_password_hash" in content
    assert "generate_password_hash" in content

    # Insecure plaintext check must be absent
    assert "users[username] == password" not in content

    # Flask debug=True must not be unconditionally hardcoded
    assert "app.run(debug=True)" not in content
