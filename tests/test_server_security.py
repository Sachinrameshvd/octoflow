"""Comprehensive Security & Hardening Tests for OctoFlow Telemetry Server (P1.5).

Tests cover:
1. Default bind host is 127.0.0.1, with exposure warning on non-localhost binding.
2. WebSocket Origin validation:
   - Missing origin (non-browser tests/CLI) is accepted.
   - Localhost and 127.0.0.1 on served port are accepted.
   - Vite dev origin (localhost:5173) accepted only when dev_mode=True.
   - Arbitrary/untrusted origins (e.g. evil.example) rejected with close code 1008.
3. HTTP Host header validation (DNS-rebinding protection):
   - Valid local host headers accepted with 200.
   - Malicious/rebinding host headers rejected with 400.
4. Telemetry payload structural sanitization:
   - Prompts, file contents, stdout/stderr, and raw API keys stripped.
   - Free-text strings passed through secret redactor.
   - Canary strings verified completely absent from broadcast history.
5. Configuration security:
   - ~/.octoflow created with mode 0700.
   - config.json written with mode 0600.
   - Loose permissions hardened automatically on load with notice.
   - Credential masking returns first 3 characters + '****'.
"""

import asyncio
import stat
import time

import httpx
import pytest

pytestmark = pytest.mark.integration_local
try:
    from websockets.asyncio.client import connect as ws_connect
except ImportError:
    from websockets import connect as ws_connect
from octoflow.conductor import SwarmTelemetryEvent
from octoflow.config import (
    load_secure_config,
    mask_credential,
    save_secure_config,
)
from octoflow.server import TelemetryBroadcaster, find_available_port
from websockets.exceptions import ConnectionClosed


@pytest.fixture
def ephemeral_server():
    """Start an ephemeral TelemetryBroadcaster bound to 127.0.0.1."""
    port = find_available_port(19000, max_attempts=50, host="127.0.0.1")
    assert port is not None, "Failed to find available port for test server"
    server = TelemetryBroadcaster(port=port, host="127.0.0.1", dev_mode=False)
    server.start_in_background()
    time.sleep(0.4)
    yield server
    server.stop()
    time.sleep(0.1)


@pytest.fixture
def dev_mode_server():
    """Start an ephemeral TelemetryBroadcaster with dev_mode=True."""
    port = find_available_port(19100, max_attempts=50, host="127.0.0.1")
    assert port is not None, "Failed to find available port for dev test server"
    server = TelemetryBroadcaster(port=port, host="127.0.0.1", dev_mode=True)
    server.start_in_background()
    time.sleep(0.4)
    yield server
    server.stop()
    time.sleep(0.1)


# ==============================================================================
# 1. Bind Address & Network Warning Tests
# ==============================================================================


def test_default_bind_is_localhost():
    """Verify default server binds only to 127.0.0.1, not 0.0.0.0."""
    server = TelemetryBroadcaster(port=18088)
    assert server.host == "127.0.0.1"


def test_non_localhost_bind_prints_warning(capsys):
    """Verify non-localhost bind issues an explicit network exposure warning."""
    server = TelemetryBroadcaster(port=18089, host="0.0.0.0")
    assert server.host == "0.0.0.0"
    captured = capsys.readouterr()
    assert "SECURITY WARNING" in captured.err
    assert "0.0.0.0" in captured.err
    assert "exposes the swarm" in captured.err


# ==============================================================================
# 2. WebSocket Origin Validation Tests
# ==============================================================================


def test_websocket_accepts_no_origin(ephemeral_server):
    """Verify CLI / automated tests without an Origin header connect successfully."""

    async def _test():
        uri = f"ws://127.0.0.1:{ephemeral_server.port}/ws/telemetry"
        async with ws_connect(uri) as ws:
            assert ws is not None

    asyncio.run(_test())


def test_websocket_accepts_localhost_origin(ephemeral_server):
    """Verify visualizer served from http://localhost:<port> connects successfully."""

    async def _test():
        uri = f"ws://127.0.0.1:{ephemeral_server.port}/ws/telemetry"
        origin = f"http://localhost:{ephemeral_server.port}"
        async with ws_connect(uri, origin=origin) as ws:
            assert ws is not None

    asyncio.run(_test())


