"""Comprehensive Conformance Tests for OctoFlow MCP JSON-RPC 2.0 Stdio Server.

Spawns the MCP server as a real subprocess, feeds raw JSON-RPC over stdin,
and verifies:
1. JSON-RPC 2.0 handshake (initialize, protocolVersion negotiation, serverInfo, capabilities)
2. Ping and initialized notifications handling
3. Strict stdio hygiene (zero extraneous stdout lines, 100% valid JSON-RPC payloads)
4. Tool discovery (all 8 canonical tools, Draft 2020-12 valid inputSchema, side effects docs)
5. Tool execution (inspect_arms, synchronous run, async run with status polling, backward compat aliases)
6. Protocol errors (invalid JSON -> -32700, unknown method -> -32601, unknown tool -> -32601, missing param -> -32602)
7. Workspace confinement (--dir boundaries, traversal rejection -> isError=True)
8. Clean shutdown on closed stdin (exit code 0, no zombies)
9. Repo manifests conformance (.mcp.json and .claude-plugin/plugin.json use canonical command form)
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator


class MCPClientSession:
    """Helper client session managing an MCP server subprocess over stdio."""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.cmd = [
            sys.executable,
            "-m",
            "octoflow.cli",
            "mcp",
            "--dir",
            str(workspace_dir),
        ]
        self.env = dict(os.environ)
        self.env["OCTOFLOW_DRY_RUN"] = "1"
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=self.env,
        )

    def send_line(self, raw_line: str) -> None:
        """Send a raw line to the server's stdin."""
        assert self.proc.stdin is not None
        self.proc.stdin.write(raw_line.strip() + "\n")
        self.proc.stdin.flush()

    def send_request(self, msg: dict) -> None:
        """Send a JSON-RPC dictionary request."""
        self.send_line(json.dumps(msg))

    def read_line(self, timeout: float = 8.0) -> str:
        """Read a single line from server stdout with a deadline."""
        assert self.proc.stdout is not None
        start = time.time()
        while time.time() - start < timeout:
            line = self.proc.stdout.readline()
            if line:
                return line
            if self.proc.poll() is not None:
                break
            time.sleep(0.05)
        raise TimeoutError(f"Timed out waiting for stdout from MCP server after {timeout}s")

    def read_response(self, timeout: float = 8.0) -> dict:
        """Read a single line and assert it is a valid JSON-RPC 2.0 payload."""
        line = self.read_line(timeout=timeout)
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            pytest.fail(f"Stdio hygiene violation: stdout emitted invalid JSON: {line!r} ({exc})")
        assert isinstance(payload, dict), f"Expected JSON object, got: {type(payload)}"
        assert payload.get("jsonrpc") == "2.0", f"Missing jsonrpc 2.0 version: {payload}"
        return payload

    def close(self) -> int:
        """Close stdin and wait for clean process shutdown."""
        if self.proc.stdin and not self.proc.stdin.closed:
            self.proc.stdin.close()
        code = self.proc.wait(timeout=5.0)
        return code


@pytest.fixture
def mcp_session(tmp_path: Path):
    """Spawns an MCP server subprocess in a clean temp directory."""
    session = MCPClientSession(workspace_dir=str(tmp_path))
    try:
        yield session
    finally:
        try:
            session.close()
        except Exception:
            session.proc.kill()


def test_mcp_handshake_lifecycle(mcp_session: MCPClientSession):
    """Verify initialize, initialized notification, and ping handshake."""
    # 1. initialize
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }
    )
    init_res = mcp_session.read_response()
    assert init_res["id"] == 1
    assert "result" in init_res
    res = init_res["result"]
    assert res["protocolVersion"] == "2024-11-05"
    assert res["serverInfo"]["name"] == "octoflow"
    assert "tools" in res["capabilities"]

    # 2. notifications/initialized (Notification: no response expected)
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
    )
    # To verify nothing was emitted for notification, send a ping and check next response is ping's
    mcp_session.send_request({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}})
    ping_res = mcp_session.read_response()
    assert ping_res["id"] == 2
    assert ping_res["result"] == {}


