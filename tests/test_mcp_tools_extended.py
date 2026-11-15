"""Comprehensive tests for extended MCP tools and 1-command installer CLI.

Verifies:
1. Tool Discovery: All 12 canonical tools are exposed with valid inputSchema.
2. octoflow_search_codebase: Semantic RAG retrieval across workspace code chunks.
3. octoflow_search_symbols: AST symbol connectome queries (classes, functions, methods).
4. octoflow_find_callers: Call graph edge traversal for callers of a symbol.
5. octoflow_switch_guild: Dynamic switching to any of the 64 personas across 8 domain guilds.
6. 1-Command Installer CLI: 'octoflow mcp install --client claude-code' creates valid configs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from octoflow.cli import app
from octoflow.commands.mcp import install_mcp
from octoflow.mcp import OctoFlowMCPServer


@pytest.fixture
def sample_code_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with Python source code for AST and RAG indexing."""
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)

    math_file = ws / "math_ops.py"
    math_file.write_text(
        '"""Mathematical operations utility."""\n\n'
        "def compute_fibonacci(n: int) -> int:\n"
        '    """Compute n-th Fibonacci number recursively."""\n'
        "    if n <= 1:\n"
        "        return n\n"
        "    return compute_fibonacci(n - 1) + compute_fibonacci(n - 2)\n\n"
        "class ArithmeticEngine:\n"
        '    """High performance arithmetic computation engine."""\n'
        "    def calculate_factorial(self, n: int) -> int:\n"
        '        """Calculate factorial of n."""\n'
        "        if n <= 1:\n"
        "            return 1\n"
        "        return n * self.calculate_factorial(n - 1)\n\n"
        "def run_engine_pipeline() -> int:\n"
        '    """Orchestrate engine calculations."""\n'
        "    engine = ArithmeticEngine()\n"
        "    fib = compute_fibonacci(5)\n"
        "    fact = engine.calculate_factorial(fib)\n"
        "    return fact\n",
        encoding="utf-8",
    )
    return ws


