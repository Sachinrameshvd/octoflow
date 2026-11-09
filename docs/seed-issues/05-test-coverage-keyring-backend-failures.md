# Add Unit Tests for Keyring Backend Failure Fallbacks

**Difficulty:** Good First Issue  
**Labels:** `testing`, `security`, `good first issue`  
**Mentoring Pointer:** Check out [`octoflow/keyring_store.py`](../../octoflow/keyring_store.py) and [`tests/test_keyring_store.py`](../../tests/) (or create it if absent).

---

## Context
OctoFlow prioritizes secret security. In [`octoflow/keyring_store.py`](../../octoflow/keyring_store.py), API keys are stored in the OS keyring service (macOS Keychain, Linux SecretService) when the `keyring` optional extra is installed.

When the OS keyring is unavailable, locked, or raises `keyring.errors.KeyringError`, OctoFlow must gracefully degrade to configuration file storage (mode `0600`) without crashing the application. Currently, this exception-handling branch lacks dedicated mock unit tests.

---

## Objectives & Requirements
1. Author unit tests covering the failure modes in [`octoflow/keyring_store.py`](../../octoflow/keyring_store.py):
   - Keyring module import failure (`ImportError`).
   - Keyring backend raises `KeyringError` during retrieval or storage.
   - Keyring returns `None` for unset keys.
2. Verify that fallback mechanisms safely route credentials to configuration storage with restricted `0600` permissions.
3. Assert that log messages output appropriate warnings without printing raw API keys or passwords.

---

## Files to Touch
- `tests/test_keyring_store.py`: Author new test module or append to existing settings tests.
- [`octoflow/keyring_store.py`](../../octoflow/keyring_store.py): Ensure all error paths are clean and typed.

---

## Acceptance Criteria
- [ ] Mocked tests simulate `keyring.errors.KeyringError` on `set_password` and `get_password`.
- [ ] Test verifies that secrets fall back to file storage with mode `0600`.
- [ ] No raw secret strings appear in logs or test output.
- [ ] Pytest passes: `pytest tests/test_keyring_store.py`.
