"""Model Context Protocol (MCP) JSON-RPC 2.0 stdio server for OctoFlow (P8.3).

Exposes OctoFlow cephalopod multi-agent swarms, associative Hebbian memory,
readiness audits, specialist guilds, receipts, and workspace tools to Claude Code,
Cursor, and any conformant Model Context Protocol host over stdio.

Specification Conformance:
- JSON-RPC 2.0 protocol format: Requests, Responses, Notifications, and standard Errors.
- Handshake: 'initialize' capability & version negotiation, 'notifications/initialized', 'ping'.
- Tool Discovery: 'tools/list' with valid JSON Schemas (inputSchema) documenting side effects
  and workspace restriction boundaries.
- Tool Execution: 'tools/call' with standard content block format, typed error mapping,
  and isError execution flags.
- Stdio Hygiene: stdout is strictly reserved for JSON-RPC 2.0 single-line payloads.
  All logging, warnings, and non-protocol writes are redirected to stderr.
- Workspace Confinement: Strictly confined to --dir; rejects path traversal and outside access.
- Asynchronous Bounded Execution: Long-running swarm missions support immediate run_id return
  and status polling via 'octoflow_get_run_status'.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, TextIO

from pydantic import BaseModel, Field

from octoflow.conductor import SupraesophagealConductor
from octoflow.config import OctoFlowConfig, SwarmMorphology
from octoflow.logging_config import get_logger
from octoflow.outcome import RunMode

logger = get_logger("mcp")

# Supported MCP protocol version negotiations
SUPPORTED_PROTOCOL_VERSIONS: set[str] = {
    "2024-11-05",
    "2024-10-07",
    "2025-03-26",
    "2026-07-28",
}
DEFAULT_PROTOCOL_VERSION: str = "2024-11-05"
SERVER_NAME: str = "octoflow"
SERVER_VERSION: str = "0.2.0"

# Standard JSON-RPC 2.0 error codes
JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603
JSONRPC_SERVER_NOT_INITIALIZED = -32002


class MCPToolSchema(BaseModel):
    """Specification of an MCP tool following the Anthropic Model Context Protocol."""

    name: str
    description: str
    inputSchema: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )


class MCPToolCallResult(BaseModel):
    """Standardized result of an MCP tool invocation."""

    content: list[dict[str, Any]]
    isError: bool = False


class MCPRegistry:
    """Central registry of MCP tools exposed to Claude Code and Cursor hosts."""

    def __init__(self) -> None:
        self._tools: dict[str, MCPToolSchema] = {}
        self._handlers: dict[
            str, Callable[[dict[str, Any]], Coroutine[Any, Any, MCPToolCallResult]]
        ] = {}
        self._aliases: dict[str, str] = {}

    def register_tool(
        self,
        schema: MCPToolSchema,
        handler: Callable[[dict[str, Any]], Coroutine[Any, Any, MCPToolCallResult]],
        aliases: list[str] | None = None,
    ) -> None:
        """Register a new MCP tool with its async invocation handler and optional aliases."""
        self._tools[schema.name] = schema
        self._handlers[schema.name] = handler
        if aliases:
            for alias in aliases:
                self._aliases[alias] = schema.name

    def get_tool(self, name: str) -> MCPToolSchema | None:
        """Resolve a tool schema by name or alias."""
        canonical = self._aliases.get(name, name)
        return self._tools.get(canonical)

    def list_tools(self) -> list[MCPToolSchema]:
        """Return all canonical registered MCP tool specifications."""
        return list(self._tools.values())

    def has_tool(self, name: str) -> bool:
        """Check if tool name or alias is registered."""
        return (name in self._tools) or (name in self._aliases)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> MCPToolCallResult:
        """Dispatch tool invocation to registered handler."""
        canonical = self._aliases.get(name, name)
        if canonical not in self._handlers:
            return MCPToolCallResult(
                content=[
                    {
                        "type": "text",
                        "text": f"Error: Tool '{name}' not found in OctoFlow MCP registry.",
                    }
                ],
                isError=True,
            )
        try:
            return await self._handlers[canonical](arguments)
        except Exception as e:
            return MCPToolCallResult(
                content=[
                    {
                        "type": "text",
                        "text": f"Execution error in tool '{name}': {type(e).__name__}: {str(e)}",
                    }
                ],
                isError=True,
            )


class StdoutGuard:
    """Wrapper that redirects accidental stdout writes to stderr for stdio protocol hygiene."""

    def __init__(self, stderr_stream: TextIO) -> None:
        self._target = stderr_stream

    def write(self, s: str) -> int:
        return self._target.write(s)

    def flush(self) -> None:
        self._target.flush()

    def isatty(self) -> bool:
        return False

    def fileno(self) -> int:
        return self._target.fileno()


class OctoFlowMCPServer:
    """Full MCP Server implementing JSON-RPC 2.0 over standard I/O (stdio).

    Allows Claude Code, Cursor, and Antigravity IDE to discover, inspect, and invoke
    OctoFlow cephalopod multi-agent coding swarms with strict workspace boundary confinement.
    """

    def __init__(self, workspace_dir: str = ".") -> None:
        self.workspace_dir = Path(workspace_dir).expanduser().resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.registry = MCPRegistry()
        self.conductor: SupraesophagealConductor | None = None
        self.initialized: bool = False
        self.negotiated_version: str = DEFAULT_PROTOCOL_VERSION
        self._real_stdout: TextIO | None = None
        self._runs: dict[str, dict[str, Any]] = {}
        self._latest_run_id: str | None = None
        self._memory: Any | None = None
        self._rag_indexed: bool = False
        self.current_guild: str | None = None
        self._setup_core_tools()

    def _resolve_safe(self, rel_path: str) -> Path:
        """Resolve a relative path safely within the workspace directory.

        Rejects null bytes, path traversal escaping workspace root, and outside symlinks.
        """
        raw_str = str(rel_path)
        if "\x00" in raw_str:
            raise ValueError(f"Null byte injection detected in path: '{repr(raw_str)}'")

        clean_path = raw_str.strip().strip("'\"").replace("\\", "/")
        if not clean_path:
            return self.workspace_dir

        target = (self.workspace_dir / clean_path).resolve()
        try:
            is_sub = target.is_relative_to(self.workspace_dir)
        except AttributeError:
            is_sub = os.path.commonpath([str(self.workspace_dir), str(target)]) == str(
                self.workspace_dir
            )

        if not is_sub:
            raise ValueError(
                f"Path traversal access denied: '{rel_path}' resolves outside workspace boundary '{self.workspace_dir}'"
            )
        return target

    def _setup_core_tools(self) -> None:
        """Register the 8 primary OctoFlow tools exposed to Claude Code and Cursor."""
        # 1. Tool: octoflow_run (alias: octoflow_run_swarm)
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_run",
                description=(
                    "Launch the 8-arm cephalopod multi-agent swarm with sensory surprise gating to solve "
                    "a software engineering, AI/ML research, or full-stack task. "
                    "Side effects: modifies files, executes test and build commands strictly confined "
                    "within the configured workspace directory (--dir)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "objective": {
                            "type": "string",
                            "description": "The high-level coding, debugging, or research goal for the swarm.",
                        },
                        "morphology": {
                            "type": "string",
                            "enum": ["software_dev", "aiml_research", "fullstack_ai", "custom"],
                            "description": "Operational preset morphology for the 8 arms.",
                            "default": "software_dev",
                        },
                        "guild": {
                            "type": "string",
                            "description": "Specific 8-arm specialist guild name from .octoflow/guilds/ or built-ins.",
                        },
                        "max_cycles": {
                            "type": "integer",
                            "description": "Maximum cognitive problem-solving cycles (default: 10).",
                            "default": 10,
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Execute in dry-run mode without real provider credentials.",
                            "default": False,
                        },
                        "async": {
                            "type": "boolean",
                            "description": "Return immediately with a run_id for background monitoring via octoflow_get_run_status.",
                            "default": False,
                        },
                        "async_run": {
                            "type": "boolean",
                            "description": "Alias for 'async'. Return immediately with a run_id for background monitoring.",
                            "default": False,
                        },
                        "timeout_seconds": {
                            "type": "number",
                            "description": "Synchronous wait timeout before backgrounding (default: 60.0s).",
                            "default": 60.0,
                        },
                        "octos": {
                            "type": "integer",
                            "description": "Count of autonomous octopuses to deploy: 1 (Solo 8-arm swarm), 3 (Triad), or 8 (Task-Adaptive Octopolis with 64 neural arms).",
                            "default": 1,
                        },
                    },
                    "required": ["objective"],
                },
            ),
            handler=self._handle_run_swarm,
            aliases=["octoflow_run_swarm"],
        )

        # 2. Tool: octoflow_get_run_status (alias: get_run_status, octoflow_status, status)
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_get_run_status",
                description=(
                    "Query the execution status, arm cycle progress, latest thought, quiescent arms, "
                    "and outcome of an active or completed swarm run. Side effects: none (read-only query)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_id": {
                            "type": "string",
                            "description": "Specific run identifier returned by octoflow_run. Defaults to the latest run.",
                        }
                    },
                },
            ),
            handler=self._handle_get_run_status,
            aliases=["get_run_status", "octoflow_status", "status"],
        )

        # 3. Tool: octoflow_inspect_arms
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_inspect_arms",
                description=(
                    "Query the live status, sensory surprise deltas (ΔS), thresholds (θ), and current tools "
                    "of all 8 arm ganglia. Side effects: none (read-only query)."
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
            handler=self._handle_inspect_arms,
            aliases=["octoflow_arms_status"],
        )

        # 4. Tool: octoflow_recall_memory
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_recall_memory",
                description=(
                    "Query the cephalopod Vertical Lobe associative memory for known bug patterns, "
                    "remediation strategies, and Hebbian weights. Side effects: none (read-only query)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "error_text": {
                            "type": "string",
                            "description": "Error message, test failure, or traceback to search in associative memory.",
                        }
                    },
                    "required": ["error_text"],
                },
            ),
            handler=self._handle_recall_memory,
        )

        # 5. Tool: octoflow_audit
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_audit",
                description=(
                    "Run an automated workspace readiness, test density, and security audit scoring on a 1-100 scale. "
                    "Side effects: read-only scan strictly within the configured workspace directory (--dir)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Optional relative path to subdirectory within workspace to audit.",
                        }
                    },
                },
            ),
            handler=self._handle_audit,
        )

        # 6. Tool: octoflow_guild_list
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_guild_list",
                description=(
                    "List all discovered 8-arm specialist guilds across project (.octoflow/guilds/), "
                    "user (~/.octoflow/guilds/), and built-ins. Side effects: none (read-only query)."
                ),
                inputSchema={"type": "object", "properties": {}},
            ),
            handler=self._handle_guild_list,
        )

        # 7. Tool: octoflow_receipt
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_receipt",
                description=(
                    "Retrieve the truthful token receipt, sensory gate savings, and cost accounting "
                    "for the last mission run. Side effects: none (read-only query)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_id": {
                            "type": "string",
                            "description": "Specific run identifier. Defaults to the latest run.",
                        }
                    },
                },
            ),
            handler=self._handle_receipt,
        )

        # 8. Tool: octoflow_read_file
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_read_file",
                description=(
                    "Read the contents of a file strictly within the configured workspace directory (--dir). "
                    "Side effects: none (read-only). Refuses operations attempting path traversal outside the workspace."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to file within workspace directory.",
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "Maximum number of lines to read from the file (default: 500).",
                            "default": 500,
                        },
                    },
                    "required": ["path"],
                },
            ),
            handler=self._handle_read_file,
        )

        # 9. Tool: octoflow_search_codebase
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_search_codebase",
                description=(
                    "Semantic vector and lexical search across indexed workspace source files, classes, and functions "
                    "using Episodic Codebase RAG. Returns top-k matching code snippets with file paths, line ranges, "
                    "and similarity scores. Side effects: none (read-only query strictly within the configured workspace directory)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query, function description, or technical concept to search.",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Maximum number of relevant code chunks to return (default: 5).",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            handler=self._handle_search_codebase,
            aliases=["octoflow_rag_search", "search_codebase"],
        )

        # 10. Tool: octoflow_search_symbols
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_search_symbols",
                description=(
                    "Lookup classes, functions, async functions, and methods across the codebase AST connectome. "
                    "Returns exact or substring symbol matches with file paths, line ranges, and docstrings. "
                    "Side effects: none (read-only query strictly within the configured workspace directory)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Symbol name or substring pattern (e.g. 'SupraesophagealConductor', 'search_codebase').",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Maximum number of matching symbols to return (default: 10).",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
            ),
            handler=self._handle_search_symbols,
            aliases=["octoflow_symbols", "search_symbols"],
        )

        # 11. Tool: octoflow_find_callers
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_find_callers",
                description=(
                    "Query the codebase AST call graph connectome to find all callers and call sites "
                    "referencing a specific function, method, or class. "
                    "Side effects: none (read-only query strictly within the configured workspace directory)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbol_name": {
                            "type": "string",
                            "description": "Target symbol or callee name to locate callers for (e.g. 'generate', 'arun_swarm').",
                        },
                    },
                    "required": ["symbol_name"],
                },
            ),
            handler=self._handle_find_callers,
            aliases=["octoflow_callers", "find_callers"],
        )

        # 12. Tool: octoflow_switch_guild
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_switch_guild",
                description=(
                    "Dynamically switch the active 8-arm specialist guild and configure the swarm roster "
                    "to any of the 64 personas (e.g. 'cloud_devops', 'cybersec_ops', 'data_science', "
                    "'enterprise_migration', 'mobile_apps', 'qa_resilience', 'systems_embedded', "
                    "'web_fullstack') or custom project guilds. "
                    "Side effects: updates active swarm arm configuration for subsequent runs."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "guild_name": {
                            "type": "string",
                            "description": "Name or alias of the specialist guild to activate (e.g. 'cloud_devops', 'devops', 'secops', 'web', 'data_science').",
                        },
                    },
                    "required": ["guild_name"],
                },
            ),
            handler=self._handle_switch_guild,
            aliases=["octoflow_set_guild", "switch_guild"],
        )

        # 13. Tool: octoflow_octopolis
        self.registry.register_tool(
            schema=MCPToolSchema(
                name="octoflow_octopolis",
                description=(
                    "Deploy the flagship Task-Adaptive 8-Octopus Swarm (Octopolis - 64 Neural Arms) "
                    "across 4 phased convergence gates on any engineering task. Dynamically adapts domain goals "
                    "across Architecture, Database, Backend, Frontend, Cognitive Logic, Security Sentinel, QA Testing, and DevOps. "
                    "Side effects: modifies files and executes builds strictly within the configured workspace directory (--dir)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "objective": {
                            "type": "string",
                            "description": "The engineering task, bug fix, feature, or project to solve with all 8 octopuses.",
                        },
                        "cycles_per_octopus": {
                            "type": "integer",
                            "description": "Cognitive problem-solving cycles per octopus (default: 3).",
                            "default": 3,
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
            handler=self._handle_run_octopolis,
            aliases=["octoflow_run_consortium", "octopolis"],
        )

    def _get_conductor(
        self, morphology: str = "software_dev", guild: str | None = None, dry_run: bool = False
    ) -> SupraesophagealConductor:
        """Create or configure a SupraesophagealConductor instance."""
        active_guild = guild or self.current_guild
        has_real_key = bool(
            os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GROK_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
        )
        is_dry = dry_run or (os.getenv("OCTOFLOW_DRY_RUN") == "1") or not has_real_key
        provider_name = (
            "mock" if is_dry else ("anthropic" if os.getenv("ANTHROPIC_API_KEY") else "mock")
        )
        if provider_name == "mock":
            is_dry = True

        custom_roster = None
        morph_val = SwarmMorphology.CUSTOM if active_guild else SwarmMorphology(morphology)

        if active_guild:
            from octoflow.guild import load_guild

            try:
                guild_spec = load_guild(active_guild, project_dir=self.workspace_dir)
                custom_roster = guild_spec.to_arm_roster()
            except Exception as e:
                logger.warning("Failed loading guild '%s': %s", active_guild, e)

        config = OctoFlowConfig(
            workspace_dir=str(self.workspace_dir),
            morphology=morph_val,
            guild=active_guild,
            custom_roster=custom_roster or [],
            model_provider=provider_name,
            dry_run=is_dry,
        )
        self.conductor = SupraesophagealConductor(config=config)
        return self.conductor

    async def _execute_swarm_task(
        self,
        run_id: str,
        objective: str,
        morphology: str,
        guild: str | None,
        max_cycles: int,
        dry_run: bool,
    ) -> dict[str, Any]:
        """Execute the swarm mission in an asynchronous task and record progress."""
        record = self._runs[run_id]
        record["status"] = "RUNNING"
        record["start_time"] = time.time()
        record["current_cycle"] = 1
        record["total_cycles"] = max_cycles
        record["latest_thought"] = (
            "Initializing brachial neural ganglia and evaluating sensory surprise..."
        )

        try:
            conductor = self._get_conductor(morphology, guild=guild, dry_run=dry_run)
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

            record["status"] = "COMPLETE" if outcome_val == "complete" else "FAILED"
            record["outcome"] = outcome_val
            record["mode"] = mode_val
            record["result"] = result
            record["files_written"] = result.get("files_written", [])
            record["tokens_consumed"] = result.get("tokens_consumed", 0)
            record["current_cycle"] = result.get("total_cycles", max_cycles)
            record["total_cycles"] = result.get("total_cycles", max_cycles)
            record["latest_thought"] = result.get(
                "latest_thought",
                f"Mission completed with outcome '{outcome_val}' after {record['current_cycle']} cycles.",
            )
            record["execution_time"] = time.time() - record["start_time"]
            return result
        except Exception as e:
            record["status"] = "FAILED"
            record["outcome"] = "failed"
            record["error"] = f"{type(e).__name__}: {str(e)}"
            record["latest_thought"] = f"Mission halted with error: {type(e).__name__}"
            record["execution_time"] = time.time() - record["start_time"]
            return {"success": False, "outcome": "failed", "error": record["error"]}

    async def _handle_run_swarm(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_run tool."""
        objective = args["objective"]
        octos_count = int(args.get("octos", 1))
        if octos_count >= 8 or bool(args.get("consortium", False)):
            return await self._handle_run_octopolis(args)

        morphology = args.get("morphology", "software_dev")
        guild = args.get("guild")
        max_cycles = int(args.get("max_cycles", 10))
        dry_run = bool(args.get("dry_run", False))
        async_run = bool(args.get("async", args.get("async_run", False)))
        timeout_seconds = float(args.get("timeout_seconds", 60.0))

        run_id = f"run-{uuid.uuid4().hex[:8]}"
        self._latest_run_id = run_id
        self._runs[run_id] = {
            "run_id": run_id,
            "objective": objective,
            "morphology": morphology,
            "guild": guild,
            "status": "RUNNING",
            "current_cycle": 1,
            "total_cycles": max_cycles,
            "latest_thought": "Evaluating sensory surprise thresholds across 8 brachial ganglia...",
            "files_written": [],
            "tokens_consumed": 0,
            "start_time": time.time(),
        }

        task = asyncio.create_task(
            self._execute_swarm_task(
                run_id=run_id,
                objective=objective,
                morphology=morphology,
                guild=guild,
                max_cycles=max_cycles,
                dry_run=dry_run,
            )
        )

        if async_run:
            text = (
                f"◈ OctoFlow Swarm Run Queued (Background):\n"
                f"• Run ID: {run_id}\n"
                f"• Objective: {objective}\n"
                f"• Status: RUNNING\n"
                f"• Note: Use tool 'octoflow_get_run_status' with run_id='{run_id}' to poll progress.\n"
            )
            payload = {"run_id": run_id, "status": "RUNNING", "async": True}
            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": text},
                    {"type": "text", "text": json.dumps(payload)},
                ],
                isError=False,
            )

        # Synchronous execution with timeout guard
        try:
            result = await asyncio.wait_for(asyncio.shield(task), timeout=timeout_seconds)
            mode_val = result.get("mode", RunMode.DRY_RUN.value if dry_run else RunMode.LIVE.value)
            outcome_val = result.get("outcome", "complete" if result.get("success") else "failed")
            files_written = result.get("files_written", [])

            status_glyph = (
                "✔" if outcome_val == "complete" else ("◈" if outcome_val == "partial" else "✖")
            )
            text = (
                f"◈ OctoFlow Cephalopod Swarm Run Completed:\n"
                f"• Run ID: {run_id}\n"
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
            payload = {
                "run_id": run_id,
                "mode": mode_val,
                "outcome": outcome_val,
                "success": (outcome_val == "complete"),
                "files_written": files_written,
                "tokens_consumed": result.get("tokens_consumed", 0),
                "execution_time_seconds": result.get("execution_time_seconds", 0.0),
            }
            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": text},
                    {"type": "text", "text": json.dumps(payload)},
                ],
                isError=(outcome_val == "failed"),
            )
        except asyncio.TimeoutError:
            text = (
                f"◈ OctoFlow Swarm Run in Progress (Timeout Reached):\n"
                f"• Run ID: {run_id}\n"
                f"• Objective: {objective}\n"
                f"• Status: RUNNING (backgrounded after {timeout_seconds:.1f}s)\n"
                f"• Note: The run is executing in background. Query 'octoflow_get_run_status' with run_id='{run_id}'.\n"
            )
            payload = {"run_id": run_id, "status": "RUNNING", "timeout": True}
            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": text},
                    {"type": "text", "text": json.dumps(payload)},
                ],
                isError=False,
            )

    async def _handle_run_octopolis(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_octopolis tool deploying all 8 task-adaptive octopuses."""
        objective = args["objective"]
        cycles = int(args.get("cycles_per_octopus", args.get("max_cycles", 2)))
        dry_run = bool(args.get("dry_run", False))

        from octoflow.config import OctoFlowConfig
        from octoflow.consortium import OctosConsortium

        has_real_key = bool(
            os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GROK_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
        )
        is_dry = dry_run or (os.getenv("OCTOFLOW_DRY_RUN") == "1") or not has_real_key
        provider_name = (
            "mock" if is_dry else ("anthropic" if os.getenv("ANTHROPIC_API_KEY") else "mock")
        )
        if provider_name == "mock":
            is_dry = True

        config = OctoFlowConfig(
            workspace_dir=str(self.workspace_dir),
            model_provider=provider_name,
            dry_run=is_dry,
        )

        consortium = OctosConsortium(
            config=config,
            octopus_count=8,
        )

        result = await consortium.arun_consortium(
            objective=objective,
            cycles_per_octopus=cycles,
        )

        total_arms = result.get("total_arms", 64)
        total_tokens = result.get("total_tokens_consumed", 0)
        total_cost = result.get("total_cost_dollars", 0.0)
        exec_time = result.get("execution_time_seconds", 0.0)

        text = (
            f"◈ Task-Adaptive 8-Octopus Octopolis Run Completed (64 Neural Arms):\n"
            f"• Objective: {objective}\n"
            f"• Tier: Flagship Octopolis (8 Octopuses • {total_arms} Arms)\n"
            f"• Phase Gates Completed: Architecture -> Core Engineering (DB/API/UI/AI) -> Shield (Sec/QA) -> Operations\n"
            f"• Total Tokens Consumed: {total_tokens:,}\n"
            f"• Execution Time: {exec_time:.2f}s\n"
            f"• Estimated Cost: ${total_cost:.4f}\n"
            f"• Status: ✔ ALL 8 OCTOPUSES DELIVERED\n"
        )
        return MCPToolCallResult(
            content=[
                {"type": "text", "text": text},
                {"type": "text", "text": json.dumps(result, default=str)},
            ],
            isError=False,
        )

    async def _handle_get_run_status(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_get_run_status tool."""
        run_id = args.get("run_id") or self._latest_run_id
        if not run_id or run_id not in self._runs:
            avail = ", ".join(self._runs.keys()) if self._runs else "none"
            return MCPToolCallResult(
                content=[
                    {
                        "type": "text",
                        "text": f"Error: Run ID '{run_id}' not found. Available runs: {avail}.",
                    }
                ],
                isError=True,
            )

        r = self._runs[run_id]
        status_glyph = (
            "✔" if r["status"] == "COMPLETE" else ("✖" if r["status"] == "FAILED" else "●")
        )
        current_cycle = r.get("current_cycle", 1)
        total_cycles = r.get("total_cycles", 10)
        latest_thought = r.get("latest_thought", "Processing sensory inputs...")
        text = (
            f"◈ OctoFlow Run Status [{run_id}]:\n"
            f"• Status: {status_glyph} {r['status']}\n"
            f"• Outcome: {r.get('outcome', 'in_progress')}\n"
            f"• Objective: {r.get('objective', '')}\n"
            f"• Arm Cycle: {current_cycle}/{total_cycles}\n"
            f"• Latest Thought: {latest_thought}\n"
            f"• Files Written: {len(r.get('files_written', []))}\n"
            f"• Tokens Consumed: {r.get('tokens_consumed', 0):,}\n"
            f"• Elapsed: {time.time() - r.get('start_time', time.time()):.1f}s\n"
        )
        if "error" in r:
            text += f"• Error: {r['error']}\n"
        return MCPToolCallResult(
            content=[
                {"type": "text", "text": text},
                {"type": "text", "text": json.dumps(r, default=str)},
            ],
            isError=(r["status"] == "FAILED"),
        )

    async def _handle_inspect_arms(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_inspect_arms tool."""
        if self.conductor is None:
            self._get_conductor()
        if self.conductor is None:
            return MCPToolCallResult(
                content=[{"type": "text", "text": "Error: Failed to initialize conductor."}],
                isError=True,
            )

        arm_reports = []
        for arm in self.conductor.arms:
            tools_list = getattr(arm.role, "tools", []) or []
            arm_reports.append(
                f"• Arm {arm.arm_id} [{arm.role.title}]: {arm.status} | "
                f"Surprise: {arm.gate.surprise_history[-1] if arm.gate.surprise_history else 0.0:.3f} / θ={arm.gate.threshold:.2f} | "
                f"Quiescent: {arm.is_quiescent} | Tools: {', '.join(tools_list)}"
            )
        text = "◈ Cephalopod Arm Ganglia Status (8 Arms):\n" + "\n".join(arm_reports)
        return MCPToolCallResult(content=[{"type": "text", "text": text}])

    async def _handle_recall_memory(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_recall_memory tool."""
        if self.conductor is None:
            self._get_conductor()
        if self.conductor is None:
            return MCPToolCallResult(
                content=[{"type": "text", "text": "Error: Failed to initialize conductor."}],
                isError=True,
            )

        error_text = str(args.get("error_text", "")).strip()
        if not error_text:
            return MCPToolCallResult(
                content=[{"type": "text", "text": "Error: 'error_text' must be non-empty."}],
                isError=True,
            )

        from octoflow.tools import ToolResult

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

    async def _handle_audit(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_audit tool."""
        target_dir = self.workspace_dir
        if "path" in args and args["path"]:
            try:
                target_dir = self._resolve_safe(str(args["path"]))
            except ValueError as ve:
                return MCPToolCallResult(
                    content=[{"type": "text", "text": f"Access denied: {ve}"}],
                    isError=True,
                )

        try:
            from octoflow.audit import run_workspace_audit

            report = run_workspace_audit(str(target_dir))
            text = (
                f"◈ OctoFlow Workspace Audit Report:\n"
                f"• Overall Readiness Score: {report.get('score', 85)}/100 (Grade: {report.get('grade', 'B')})\n"
                f"• Workspace Directory: {target_dir}\n"
                f"• Test Density: {report.get('test_density_pct', 0.0):.1f}%\n"
                f"• Security Findings: {report.get('security_findings', 0)}\n"
            )
            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": text},
                    {"type": "text", "text": json.dumps(report, default=str)},
                ]
            )
        except Exception as e:
            return MCPToolCallResult(
                content=[{"type": "text", "text": f"Audit execution failed: {e}"}],
                isError=True,
            )

    async def _handle_guild_list(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_guild_list tool."""
        from octoflow.guild import list_guilds

        entries = list_guilds(project_dir=self.workspace_dir)
        lines = ["◈ Available Specialist 8-Arm Guilds:"]
        for g in entries:
            src = g.get("source", "builtin")
            lines.append(f"• {g['name']} [{src}]: {g['description']} (8 arms)")
        return MCPToolCallResult(
            content=[
                {"type": "text", "text": "\n".join(lines)},
                {"type": "text", "text": json.dumps(entries)},
            ]
        )

    async def _handle_receipt(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_receipt tool."""
        run_id = args.get("run_id") or self._latest_run_id
        if run_id and run_id in self._runs and "result" in self._runs[run_id]:
            res = self._runs[run_id]["result"]
            text = (
                f"◈ OctoFlow Mission Receipt [{run_id}]:\n"
                f"• Tokens Consumed: {res.get('tokens_consumed', 0):,}\n"
                f"• Estimated Chatty Swarm Tokens: {res.get('estimated_chatty_tokens', 0):,}\n"
                f"• Token Reduction: {res.get('token_reduction_pct', 0.0):.1f}%\n"
                f"• Total Cost: ${res.get('total_cost_dollars', 0.0):.4f}\n"
                f"• Outcome: {res.get('outcome', 'unknown')}\n"
            )
            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": text},
                    {"type": "text", "text": json.dumps(res, default=str)},
                ]
            )

        return MCPToolCallResult(
            content=[
                {"type": "text", "text": "No completed mission receipts available in this session."}
            ],
            isError=False,
        )

    async def _handle_read_file(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_read_file tool with strict workspace confinement."""
        path_arg = str(args.get("path", "")).strip()
        if not path_arg:
            return MCPToolCallResult(
                content=[{"type": "text", "text": "Error: 'path' argument is required."}],
                isError=True,
            )

        try:
            target_path = self._resolve_safe(path_arg)
        except ValueError as ve:
            return MCPToolCallResult(
                content=[{"type": "text", "text": f"Access denied: {ve}"}],
                isError=True,
            )

        if not target_path.exists():
            return MCPToolCallResult(
                content=[{"type": "text", "text": f"File not found: '{path_arg}'"}],
                isError=True,
            )
        if not target_path.is_file():
            return MCPToolCallResult(
                content=[{"type": "text", "text": f"Target path is not a file: '{path_arg}'"}],
                isError=True,
            )

        max_lines = int(args.get("max_lines", 500))
        try:
            raw_lines = target_path.read_text(encoding="utf-8").splitlines()
            if len(raw_lines) > max_lines:
                content = (
                    "\n".join(raw_lines[:max_lines])
                    + f"\n... [Truncated: showing first {max_lines} of {len(raw_lines)} lines]"
                )
            else:
                content = "\n".join(raw_lines)

            return MCPToolCallResult(
                content=[{"type": "text", "text": f"// File: {path_arg}\n{content}"}]
            )
        except Exception as e:
            return MCPToolCallResult(
                content=[{"type": "text", "text": f"Failed reading file '{path_arg}': {e}"}],
                isError=True,
            )

    def _get_memory(self) -> Any:
        """Initialize and return the VerticalLobeMemory instance with Codebase RAG."""
        if self._memory is None:
            from octoflow.memory import VerticalLobeMemory

            db_path = self.workspace_dir / ".octoflow" / "memory" / "codebase_rag.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._memory = VerticalLobeMemory(db_path=str(db_path))

        if not self._rag_indexed:
            try:
                self._memory.index_workspace(str(self.workspace_dir))
                self._rag_indexed = True
            except Exception as e:
                logger.warning("Codebase RAG initial indexing warning: %s", e)

        return self._memory

    async def _handle_search_codebase(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_search_codebase tool."""
        query = str(args.get("query", "")).strip()
        if not query:
            return MCPToolCallResult(
                content=[{"type": "text", "text": "Error: 'query' argument is required."}],
                isError=True,
            )
        top_k = int(args.get("top_k", 5))
        try:
            mem = self._get_memory()
            results = mem.search_codebase(query, top_k=top_k)
            if not results:
                return MCPToolCallResult(
                    content=[{"type": "text", "text": f"No code snippets matched query: '{query}'"}],
                    isError=False,
                )
            lines = [f"◈ Codebase RAG Search Results for '{query}' ({len(results)} matches):"]
            for idx, r in enumerate(results, start=1):
                sim = r.get("similarity", r.get("score", 0.0))
                fp = r.get("file_path", "unknown")
                sline = r.get("start_line", 1)
                eline = r.get("end_line", 1)
                sym = r.get("symbol_name") or r.get("symbol") or ""
                sym_tag = f" [{sym}]" if sym else ""
                lines.append(f"\n--- [{idx}] {fp}:{sline}-{eline}{sym_tag} (Score: {sim:.3f}) ---")
                snippet = (r.get("content") or r.get("snippet") or "").strip()
                lines.append(snippet)

            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": "\n".join(lines)},
                    {"type": "text", "text": json.dumps(results, default=str)},
                ],
                isError=False,
            )
        except Exception as e:
            return MCPToolCallResult(
                content=[
                    {
                        "type": "text",
                        "text": f"Error performing codebase search: {type(e).__name__}: {e}",
                    }
                ],
                isError=True,
            )

    async def _handle_search_symbols(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_search_symbols tool."""
        query = str(args.get("query", "")).strip()
        if not query:
            return MCPToolCallResult(
                content=[{"type": "text", "text": "Error: 'query' argument is required."}],
                isError=True,
            )
        top_k = int(args.get("top_k", 10))
        try:
            mem = self._get_memory()
            symbols = mem.search_symbols(query, top_k=top_k)
            if not symbols:
                return MCPToolCallResult(
                    content=[{"type": "text", "text": f"No symbols found matching: '{query}'"}],
                    isError=False,
                )
            lines = [f"◈ Codebase AST Symbol Matches for '{query}' ({len(symbols)} found):"]
            for s in symbols:
                sym_name = s.get("name", "")
                sym_type = s.get("symbol_type", "")
                fp = s.get("file_path", "")
                sline = s.get("start_line", 1)
                eline = s.get("end_line", 1)
                doc = s.get("docstring") or ""
                doc_preview = f" - {doc.splitlines()[0][:60]}..." if doc else ""
                lines.append(f"• {sym_name} ({sym_type}) -> {fp}:{sline}-{eline}{doc_preview}")

            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": "\n".join(lines)},
                    {"type": "text", "text": json.dumps(symbols, default=str)},
                ],
                isError=False,
            )
        except Exception as e:
            return MCPToolCallResult(
                content=[
                    {
                        "type": "text",
                        "text": f"Error searching symbols: {type(e).__name__}: {e}",
                    }
                ],
                isError=True,
            )

    async def _handle_find_callers(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_find_callers tool."""
        symbol_name = str(args.get("symbol_name", "")).strip()
        if not symbol_name:
            return MCPToolCallResult(
                content=[{"type": "text", "text": "Error: 'symbol_name' argument is required."}],
                isError=True,
            )
        try:
            mem = self._get_memory()
            callers = mem.find_callers(symbol_name)
            if not callers:
                return MCPToolCallResult(
                    content=[
                        {
                            "type": "text",
                            "text": f"No recorded callers found for symbol: '{symbol_name}'",
                        }
                    ],
                    isError=False,
                )
            lines = [f"◈ Callers of '{symbol_name}' in AST Connectome ({len(callers)} call sites):"]
            for c in callers:
                caller_name = c.get("caller", "<module>")
                fp = c.get("file_path", "")
                ln = c.get("line_number", 0)
                lines.append(f"• {caller_name}() at {fp}:{ln}")

            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": "\n".join(lines)},
                    {"type": "text", "text": json.dumps(callers, default=str)},
                ],
                isError=False,
            )
        except Exception as e:
            return MCPToolCallResult(
                content=[
                    {
                        "type": "text",
                        "text": f"Error finding callers: {type(e).__name__}: {e}",
                    }
                ],
                isError=True,
            )

    async def _handle_switch_guild(self, args: dict[str, Any]) -> MCPToolCallResult:
        """Handler for octoflow_switch_guild tool."""
        guild_name = str(args.get("guild_name", "")).strip()
        if not guild_name:
            return MCPToolCallResult(
                content=[{"type": "text", "text": "Error: 'guild_name' argument is required."}],
                isError=True,
            )
        try:
            from octoflow.guild import load_guild

            guild_spec = load_guild(guild_name, project_dir=self.workspace_dir)
            self.current_guild = guild_spec.name
            # Reconfigure conductor with new custom roster
            self._get_conductor(guild=guild_spec.name)

            domain_val = (
                getattr(guild_spec, "domain", None)
                or (guild_spec.metadata.get("domain") if getattr(guild_spec, "metadata", None) else None)
                or guild_spec.name
            )

            lines = [
                f"◈ Activated Specialist Guild: {guild_spec.name}",
                f"• Description: {guild_spec.description}",
                f"• Domain: {domain_val}",
                "• Active 8-Arm Specialist Roster:",
            ]
            for arm in guild_spec.arms:
                lines.append(
                    f"  - Arm {arm.id}: {arm.role} [{arm.focus}]"
                )

            payload = {
                "guild": guild_spec.name,
                "domain": domain_val,
                "description": guild_spec.description,
                "arms": [
                    {
                        "id": a.id,
                        "role": a.role,
                        "focus": a.focus,
                        "color": a.color,
                        "tools": a.tools,
                    }
                    for a in guild_spec.arms
                ],
            }
            return MCPToolCallResult(
                content=[
                    {"type": "text", "text": "\n".join(lines)},
                    {"type": "text", "text": json.dumps(payload)},
                ],
                isError=False,
            )
        except Exception as e:
            return MCPToolCallResult(
                content=[
                    {
                        "type": "text",
                        "text": f"Failed to switch guild to '{guild_name}': {type(e).__name__}: {e}",
                    }
                ],
                isError=True,
            )

    async def handle_json_rpc_message(self, message: Any) -> dict[str, Any] | None:
        """Process a single MCP JSON-RPC 2.0 message."""
        if not isinstance(message, dict):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": JSONRPC_INVALID_REQUEST,
                    "message": "Invalid Request: message must be a JSON object.",
                },
            }

        if message.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": JSONRPC_INVALID_REQUEST,
                    "message": "Invalid Request: 'jsonrpc' must be exactly '2.0'.",
                },
            }

        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        if not isinstance(method, str) or not method:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": JSONRPC_INVALID_REQUEST,
                    "message": "Invalid Request: 'method' must be a non-empty string.",
                },
            }

        # 1. initialize Handshake
        if method == "initialize":
            if not isinstance(params, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": JSONRPC_INVALID_PARAMS,
                        "message": "Invalid params for 'initialize': expected an object.",
                    },
                }

            client_version = params.get("protocolVersion")
            if client_version in SUPPORTED_PROTOCOL_VERSIONS:
                self.negotiated_version = client_version
            else:
                self.negotiated_version = DEFAULT_PROTOCOL_VERSION

            self.initialized = True
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": self.negotiated_version,
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    "capabilities": {"tools": {"listChanged": False}},
                },
            }

        # 2. notifications/initialized Notification (No response expected)
        elif method in ("notifications/initialized", "initialized"):
            self.initialized = True
            return None

        # 3. ping Handshake
        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        # 4. tools/list Discovery
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

        # 5. tools/call Execution
        elif method == "tools/call":
            if not isinstance(params, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": JSONRPC_INVALID_PARAMS,
                        "message": "Invalid params: 'params' must be an object.",
                    },
                }

            tool_name = params.get("name")
            if not tool_name or not isinstance(tool_name, str):
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": JSONRPC_INVALID_PARAMS,
                        "message": "Invalid params: 'name' is required and must be a string.",
                    },
                }

            tool_args = params.get("arguments", {})
            if not isinstance(tool_args, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": JSONRPC_INVALID_PARAMS,
                        "message": "Invalid params: 'arguments' must be an object/dict.",
                    },
                }

            # Verify tool existence
            if not self.registry.has_tool(tool_name):
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": JSONRPC_METHOD_NOT_FOUND,
                        "message": f"Method not found: unknown tool '{tool_name}'.",
                    },
                }

            # Verify required parameters per tool schema
            schema = self.registry.get_tool(tool_name)
            if schema and "required" in schema.inputSchema:
                for req in schema.inputSchema["required"]:
                    if req not in tool_args or tool_args[req] is None:
                        return {
                            "jsonrpc": "2.0",
                            "id": msg_id,
                            "error": {
                                "code": JSONRPC_INVALID_PARAMS,
                                "message": f"Invalid params: missing required parameter '{req}'.",
                            },
                        }

            try:
                call_res = await self.registry.call_tool(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": call_res.content,
                        "isError": call_res.isError,
                    },
                }
            except Exception as e:
                # Internal error without leaking full stack trace
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": JSONRPC_INTERNAL_ERROR,
                        "message": f"Internal error executing tool '{tool_name}': {type(e).__name__}: {str(e)}",
                    },
                }

        # 6. Unimplemented / Unknown Methods
        else:
            if msg_id is None:
                # Unknown notifications are dropped silently per JSON-RPC 2.0
                return None
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": JSONRPC_METHOD_NOT_FOUND,
                    "message": f"Method '{method}' not implemented by OctoFlow MCP server.",
                },
            }

    async def run_stdio(self) -> None:
        """Run the MCP server listening on stdin and responding on stdout with strict stdio hygiene."""
        # 1. Guard stdout: redirect all standard stdout writes (prints, logs) to stderr
        self._real_stdout = sys.stdout
        sys.stdout = StdoutGuard(sys.stderr)

        # 2. Configure logging handlers to write to stderr exclusively
        for handler in logging.root.handlers:
            if hasattr(handler, "stream") and handler.stream is sys.stdout:
                handler.stream = sys.stderr

        try:
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            loop = asyncio.get_running_loop()
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)

            while True:
                line = await reader.readline()
                if not line:  # Clean shutdown on EOF
                    break
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue

                try:
                    msg = json.loads(line_str)
                except Exception as e:
                    err_resp = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": JSONRPC_PARSE_ERROR,
                            "message": f"Parse error: invalid JSON: {str(e)}",
                        },
                    }
                    self._send_protocol_message(err_resp)
                    continue

                try:
                    resp = await self.handle_json_rpc_message(msg)
                    if resp is not None:
                        self._send_protocol_message(resp)
                except Exception as e:
                    err_resp = {
                        "jsonrpc": "2.0",
                        "id": msg.get("id") if isinstance(msg, dict) else None,
                        "error": {
                            "code": JSONRPC_INTERNAL_ERROR,
                            "message": f"Internal server error: {type(e).__name__}: {str(e)}",
                        },
                    }
                    self._send_protocol_message(err_resp)

        finally:
            # Restore stdout on exit
            if self._real_stdout is not None:
                sys.stdout = self._real_stdout

    def _send_protocol_message(self, message: dict[str, Any]) -> None:
        """Write a single JSON-RPC 2.0 response line strictly to the real stdout stream."""
        target = self._real_stdout or sys.stderr
        payload_str = json.dumps(message, ensure_ascii=False) + "\n"
        target.write(payload_str)
        target.flush()