def test_websocket_accepts_127_origin(ephemeral_server):
    """Verify visualizer served from http://127.0.0.1:<port> connects successfully."""

    async def _test():
        uri = f"ws://127.0.0.1:{ephemeral_server.port}/ws/telemetry"
        origin = f"http://127.0.0.1:{ephemeral_server.port}"
        async with ws_connect(uri, origin=origin) as ws:
            assert ws is not None

    asyncio.run(_test())


def test_websocket_rejects_evil_origin_with_1008(ephemeral_server):
    """Verify untrusted origin (e.g. evil.example) is rejected with RFC 6455 code 1008."""

    async def _test():
        uri = f"ws://127.0.0.1:{ephemeral_server.port}/ws/telemetry"
        with pytest.raises(ConnectionClosed) as exc_info:
            async with ws_connect(uri, origin="https://evil.example") as ws:
                await ws.recv()
        close_code = (
            exc_info.value.rcvd.code
            if hasattr(exc_info.value, "rcvd") and exc_info.value.rcvd
            else exc_info.value.code
        )
        assert close_code == 1008

    asyncio.run(_test())


def test_websocket_rejects_arbitrary_web_page_origin(ephemeral_server):
    """Verify connection from an arbitrary website (e.g. attacker.com) is rejected with 1008."""

    async def _test():
        uri = f"ws://127.0.0.1:{ephemeral_server.port}/ws/telemetry"
        with pytest.raises(ConnectionClosed) as exc_info:
            async with ws_connect(uri, origin="http://attacker.com:8080") as ws:
                await ws.recv()
        close_code = (
            exc_info.value.rcvd.code
            if hasattr(exc_info.value, "rcvd") and exc_info.value.rcvd
            else exc_info.value.code
        )
        assert close_code == 1008

    asyncio.run(_test())


def test_vite_dev_mode_origin_behavior(ephemeral_server, dev_mode_server):
    """Verify Vite dev origin (http://localhost:5173) is accepted only in dev_mode."""

    async def _test():
        vite_origin = "http://localhost:5173"

        # Production/default server rejects Vite dev origin
        uri_prod = f"ws://127.0.0.1:{ephemeral_server.port}/ws/telemetry"
        with pytest.raises(ConnectionClosed) as exc_info:
            async with ws_connect(uri_prod, origin=vite_origin) as ws:
                await ws.recv()
        close_code = (
            exc_info.value.rcvd.code
            if hasattr(exc_info.value, "rcvd") and exc_info.value.rcvd
            else exc_info.value.code
        )
        assert close_code == 1008

        # Dev server accepts Vite dev origin
        uri_dev = f"ws://127.0.0.1:{dev_mode_server.port}/ws/telemetry"
        async with ws_connect(uri_dev, origin=vite_origin) as ws:
            assert ws is not None

    asyncio.run(_test())


def test_websocket_e2e_message_flow(ephemeral_server):
    """E2E Test: Proves local client connects, registers, and receives broadcast telemetry packets."""
    import json

    async def _test():
        uri = f"ws://127.0.0.1:{ephemeral_server.port}/ws/telemetry"
        async with ws_connect(uri) as ws:
            # Wait briefly for server to register connection into active_sockets
            await asyncio.sleep(0.15)
            assert len(ephemeral_server.active_sockets) >= 1

            test_event = SwarmTelemetryEvent(
                event_type="STEP",
                arm_id=4,
                role="Backend Engineer",
                status="DISPATCHED",
                surprise=0.42,
                threshold=0.35,
                active_coalitions=[[1, 4]],
                summary="Refactoring API endpoints",
            )
            ephemeral_server.broadcast(test_event)

            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)
            assert data["event_type"] == "STEP"
            assert data["arm_id"] == 4
            assert data["role"] == "Backend Engineer"
            assert data["status"] == "DISPATCHED"
            assert data["surprise"] == 0.42
            assert data["threshold"] == 0.35
            assert data["active_coalitions"] == [[1, 4]]
            assert data["summary"] == "Refactoring API endpoints"

    asyncio.run(_test())


