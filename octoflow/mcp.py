"""Model Context Protocol (MCP) Client & Server Architecture for OctoFlow.

Enables two-way MCP integration:
1. MCP Client: OctoFlow arms can connect to and wield any external MCP tool server
   (Postgres, GitHub, Puppeteer, Brave Search, Filesystem).
2. MCP Server: Exposes OctoFlow as a full JSON-RPC 2.0 MCP tool server to Claude Code,
   Cursor, Antigravity IDE, and external agent orchestrators.
"""

import asyncio
import json
import os
import sys
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from octoflow.conductor import SupraesophagealConductor
from octoflow.config import OctoFlowConfig, SwarmMorphology
from octoflow.outcome import RunMode
from octoflow.tools import ToolResult


class MCPToolSchema(BaseModel):
    """Specification of an MCP tool following the Anthropic MCP specification."""

    name: str
    description: str
    inputSchema: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )


class MCPToolCallRequest(BaseModel):
    """Request to invoke an MCP tool."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPToolCallResult(BaseModel):
    """Standardized result of an MCP tool invocation."""

    content: list[dict[str, Any]]
    isError: bool = False


class MCPRegistry:
    """Central registry of MCP tools accessible to OctoFlow arms."""

    def __init__(self):
        self._tools: dict[str, MCPToolSchema] = {}
        self._handlers: dict[
            str, Callable[[dict[str, Any]], Coroutine[Any, Any, MCPToolCallResult]]
        ] = {}

    def register_tool(
        self,
        schema: MCPToolSchema,
        handler: Callable[[dict[str, Any]], Coroutine[Any, Any, MCPToolCallResult]],
    ) -> None:
        """Register a new MCP tool with its async invocation handler."""
        self._tools[schema.name] = schema
        self._handlers[schema.name] = handler

    def list_tools(self) -> list[MCPToolSchema]:
        """Return all registered MCP tools."""
        return list(self._tools.values())

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> MCPToolCallResult:
        """Dispatch tool invocation to the registered handler."""
        if name not in self._handlers:
            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": f"Error: Tool '{name}' not found in MCP registry."}
                ],
                isError=True,
            )
        try:
            return await self._handlers[name](arguments)
        except Exception as e:
            return MCPToolCallResult(
                content=[{"type": "text", "text": f"Error executing tool '{name}': {str(e)}"}],
                isError=True,
            )


class OctoFlowMCPServer:
    """Full MCP Server implementing JSON-RPC 2.0 over standard I/O.

    Allows Claude Code, Cursor, and Antigravity to invoke OctoFlow cephalopod swarms.
    """

    PROTOCOL_VERSION = "2024-11-05"

    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = str(Path(workspace_dir).expanduser().resolve())
        self.registry = MCPRegistry()
        self.conductor: SupraesophagealConductor | None = None
        self._setup_core_tools()

    def _setup_core_tools(self) -> None:
        """Register OctoFlow swarm tools exposed to Claude Code and MCP hosts."""
        # 1. Tool: octoflow_run_swarm
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_run_swarm",
                description=(
                    "Launch the 8-arm cephalopod multi-agent swarm with sensory surprise gating "
                    "to solve a software engineering, AI/ML research, or full-stack task."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "objective": {
                            "type": "string",
                            "description": "The high-level coding or research goal for the swarm.",
                        },
                        "morphology": {
                            "type": "string",
                            "enum": ["software_dev", "aiml_research", "fullstack_ai"],
                            "description": "Operational preset morphology for the 8 arms.",
                            "default": "software_dev",
                        },
                        "max_cycles": {
                            "type": "integer",
                            "description": "Maximum cognitive problem-solving cycles (default 10).",
                            "default": 10,
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Execute in dry-run mode without real provider credentials.",
                            "default": False,
                        },
                    },
                    "required": ["objective"],
                },
            ),
            handler=self._handle_run_swarm,
        )

        # 2. Tool: octoflow_inspect_arms
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_inspect_arms",
                description="Query the live status, surprise deltas, and current tools of all 8 arm ganglia.",
                inputSchema={"type": "object", "properties": {}},
            ),
            handler=self._handle_inspect_arms,
        )

        # 3. Tool: octoflow_recall_memory
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_recall_memory",
                description="Query the cephalopod Vertical Lobe associative memory for known bug patterns and fixes.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "error_text": {
                            "type": "string",
                            "description": "Error message or traceback to search in associative memory.",
                        }
                    },
                    "required": ["error_text"],
                },
            ),
            handler=self._handle_recall_memory,
        )

    def _get_conductor(
        self, morphology: str = "software_dev", dry_run: bool = False
    ) -> SupraesophagealConductor:
        is_dry = dry_run or (os.getenv("OCTOFLOW_DRY_RUN") == "1")
        config = OctoFlowConfig(
            workspace_dir=self.workspace_dir,
            morphology=SwarmMorphology(morphology),
            model_provider="mock"
            if is_dry
            else ("anthropic" if os.getenv("ANTHROPIC_API_KEY") else "mock"),
            dry_run=is_dry,
        )
        self.conductor = SupraesophagealConductor(config=config)
        return self.conductor

    async def _handle_run_swarm(self, args: dict[str, Any]) -> MCPToolCallResult:
        objective = args["objective"]
        morphology = args.get("morphology", "software_dev")
        max_cycles = int(args.get("max_cycles", 10))
        dry_run = bool(args.get("dry_run", False))

        conductor = self._get_conductor(morphology, dry_run=dry_run)
        result = await conductor.arun_swarm(objective=objective, max_cycles=max_cycles)

        mode_val = (
            result["mode"]
            if "mode" in result
            else (RunMode.DRY_RUN.value if dry_run else RunMode.LIVE.value)
        )
        outcome_val = (
            result["outcome"]
            if "outcome" in result
            else ("complete" if result.get("success") else "failed")
        )
        files_written = result.get("files_written", [])

        status_glyph = (
            "✔" if outcome_val == "complete" else ("◈" if outcome_val == "partial" else "✖")
        )
        text = (
            f"◈ OctoFlow Cephalopod Swarm Run Completed:\n"
            f"• Objective: {result.get('objective', objective)}\n"
            f"• Mode: {mode_val}\n"
            f"• Outcome: {outcome_val}\n"
            f"• Status: {status_glyph} {result.get('status', 'DONE')}\n"
            f"• Files Written: {len(files_written)}\n"
            f"• Quiescent Arms: {result.get('quiescent_arms', 0)}/8\n"
            f"• Problem Cycles: {result.get('total_cycles', 0)}\n"
            f"• Tokens Consumed: {result.get('tokens_consumed', 0):,} (Saved {result.get('token_reduction_pct', 0.0):.1f}% vs Chatty Swarm)\n"
            f"• Execution Time: {result.get('execution_time_seconds', 0.0):.2f}s\n"
            f"• Estimated Cost: ${result.get('total_cost_dollars', 0.0):.4f}\n"
        )
        secrets_redacted = result.get("secrets_redacted", 0)
        if secrets_redacted:
            text += f"• Secrets Redacted: {secrets_redacted} (outbound privacy guard)\n"

        payload = {
            "mode": mode_val,
            "outcome": outcome_val,
            "success": (outcome_val == "complete"),
            "files_written": files_written,
            "tokens_consumed": result.get("tokens_consumed", 0),
            "execution_time_seconds": result.get("execution_time_seconds", 0.0),
        }
        if secrets_redacted:
            payload["secrets_redacted"] = secrets_redacted
        return MCPToolCallResult(
            content=[
                {"type": "text", "text": text},
                {"type": "text", "text": json.dumps(payload)},
            ],
            isError=(outcome_val == "failed"),
        )

    async def _handle_inspect_arms(self, args: dict[str, Any]) -> MCPToolCallResult:
        if self.conductor is None:
            self._get_conductor()

        arm_reports = []
        for arm in self.conductor.arms:
            arm_reports.append(
                f"• Arm {arm.arm_id} [{arm.role.title}]: {arm.status} | "
                f"Surprise: {arm.gate.surprise_history[-1] if arm.gate.surprise_history else 0.0:.3f} / θ={arm.gate.threshold:.2f} | "
                f"Quiescent: {arm.is_quiescent}"
            )
        text = "◈ Cephalopod Arm Ganglia Status:\n" + "\n".join(arm_reports)
        return MCPToolCallResult(content=[{"type": "text", "text": text}])

    async def _handle_recall_memory(self, args: dict[str, Any]) -> MCPToolCallResult:
        if self.conductor is None:
            self._get_conductor()

        error_text = args["error_text"]
        dummy_res = ToolResult(
            tool_name="shell", target="", success=False, returncode=1, stderr=error_text
        )
        obs = self.conductor.arms[0].encoder.encode(dummy_res, as_tensor=False)
        match = self.conductor.memory.recall(obs)

        if match:
            guidance, conf = match
            text = f"◈ Vertical Lobe Hebbian Recall (Confidence {conf:.1%}):\n{guidance}"
        else:
            text = "◈ No existing Hebbian pattern match in Vertical Lobe for this error signature."

        return MCPToolCallResult(content=[{"type": "text", "text": text}])

    async def handle_json_rpc_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single MCP JSON-RPC 2.0 message."""
        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "serverInfo": {"name": "octoflow-mcp", "version": "0.1.0"},
                    "capabilities": {"tools": {"listChanged": False}},
                },
            }
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            tools_data = [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema,
                }
                for t in self.registry.list_tools()
            ]
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools_data}}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            call_res = await self.registry.call_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": call_res.content,
                    "isError": call_res.isError,
                },
            }
        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{method}' not implemented."},
            }

    async def run_stdio(self) -> None:
        """Run the MCP server listening on stdin and responding on stdout."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            try:
                msg = json.loads(line_str)
                resp = await self.handle_json_rpc_message(msg)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