def test_mcp_tools_list_and_schemas(mcp_session: MCPClientSession):
    """Verify all 8 canonical tools are registered and expose Draft 2020-12 valid schemas."""
    mcp_session.send_request({"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {}})
    resp = mcp_session.read_response()
    assert resp["id"] == 10
    tools = resp["result"]["tools"]

    canonical_names = [t["name"] for t in tools]
    expected_tools = [
        "octoflow_run",
        "octoflow_get_run_status",
        "octoflow_inspect_arms",
        "octoflow_recall_memory",
        "octoflow_audit",
        "octoflow_guild_list",
        "octoflow_receipt",
        "octoflow_read_file",
        "octoflow_search_codebase",
        "octoflow_search_symbols",
        "octoflow_find_callers",
        "octoflow_switch_guild",
        "octoflow_octopolis",
    ]
    assert len(tools) == 13, f"Expected exactly 13 canonical tools, got: {canonical_names}"
    for exp in expected_tools:
        assert exp in canonical_names, f"Expected tool '{exp}' not in tools list"

    # Validate each tool's schema against JSON Schema Draft 2020-12
    for tool in tools:
        schema = tool["inputSchema"]
        assert schema.get("type") == "object", f"Tool {tool['name']} inputSchema must be object"
        # Validate schema structure
        Draft202012Validator.check_schema(schema)
        # Verify description exists and documents side effects / scope
        desc = tool.get("description", "")
        assert len(desc) > 20, f"Tool {tool['name']} lacks descriptive documentation"

    # Verify specific tool description guarantees
    run_tool = next(t for t in tools if t["name"] == "octoflow_run")
    assert "side effect" in run_tool["description"].lower()
    assert "workspace" in run_tool["description"].lower()

    read_tool = next(t for t in tools if t["name"] == "octoflow_read_file")
    assert "workspace" in read_tool["description"].lower()
    assert "path" in read_tool["inputSchema"]["required"]


def test_mcp_tool_execution_synchronous(mcp_session: MCPClientSession):
    """Verify synchronous tool execution for inspect_arms and octoflow_run."""
    # 1. octoflow_inspect_arms
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/call",
            "params": {"name": "octoflow_inspect_arms", "arguments": {}},
        }
    )
    resp = mcp_session.read_response()
    assert resp["id"] == 20
    assert resp["result"]["isError"] is False
    content_text = resp["result"]["content"][0]["text"]
    assert "Arm Ganglia Status" in content_text

    # 2. octoflow_run (dry run, synchronous)
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {
                "name": "octoflow_run",
                "arguments": {
                    "objective": "Verify MCP integration test",
                    "max_cycles": 1,
                    "dry_run": True,
                },
            },
        }
    )
    run_resp = mcp_session.read_response(timeout=10.0)
    assert run_resp["id"] == 21
    assert run_resp["result"]["isError"] is False
    text = run_resp["result"]["content"][0]["text"]
    assert "OctoFlow Cephalopod Swarm Run Completed" in text


def test_mcp_async_run_and_status_polling(mcp_session: MCPClientSession):
    """Verify async run queuing and status polling via octoflow_get_run_status."""
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "tools/call",
            "params": {
                "name": "octoflow_run",
                "arguments": {
                    "objective": "Build async telemetry harness",
                    "async": True,
                    "max_cycles": 2,
                    "dry_run": True,
                },
            },
        }
    )
    resp = mcp_session.read_response()
    assert resp["id"] == 30
    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][1]["text"])
    run_id = payload["run_id"]
    assert payload["status"] == "RUNNING"
    assert payload["async"] is True

    # Poll status
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 31,
            "method": "tools/call",
            "params": {
                "name": "octoflow_get_run_status",
                "arguments": {"run_id": run_id},
            },
        }
    )
    status_resp = mcp_session.read_response()
    assert status_resp["id"] == 31
    assert status_resp["result"]["isError"] is False
    status_text = status_resp["result"]["content"][0]["text"]
    assert "Arm Cycle:" in status_text
    assert "Latest Thought:" in status_text


def test_mcp_backward_compatibility_aliases(mcp_session: MCPClientSession):
    """Verify legacy tool aliases (octoflow_run_swarm, status, octoflow_arms_status)."""
    # 1. Alias octoflow_arms_status
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 40,
            "method": "tools/call",
            "params": {"name": "octoflow_arms_status", "arguments": {}},
        }
    )
    resp1 = mcp_session.read_response()
    assert resp1["id"] == 40
    assert resp1["result"]["isError"] is False

    # 2. Alias octoflow_run_swarm
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 41,
            "method": "tools/call",
            "params": {
                "name": "octoflow_run_swarm",
                "arguments": {
                    "objective": "Test alias dispatch",
                    "async_run": True,
                },
            },
        }
    )
    resp2 = mcp_session.read_response()
    assert resp2["id"] == 41
    assert resp2["result"]["isError"] is False
    payload = json.loads(resp2["result"]["content"][1]["text"])
    run_id = payload["run_id"]

    # 3. Alias status
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "tools/call",
            "params": {"name": "status", "arguments": {"run_id": run_id}},
        }
    )
    resp3 = mcp_session.read_response()
    assert resp3["id"] == 42
    assert resp3["result"]["isError"] is False