# ==============================================================================
# 3. HTTP Host Header Validation Tests (DNS Rebinding Defense)
# ==============================================================================


def test_http_accepts_valid_localhost_host_header(ephemeral_server):
    """Verify valid Host header for localhost returns status 200."""
    url = f"http://127.0.0.1:{ephemeral_server.port}/"
    res = httpx.get(url, headers={"Host": f"127.0.0.1:{ephemeral_server.port}"})
    assert res.status_code == 200


def test_http_rejects_evil_host_header(ephemeral_server):
    """Verify malicious Host header (DNS rebinding attempt) is rejected with 400."""
    url = f"http://127.0.0.1:{ephemeral_server.port}/"
    res = httpx.get(url, headers={"Host": "evil.example"})
    assert res.status_code == 400
    assert "Forbidden: Invalid Host header" in res.text


def test_http_rejects_attacker_domain_host_header(ephemeral_server):
    """Verify attacker host header with port is rejected with 400."""
    url = f"http://127.0.0.1:{ephemeral_server.port}/"
    res = httpx.get(url, headers={"Host": f"attacker.com:{ephemeral_server.port}"})
    assert res.status_code == 400


# ==============================================================================
# 4. Telemetry Payload Sanitization & Canary Scrubbing Tests
# ==============================================================================


def test_telemetry_payload_strips_sensitive_fields():
    """Verify sanitize_telemetry_dict strips prompts, file contents, outputs, and keys."""
    test_key = "sk-" + "ant-api03-CANARYKEY1234567890abcdef-SHOULD-STRIP"
    summary_key = "sk-" + "ant-api03-abcdef1234567890abcdef"
    raw_payload = {
        "arm_id": 2,
        "role": "backend",
        "status": "active",
        "surprise": 0.42,
        "prompt": "CANARY_PROMPT_TEXT_SHOULD_BE_STRIPPED",
        "file_content": "CANARY_FILE_CONTENT_SHOULD_BE_STRIPPED",
        "stdout": "CANARY_COMMAND_STDOUT_SHOULD_BE_STRIPPED",
        "stderr": "CANARY_COMMAND_STDERR_SHOULD_BE_STRIPPED",
        "api_key": test_key,
        "anthropic_api_key": "sk-" + "ant-canary-key",
        "nested": {
            "token": "secret_bearer_token",
            "safe_metric": 100,
            "raw_output": "ls -la secret",
        },
        "summary": f"Ran step with {summary_key} successfully.",
    }

    sanitized = TelemetryBroadcaster.sanitize_telemetry_dict(raw_payload)

    # Sensitive fields removed completely
    assert "prompt" not in sanitized
    assert "file_content" not in sanitized
    assert "stdout" not in sanitized
    assert "stderr" not in sanitized
    assert "api_key" not in sanitized
    assert "anthropic_api_key" not in sanitized
    assert "token" not in sanitized["nested"]
    assert "raw_output" not in sanitized["nested"]

    # Structural / metrics preserved
    assert sanitized["arm_id"] == 2
    assert sanitized["role"] == "backend"
    assert sanitized["nested"]["safe_metric"] == 100

    # Free-text strings redacted
    assert "CANARY" not in str(sanitized)
    assert "[REDACTED_KEY]" in sanitized["summary"]


def test_captured_telemetry_contains_no_canary(ephemeral_server):
    """Stream simulated telemetry with canary strings and verify broadcaster history is clean."""
    canary_prompt = "CANARY_LLM_PROMPT_PHASE_1_5_VERIFY"
    canary_file = "CANARY_WORKSPACE_FILE_CONTENT_SECRET"
    canary_key = "sk-" + "ant-api03-CANARY1234567890abcdef-SECRET"

    event = SwarmTelemetryEvent(
        event_type="STEP",
        arm_id=1,
        role="database",
        status="complete",
        surprise=0.15,
        threshold=0.5,
        summary=f"Created schema with key {canary_key}",
        payload={
            "prompt": canary_prompt,
            "file_content": canary_file,
            "api_key": canary_key,
            "safe_counter": 42,
        },
    )

    ephemeral_server.broadcast(event)
    history = ephemeral_server.get_history()
    assert len(history) == 1

    history_str = str(history)
    assert canary_prompt not in history_str
    assert canary_file not in history_str
    assert canary_key not in history_str
    assert "[REDACTED_KEY]" in history[0]["summary"]
    assert history[0]["payload"]["safe_counter"] == 42


