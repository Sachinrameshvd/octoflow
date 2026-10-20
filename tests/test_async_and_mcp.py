"""Comprehensive Unit Tests for Async Parallel Execution, Vertical Lobe Persistence, and MCP.

Verifies:
1. True async parallel arm execution via conductor.arun_swarm()
2. WorkspaceSandbox async tool methods (aread_file, awrite_file, arun_command)
3. VerticalLobeMemory cross-session disk persistence (save/load)
4. OctoFlowMCPServer JSON-RPC 2.0 protocol handling (initialize, tools/list, tools/call)
"""

import json
import os
import shutil
import tempfile
import pytest
import numpy as np

from octoflow.config import OctoFlowConfig, SwarmMorphology
from octoflow.conductor import SupraesophagealConductor
from octoflow.tools import WorkspaceSandbox
from octoflow.memory import VerticalLobeMemory
from octoflow.provider import MockLLMProvider
from octoflow.mcp import OctoFlowMCPServer, MCPRegistry, MCPToolSchema, MCPToolCallResult


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace folder and clean up after."""
    d = tempfile.mkdtemp(prefix="octoflow_async_ws_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.anyio
async def test_workspace_sandbox_async(temp_workspace):
    """Verify non-blocking async tool operations in WorkspaceSandbox."""
    sandbox = WorkspaceSandbox(temp_workspace)

    # Write file async
    res_w = await sandbox.awrite_file("async_test.py", "x = 42\n", arm_id=0)
    assert res_w.success is True
    assert res_w.diff_lines == 1

    # Read file async
    res_r = await sandbox.aread_file("async_test.py")
    assert res_r.success is True
    assert res_r.stdout == "x = 42\n"

    # List dir async
    res_l = await sandbox.alist_dir(".")
    assert res_l.success is True
    assert "async_test.py" in res_l.stdout

    # Run command async
    res_c = await sandbox.arun_command("python3 -c 'print(100 + 200)'")
    assert res_c.success is True
    assert "300" in res_c.stdout


@pytest.mark.anyio
async def test_async_parallel_swarm_execution(temp_workspace):
    """Verify concurrent async parallel execution of all 8 arm ganglia."""
    cfg = OctoFlowConfig(
        workspace_dir=temp_workspace,
        morphology=SwarmMorphology.SOFTWARE_DEV,
        model_provider="mock",
    )
    conductor = SupraesophagealConductor(config=cfg)

    # Run swarm concurrently
    result = await conductor.arun_swarm(
        objective="Build a real-time markdown editor with FastAPI and Vue",
        max_cycles=3,
    )

    assert result["objective"] != ""
    assert result["quiescent_arms"] >= 1
    assert result["tokens_consumed"] > 0
    assert result["token_reduction_pct"] >= 50.0  # >70% expected
    assert result["execution_time_seconds"] > 0.0


def test_vertical_lobe_memory_persistence(temp_workspace):
    """Verify cross-session persistence of learned Hebbian patterns."""
    mem1 = VerticalLobeMemory(feature_dim=16)

    # Consolidate a custom learned bug fix
    err_vec = np.zeros(16, dtype=np.float32)
    err_vec[3] = 1.0
    mem1.consolidate(err_vec, "DatabaseConnectionTimeout", "Retry with exponential backoff connection pool.")

    save_path = os.path.join(temp_workspace, "persisted_lobe.json")
    mem1.save(save_path)
    assert os.path.exists(save_path)

    # Load in a fresh memory instance
    mem2 = VerticalLobeMemory(feature_dim=16)
    loaded = mem2.load(save_path)
    assert loaded is True

    # Verify recalled pattern
    match = mem2.recall(err_vec)
    assert match is not None
    guidance, conf = match
    assert "exponential backoff" in guidance
    assert conf >= 0.90


@pytest.mark.anyio
async def test_mcp_server_protocol(temp_workspace):
    """Verify MCP JSON-RPC 2.0 initialize, tools/list, and tools/call handling."""
    server = OctoFlowMCPServer(workspace_dir=temp_workspace)

    # 1. Initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }
    init_resp = await server.handle_json_rpc_message(init_req)
    assert init_resp["id"] == 1
    assert init_resp["result"]["serverInfo"]["name"] == "octoflow-mcp"
    assert "tools" in init_resp["result"]["capabilities"]

    # 2. Tools list
    list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    list_resp = await server.handle_json_rpc_message(list_req)
    assert list_resp["id"] == 2
    tool_names = [t["name"] for t in list_resp["result"]["tools"]]
    assert "octoflow_run_swarm" in tool_names
    assert "octoflow_inspect_arms" in tool_names
    assert "octoflow_recall_memory" in tool_names

    # 3. Call inspect_arms
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "octoflow_inspect_arms", "arguments": {}},
    }
    call_resp = await server.handle_json_rpc_message(call_req)
    assert call_resp["id"] == 3
    assert call_resp["result"]["isError"] is False
    assert "Arm Ganglia Status" in call_resp["result"]["content"][0]["text"]

    # 4. Call run_swarm via MCP
    run_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "octoflow_run_swarm",
            "arguments": {
                "objective": "Design an MCP tool client interface",
                "max_cycles": 2,
            },
        },
    }
    run_resp = await server.handle_json_rpc_message(run_req)
    assert run_resp["id"] == 4
    assert "OctoFlow Cephalopod Swarm Run Completed" in run_resp["result"]["content"][0]["text"]


def test_frontier_llm_providers():
    """Verify Gemini, Grok, and DeepSeek providers initialize and route properly."""
    from octoflow.provider import GeminiProvider, GrokProvider, DeepSeekProvider, _build_single_provider
    from octoflow.config import OctoFlowConfig

    # 1. Direct class instantiation
    gemini = GeminiProvider(api_key="test-gemini-key")
    assert gemini.model == "gemini-2.0-flash"
    assert "googleapis.com" in gemini.base_url

    grok = GrokProvider(api_key="test-grok-key")
    assert grok.model == "grok-2-1212"
    assert "api.x.ai" in grok.base_url

    deepseek = DeepSeekProvider(api_key="test-deepseek-key")
    assert deepseek.model == "deepseek-chat"
    assert "deepseek.com" in deepseek.base_url

    # 2. Config factory routing
    cfg_gemini = OctoFlowConfig(model_provider="gemini", gemini_api_key="dummy-key")
    p_gemini = _build_single_provider("gemini", cfg_gemini)
    assert isinstance(p_gemini, GeminiProvider)

    cfg_grok = OctoFlowConfig(model_provider="grok", grok_api_key="dummy-key")
    p_grok = _build_single_provider("grok", cfg_grok)
    assert isinstance(p_grok, GrokProvider)

    cfg_deepseek = OctoFlowConfig(model_provider="deepseek", deepseek_api_key="dummy-key")
    p_deepseek = _build_single_provider("deepseek", cfg_deepseek)
    assert isinstance(p_deepseek, DeepSeekProvider)


def test_cascade_pool_token_failover():
    """Verify CascadePoolLLMProvider hot-swaps to the next LLM when tokens deplete or 429 occurs."""
    from octoflow.config import LLMConfigEntry
    from octoflow.provider import CascadePoolLLMProvider, MockLLMProvider, BaseLLMProvider, LLMResponse

    # Create dummy failing provider (simulates 429 quota exhaustion)
    class ExhaustedQuotaProvider(BaseLLMProvider):
        def generate(self, prompt, system_prompt="", temperature=0.2, max_tokens=2048):
            raise RuntimeError("HTTP 429: Resource exhausted / monthly token quota reached")

    # Create backup provider
    class BackupProvider(BaseLLMProvider):
        def generate(self, prompt, system_prompt="", temperature=0.2, max_tokens=2048):
            return LLMResponse(content="Backup model completed successfully!", total_tokens=150)

    entries = [
        LLMConfigEntry(id="gemini-1", provider="gemini", name="Google Gemini Flash", priority=1),
        LLMConfigEntry(id="grok-1", provider="grok", name="xAI Grok-2", priority=2),
    ]

    failovers_logged = []
    cascade = CascadePoolLLMProvider(
        entries=entries,
        on_failover=lambda ev: failovers_logged.append(ev),
    )

    # Inject mock behavior for the test
    cascade.providers = [ExhaustedQuotaProvider(), BackupProvider()]

    # Execute generation: First provider will throw 429, cascade should catch and switch to provider 2
    res = cascade.generate("Generate resume parsing engine")
    assert "Backup model completed successfully!" in res.content
    assert res.total_tokens == 150

    # Verify telemetry and failover log
    summary = cascade.get_status_summary()
    assert summary[0]["status"] == "EXHAUSTED"
    assert summary[0]["failover_count"] == 1
    assert summary[1]["status"] == "ACTIVE"
    assert summary[1]["tokens_used"] == 150

    assert len(failovers_logged) == 1
    assert failovers_logged[0]["from_id"] == "gemini-1"
    assert failovers_logged[0]["to_id"] == "grok-1"
    assert failovers_logged[0]["is_rate_limit"] is True