def test_mcp_error_protocol_handling(mcp_session: MCPClientSession):
    """Verify JSON-RPC 2.0 error codes (-32700, -32601, -32602)."""
    # 1. Parse error (-32700) on malformed JSON
    mcp_session.send_line("{ bad json: ")
    err_parse = mcp_session.read_response()
    assert err_parse["id"] is None
    assert err_parse["error"]["code"] == -32700

    # 2. Unknown method (-32601)
    mcp_session.send_request({"jsonrpc": "2.0", "id": 50, "method": "invalid/method", "params": {}})
    err_method = mcp_session.read_response()
    assert err_method["id"] == 50
    assert err_method["error"]["code"] == -32601

    # 3. Unknown tool (-32601)
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 51,
            "method": "tools/call",
            "params": {"name": "nonexistent_neural_arm", "arguments": {}},
        }
    )
    err_tool = mcp_session.read_response()
    assert err_tool["id"] == 51
    assert err_tool["error"]["code"] == -32601

    # 4. Missing required parameter (-32602)
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 52,
            "method": "tools/call",
            "params": {"name": "octoflow_run", "arguments": {}},  # objective missing
        }
    )
    err_params = mcp_session.read_response()
    assert err_params["id"] == 52
    assert err_params["error"]["code"] == -32602
    assert "objective" in err_params["error"]["message"]


def test_mcp_workspace_confinement(mcp_session: MCPClientSession):
    """Verify path traversal outside workspace is refused with isError=True without server crash."""
    # 1. octoflow_read_file with traversal
    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 60,
            "method": "tools/call",
            "params": {
                "name": "octoflow_read_file",
                "arguments": {"path": "../../../etc/passwd"},
            },
        }
    )
    resp = mcp_session.read_response()
    assert resp["id"] == 60
    assert resp["result"]["isError"] is True
    err_text = resp["result"]["content"][0]["text"]
    assert "Access denied" in err_text or "Path traversal" in err_text

    # 2. Valid workspace read
    test_file = Path(mcp_session.workspace_dir) / "safe_file.txt"
    test_file.write_text("octoflow safe content\nsecond line\n", encoding="utf-8")

    mcp_session.send_request(
        {
            "jsonrpc": "2.0",
            "id": 61,
            "method": "tools/call",
            "params": {
                "name": "octoflow_read_file",
                "arguments": {"path": "safe_file.txt"},
            },
        }
    )
    valid_resp = mcp_session.read_response()
    assert valid_resp["id"] == 61
    assert valid_resp["result"]["isError"] is False
    assert "octoflow safe content" in valid_resp["result"]["content"][0]["text"]


def test_mcp_clean_shutdown_on_eof(tmp_path: Path):
    """Verify server exits cleanly with return code 0 when stdin is closed."""
    session = MCPClientSession(workspace_dir=str(tmp_path))
    # Send ping to confirm ready
    session.send_request({"jsonrpc": "2.0", "id": 70, "method": "ping", "params": {}})
    session.read_response()

    # Close stdin (EOF)
    code = session.close()
    assert code == 0, f"Expected returncode 0 on stdin EOF, got: {code}"


def test_manifest_command_format():
    """Verify .mcp.json and .claude-plugin/plugin.json use canonical 'octoflow mcp' without absolute paths."""
    repo_root = Path(__file__).resolve().parent.parent

    # 1. .mcp.json
    mcp_json_path = repo_root / ".mcp.json"
    assert mcp_json_path.exists(), ".mcp.json missing from repository root"
    mcp_data = json.loads(mcp_json_path.read_text(encoding="utf-8"))
    server_entry = mcp_data["mcpServers"]["octoflow"]
    assert server_entry["command"] == "octoflow"
    assert server_entry["args"] == ["mcp"]
    # Check for absence of absolute paths
    assert not any(arg.startswith("/") or arg.startswith("~") for arg in server_entry["args"])

    # 2. .claude-plugin/plugin.json
    plugin_json_path = repo_root / ".claude-plugin" / "plugin.json"
    assert plugin_json_path.exists(), ".claude-plugin/plugin.json missing"
    plugin_data = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    mcp_block = plugin_data["mcp"]
    assert mcp_block["command"] == "octoflow"
    assert mcp_block["args"] == ["mcp"]
    assert not any(arg.startswith("/") or arg.startswith("~") for arg in mcp_block["args"])