@pytest.mark.anyio
async def test_mcp_all_tools_registered(sample_code_workspace: Path) -> None:
    """Verify OctoFlow MCP server registers all canonical tools."""
    server = OctoFlowMCPServer(workspace_dir=str(sample_code_workspace))
    tools = server.registry.list_tools()
    tool_names = [t.name for t in tools]

    expected = [
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
    assert len(tools) == 13
    for exp in expected:
        assert exp in tool_names, f"Expected tool '{exp}' not in registered tools"


@pytest.mark.anyio
async def test_mcp_search_codebase_tool(sample_code_workspace: Path) -> None:
    """Verify octoflow_search_codebase returns relevant code chunks and similarity."""
    server = OctoFlowMCPServer(workspace_dir=str(sample_code_workspace))

    # Test valid search
    res = await server.registry.call_tool(
        "octoflow_search_codebase", {"query": "Fibonacci calculation", "top_k": 3}
    )
    assert not res.isError
    assert len(res.content) == 2
    human_text = res.content[0]["text"]
    assert "Codebase RAG Search Results" in human_text
    assert "compute_fibonacci" in human_text

    raw_json = json.loads(res.content[1]["text"])
    assert len(raw_json) >= 1
    assert "file_path" in raw_json[0]
    assert "similarity" in raw_json[0]

    # Test empty query error handling
    err_res = await server.registry.call_tool("octoflow_search_codebase", {"query": ""})
    assert err_res.isError
    assert "required" in err_res.content[0]["text"].lower()


@pytest.mark.anyio
async def test_mcp_search_symbols_tool(sample_code_workspace: Path) -> None:
    """Verify octoflow_search_symbols returns classes, functions, methods from AST connectome."""
    server = OctoFlowMCPServer(workspace_dir=str(sample_code_workspace))

    res = await server.registry.call_tool(
        "octoflow_search_symbols", {"query": "ArithmeticEngine", "top_k": 5}
    )
    assert not res.isError
    human_text = res.content[0]["text"]
    assert "ArithmeticEngine" in human_text

    raw_symbols = json.loads(res.content[1]["text"])
    matches = [s["name"] for s in raw_symbols]
    assert "ArithmeticEngine" in matches

    # Test method search
    res_meth = await server.registry.call_tool(
        "octoflow_search_symbols", {"query": "calculate_factorial"}
    )
    assert not res_meth.isError
    raw_meth = json.loads(res_meth.content[1]["text"])
    assert any("calculate_factorial" in s["name"] for s in raw_meth)


@pytest.mark.anyio
async def test_mcp_find_callers_tool(sample_code_workspace: Path) -> None:
    """Verify octoflow_find_callers locates callers from the AST call graph."""
    server = OctoFlowMCPServer(workspace_dir=str(sample_code_workspace))

    res = await server.registry.call_tool(
        "octoflow_find_callers", {"symbol_name": "compute_fibonacci"}
    )
    assert not res.isError
    human_text = res.content[0]["text"]
    assert "Callers of 'compute_fibonacci'" in human_text

    raw_callers = json.loads(res.content[1]["text"])
    callers = [c["caller"] for c in raw_callers]
    assert "run_engine_pipeline" in callers or "compute_fibonacci" in callers


@pytest.mark.anyio
async def test_mcp_switch_guild_tool(sample_code_workspace: Path) -> None:
    """Verify octoflow_switch_guild dynamically activates 64 personas across domain guilds."""
    server = OctoFlowMCPServer(workspace_dir=str(sample_code_workspace))

    # Switch to web_fullstack
    res = await server.registry.call_tool(
        "octoflow_switch_guild", {"guild_name": "web_fullstack"}
    )
    assert not res.isError
    assert server.current_guild == "web_fullstack"
    human_text = res.content[0]["text"]
    assert "web_fullstack" in human_text
    assert "Arm 0:" in human_text

    raw_payload = json.loads(res.content[1]["text"])
    assert raw_payload["guild"] == "web_fullstack"
    assert len(raw_payload["arms"]) == 8

    # Switch using alias 'secops' -> cybersec_ops
    res_sec = await server.registry.call_tool(
        "octoflow_switch_guild", {"guild_name": "secops"}
    )
    assert not res_sec.isError
    assert server.current_guild == "cybersec_ops"

    # Test non-existent guild
    res_err = await server.registry.call_tool(
        "octoflow_switch_guild", {"guild_name": "non_existent_guild_xyz"}
    )
    assert res_err.isError


def test_install_mcp_claude_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify install_mcp writes ~/.claude.json, .mcp.json, and .claude-plugin/plugin.json."""
    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    ws = tmp_path / "proj"
    ws.mkdir(parents=True, exist_ok=True)

    result = install_mcp(workspace=str(ws), client="claude-code", quiet=True)
    assert result["claude_code"] is True
    assert result["workspace_mcp"] is True

    # 1. ~/.claude.json
    claude_cfg = fake_home / ".claude.json"
    assert claude_cfg.exists()
    claude_data = json.loads(claude_cfg.read_text(encoding="utf-8"))
    assert "mcpServers" in claude_data
    assert "octoflow" in claude_data["mcpServers"]
    assert claude_data["mcpServers"]["octoflow"]["args"] == ["mcp"]

    # 2. .mcp.json
    ws_mcp = ws / ".mcp.json"
    assert ws_mcp.exists()
    ws_mcp_data = json.loads(ws_mcp.read_text(encoding="utf-8"))
    assert "mcpServers" in ws_mcp_data
    assert "octoflow" in ws_mcp_data["mcpServers"]
    assert ws_mcp_data["mcpServers"]["octoflow"]["args"] == ["mcp"]

    # 3. .claude-plugin/plugin.json
    plugin_manifest = ws / ".claude-plugin" / "plugin.json"
    assert plugin_manifest.exists()
    manifest_data = json.loads(plugin_manifest.read_text(encoding="utf-8"))
    assert manifest_data["name"] == "octoflow"
    assert manifest_data["mcp"]["args"] == ["mcp"]


def test_cli_mcp_install_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify CLI 'octoflow mcp install --client claude-code' executes correctly."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    ws = tmp_path / "cli_ws"
    ws.mkdir(parents=True, exist_ok=True)

    runner = CliRunner()
    res = runner.invoke(app, ["mcp", "install", "--client", "claude-code", "--dir", str(ws)])
    assert res.exit_code == 0
    assert "OctoFlow Model Context Protocol (MCP) Integration" in res.output
    assert "Claude Code MCP Suite" in res.output

    # Verify configs were created
    assert (fake_home / ".claude.json").exists()
    assert (ws / ".mcp.json").exists()
    assert (ws / ".claude-plugin" / "plugin.json").exists()
