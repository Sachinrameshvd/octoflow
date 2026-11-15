"""Comprehensive verification tests for the Task-Adaptive 8-Octopus Swarm (Octopolis).

Verifies:
1. synthesize_adaptive_octopolis_goals: Dynamic goal synthesis across bugfix, feature,
   performance, and new-project tasks.
2. 4-Phase Convergence Gates: Architecture -> Core Engineering (DB/API/UI/AI) ->
   Shield (Security/QA) -> Operations (DevOps/Runner).
3. Synaptic Bus Broadcast: Inter-octopus events emitted across phase boundaries.
4. MCP Integration: octoflow_octopolis tool dispatches all 8 octopuses (64 arms).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from octoflow.config import OctoFlowConfig
from octoflow.consortium import (
    OctosConsortium,
    synthesize_adaptive_octopolis_goals,
)
from octoflow.mcp import OctoFlowMCPServer


def test_adaptive_goal_synthesis_bugfix() -> None:
    """Verify all 8 octopuses receive specialized bugfix mission briefs."""
    objective = "Fix memory leak and slow query in user session management"
    goals = synthesize_adaptive_octopolis_goals(objective, octopus_count=8)

    assert len(goals) == 8
    # Octo 0: System Architect
    assert "Root Cause" in goals[0] or "Architect" in goals[0]
    # Octo 1: Database
    assert "Database" in goals[1] or "Query" in goals[1]
    # Octo 2: Backend
    assert "Backend" in goals[2] or "Patch" in goals[2]
    # Octo 3: Frontend
    assert "Frontend" in goals[3] or "Client" in goals[3]
    # Octo 4: Cognitive
    assert "Edge-Case" in goals[4] or "Cognitive" in goals[4]
    # Octo 5: Security Sentinel
    assert "Security" in goals[5] or "Sentinel" in goals[5]
    # Octo 6: QA
    assert "Regression" in goals[6] or "QA" in goals[6]
    # Octo 7: DevOps
    assert "Runner" in goals[7] or "DevOps" in goals[7]


def test_adaptive_goal_synthesis_feature() -> None:
    """Verify all 8 octopuses receive specialized feature build mission briefs."""
    objective = "Implement Google OAuth2 authentication flow with JWT tokens"
    goals = synthesize_adaptive_octopolis_goals(objective, octopus_count=8)

    assert len(goals) == 8
    assert "Architect" in goals[0]
    assert "Database" in goals[1]
    assert "Backend" in goals[2]
    assert "Frontend" in goals[3]
    assert "Cognitive" in goals[4]
    assert "Security" in goals[5]
    assert "QA" in goals[6]
    assert "DevOps" in goals[7]


def test_adaptive_goal_synthesis_performance() -> None:
    """Verify all 8 octopuses receive specialized performance optimization mission briefs."""
    objective = "Optimize API response latency and benchmark search speed"
    goals = synthesize_adaptive_octopolis_goals(objective, octopus_count=8)

    assert len(goals) == 8
    assert "Architect" in goals[0]
    assert "Database" in goals[1]
    assert "Backend" in goals[2]
    assert "Frontend" in goals[3]
    assert "Benchmark" in goals[6] or "QA" in goals[6]


@pytest.mark.anyio
async def test_8_octopus_consortium_4_phase_execution(tmp_path: Path) -> None:
    """Verify full 8-octopus swarm executes across all 4 phased convergence gates."""
    cfg = OctoFlowConfig(model_provider="mock", workspace_dir=str(tmp_path))
    consortium = OctosConsortium(config=cfg, octopus_count=8)

    assert len(consortium.conductors) == 8
    total_arms = sum(len(c.arms) for c in consortium.conductors)
    assert total_arms == 64

    result = await consortium.arun_consortium(
        objective="Fix database query latency and add regression test",
        cycles_per_octopus=1,
    )

    assert result["status"] == "COMPLETED"
    assert result["tier"] == "octopolis"
    assert result["octopus_count"] == 8
    assert result["total_arms"] == 64

    # Verify all 4 phase gates executed
    phase_res = result["phase_results"]
    assert "genesis" in phase_res or "architecture" in phase_res
    assert "core_engineering" in phase_res
    assert "verification_and_shield" in phase_res
    assert "runner" in phase_res
    assert "construction" in phase_res  # backwards compat

    # Verify Synaptic Bus recorded inter-octopus events
    bus_events = consortium.synaptic_bus.events
    event_types = [e.event_type for e in bus_events]
    assert "SCAFFOLD_READY" in event_types or "ARCH_SPEC_READY" in event_types
    assert "MODULE_DELIVERED" in event_types
    assert "SECURITY_AUDIT_PASS" in event_types


@pytest.mark.anyio
async def test_mcp_octoflow_octopolis_tool(tmp_path: Path) -> None:
    """Verify octoflow_octopolis MCP tool executes the 8-octopus swarm via JSON-RPC."""
    server = OctoFlowMCPServer(workspace_dir=str(tmp_path))

    res = await server.registry.call_tool(
        "octoflow_octopolis",
        {
            "objective": "Patch memory leak and optimize connection pool",
            "cycles_per_octopus": 1,
            "dry_run": True,
        },
    )

    assert not res.isError
    assert len(res.content) == 2
    human_text = res.content[0]["text"]
    assert "Task-Adaptive 8-Octopus Octopolis Run Completed" in human_text
    assert "64 Neural Arms" in human_text
    assert "ALL 8 OCTOPUSES DELIVERED" in human_text

    raw_json = json.loads(res.content[1]["text"])
    assert raw_json["tier"] == "octopolis"
    assert raw_json["total_arms"] == 64