# ==============================================================================
# 5. Config Permissions, Hardening & Masking Tests
# ==============================================================================


def test_mask_credential():
    """Verify mask_credential produces first 3 characters followed by '****'."""
    assert mask_credential("sk-" + "ant-api03-1234567890abcdef") == "sk-****"
    assert mask_credential("AIzaSyDummyKey123") == "AIz****"
    assert mask_credential("secret_key_value") == "sec****"
    assert mask_credential("ab") == "ab****"
    assert mask_credential("") == ""
    assert mask_credential(None) == ""


def test_config_directory_and_file_permissions(tmp_path, monkeypatch, capsys):
    """Verify ~/.octoflow is 0700, config.json is 0600, and looser modes are auto-hardened."""
    monkeypatch.setenv("HOME", str(tmp_path))

    octo_dir = tmp_path / ".octoflow"
    cfg_file = octo_dir / "config.json"

    # Save secure config
    save_secure_config(
        {"default_model": "mock", "anthropic_api_key": "sk-" + "ant-secret1234567890"}
    )

    assert octo_dir.exists()
    assert cfg_file.exists()

    # Verify initial permissions (0700 for dir, 0600 for file)
    dir_mode = stat.S_IMODE(octo_dir.stat().st_mode)
    file_mode = stat.S_IMODE(cfg_file.stat().st_mode)
    assert dir_mode == 0o700, f"Expected dir mode 0700, got {oct(dir_mode)}"
    assert file_mode == 0o600, f"Expected file mode 0600, got {oct(file_mode)}"

    # Intentionally loosen permissions to 0644 (world readable)
    cfg_file.chmod(0o644)
    octo_dir.chmod(0o755)
    assert stat.S_IMODE(cfg_file.stat().st_mode) == 0o644
    assert stat.S_IMODE(octo_dir.stat().st_mode) == 0o755

    # On load, permissions must be automatically tightened
    loaded = load_secure_config(cfg_file)
    assert loaded.get("default_model") == "mock"

    fixed_dir_mode = stat.S_IMODE(octo_dir.stat().st_mode)
    fixed_file_mode = stat.S_IMODE(cfg_file.stat().st_mode)
    assert fixed_dir_mode == 0o700, f"Expected hardened dir mode 0700, got {oct(fixed_dir_mode)}"
    assert fixed_file_mode == 0o600, f"Expected hardened file mode 0600, got {oct(fixed_file_mode)}"

    # Check for printed one-line hardening notices
    captured = capsys.readouterr()
    assert "Hardened permissions on" in captured.out
    assert "0o700" in captured.out
    assert "0o600" in captured.out


def test_llm_pool_endpoint_masks_credentials(ephemeral_server, tmp_path, monkeypatch):
    """Verify /llm/pool GET endpoint never exposes raw credentials, displaying masked keys."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg_data = {
        "llm_pool": [
            {
                "id": "anthropic_primary",
                "provider": "anthropic",
                "name": "Anthropic Claude",
                "model": "claude-3-5-sonnet",
                "api_key": "sk-" + "ant-api03-CANARY1234567890abcdef",
                "enabled": True,
                "priority": 1,
            }
        ]
    }
    save_secure_config(cfg_data)

    res = httpx.get(f"http://127.0.0.1:{ephemeral_server.port}/llm/pool")
    assert res.status_code == 200
    data = res.json()
    pool = data.get("pool", [])
    assert len(pool) == 1
    entry = pool[0]
    assert "api_key" not in entry
    assert entry.get("masked_key") == "sk-****"
    assert entry.get("has_key") is True
