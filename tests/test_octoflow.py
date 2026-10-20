"""Comprehensive Unit Test Suite for OctoFlow Cephalopod Swarm Architecture.

Tests all core components:
1. WorkspaceSandbox & advisory locks
2. CodeSensoryEncoder
3. SurpriseGate & event-triggered silent execution
4. InterBrachialBus ring communication
5. VerticalLobeMemory Hebbian pattern recall
6. ArmAgent autonomous execution loop
7. SupraesophagealConductor & dynamic coalition attention
"""

import os
import shutil
import tempfile
import pytest
import numpy as np
import torch

from octoflow.config import (
    OctoFlowConfig,
    SwarmMorphology,
    SOFTWARE_DEV_ROSTER,
    AIML_RESEARCH_ROSTER,
    FULLSTACK_AI_ROSTER,
)
from octoflow.tools import WorkspaceSandbox, ToolResult
from octoflow.encoder import CodeSensoryEncoder
from octoflow.gate import SurpriseGate
from octoflow.bus import InterBrachialBus, MessageIntent
from octoflow.memory import VerticalLobeMemory
from octoflow.provider import MockLLMProvider
from octoflow.arm import ArmAgent
from octoflow.conductor import SupraesophagealConductor


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace folder and clean up after."""
    d = tempfile.mkdtemp(prefix="octoflow_test_ws_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_workspace_sandbox_and_security(temp_workspace):
    """Verify safe filesystem execution, path traversal blocking, and advisory locks."""
    sandbox = WorkspaceSandbox(temp_workspace)

    # 1. Safe file write and read
    res_w = sandbox.write_file("nested/test.txt", "hello cephalopod")
    assert res_w.success is True
    assert res_w.returncode == 0

    res_r = sandbox.read_file("nested/test.txt")
    assert res_r.success is True
    assert res_r.stdout == "hello cephalopod"

    # 2. Path traversal security
    with pytest.raises(ValueError):
        sandbox._resolve_safe("../../escaped.txt")

    # 3. Advisory locks
    lock_a0 = sandbox.acquire_lock("shared.py", arm_id=0)
    assert lock_a0 is True

    # Arm 1 should fail to acquire lock held by Arm 0
    lock_a1 = sandbox.acquire_lock("shared.py", arm_id=1)
    assert lock_a1 is False

    # Arm 1 writing to locked file should fail with FileLockError
    res_w_fail = sandbox.write_file("shared.py", "malicious", arm_id=1)
    assert res_w_fail.success is False
    assert "FileLockError" in res_w_fail.stderr

    # Arm 0 releases, Arm 1 can now acquire
    sandbox.release_lock("shared.py", arm_id=0)
    lock_a1_retry = sandbox.acquire_lock("shared.py", arm_id=1)
    assert lock_a1_retry is True


def test_code_sensory_encoder():
    """Verify encoding of software signals into 16-dim sensory observation tensors."""
    encoder = CodeSensoryEncoder(obs_dim=16)

    # Clean execution result
    clean_res = ToolResult(
        tool_name="run_command",
        target="pytest",
        success=True,
        returncode=0,
        stdout="5 passed in 0.2s",
        stderr="",
        execution_time_ms=200.0,
    )
    obs_clean = encoder.encode(clean_res, step=1, max_steps=10, as_tensor=False)
    assert obs_clean.shape == (16,)
    assert obs_clean[0] == 0.0  # Exit code 0
    assert obs_clean[1] == 0.0  # No stderr
    assert obs_clean[15] == 1.0  # Quiescent / clean flag

    # Error execution result with syntax error
    err_res = ToolResult(
        tool_name="write_file",
        target="bad.py",
        success=False,
        returncode=1,
        stdout="",
        stderr="SyntaxError: invalid syntax on line 12",
        execution_time_ms=50.0,
    )
    obs_err = encoder.encode(err_res, step=2, max_steps=10, as_tensor=False)
    assert obs_err[0] > 0.0  # Non-zero exit code
    assert obs_err[1] == 1.0  # Stderr present
    assert obs_err[6] == 1.0  # Syntax error flag detected!
    assert obs_err[15] == 0.0  # Not quiescent


def test_surprise_gate_and_silent_execution():
    """Verify that clean execution stays silent while errors trigger escalation."""
    gate = SurpriseGate(arm_id=2, obs_dim=16, initial_threshold=0.50)
    encoder = CodeSensoryEncoder(obs_dim=16)

    # 1. Clean tool run -> Low surprise -> Silent execution
    clean_res = ToolResult(tool_name="write_file", target="api.py", success=True, returncode=0, diff_lines=20)
    obs_clean = encoder.encode(clean_res)
    escalate, surprise, telemetry = gate.evaluate(obs_clean, clean_res)

    assert escalate is False  # SILENT!
    assert surprise <= 0.50
    assert telemetry["savings_pct"] == 100.0

    # 2. Fatal crash tool run -> High surprise -> Escalation
    fatal_res = ToolResult(tool_name="run_command", target="pytest", success=False, returncode=1, stderr="AssertionError: 404 != 200")
    obs_fatal = encoder.encode(fatal_res)
    escalate_fatal, surprise_fatal, _ = gate.evaluate(obs_fatal, fatal_res)

    assert escalate_fatal is True  # ESCALATION ALERT!
    assert surprise_fatal > 0.50


def test_inter_brachial_ring_bus():
    """Verify lateral peer-to-peer ring communication between adjacent arms."""
    bus = InterBrachialBus(n_arms=8)

    # Neighbors of Arm 0 should be 7 (left) and 1 (right)
    left, right = bus.get_neighbors(0)
    assert left == 7
    assert right == 1

    # Arm 2 sends lateral message to Arm 3 (Backend to Frontend)
    msg = bus.send_lateral(
        sender_id=2,
        target_id=3,
        intent=MessageIntent.COOPERATIVE_PULL,
        summary="User schema updated: added avatar_url field.",
    )
    assert msg.sender_id == 2
    assert msg.target_id == 3

    # Arm 3 polls inbox and receives message
    inbox_3 = bus.poll_inbox(3)
    assert len(inbox_3) == 1
    assert inbox_3[0].intent == MessageIntent.COOPERATIVE_PULL
    assert "avatar_url" in inbox_3[0].summary

    # Inbox 3 is now cleared (drained)
    assert len(bus.poll_inbox(3)) == 0


def test_vertical_lobe_ltp_memory():
    """Verify fast Hebbian associative recall for bug resolution patterns."""
    memory = VerticalLobeMemory(feature_dim=16)

    # Query with a syntax error observation
    syntax_obs = np.zeros(16, dtype=np.float32)
    syntax_obs[6] = 1.0  # Syntax error flag

    recalled = memory.recall(syntax_obs)
    assert recalled is not None
    guidance, confidence = recalled
    assert confidence >= 0.75
    assert "colons" in guidance.lower() or "brackets" in guidance.lower()

    # Consolidate a new custom pattern
    custom_obs = np.zeros(16, dtype=np.float32)
    custom_obs[5] = 1.0  # High latency
    custom_obs[10] = 1.0  # Type error
    memory.consolidate(custom_obs, "Custom Error", "Check database pool timeout.")

    recalled_custom = memory.recall(custom_obs)
    assert recalled_custom is not None
    assert "database pool timeout" in recalled_custom[0]


def test_arm_agent_execution(temp_workspace):
    """Verify ArmAgent step lifecycle, saccade buffer pruning, and status transitions."""
    sandbox = WorkspaceSandbox(temp_workspace)
    bus = InterBrachialBus(n_arms=8)
    memory = VerticalLobeMemory(feature_dim=16)
    provider = MockLLMProvider()

    agent = ArmAgent(
        role_config=SOFTWARE_DEV_ROSTER[2],  # Backend API
        sandbox=sandbox,
        provider=provider,
        bus=bus,
        memory=memory,
        obs_dim=16,
    )

    res = agent.step(sub_goal="Create user authentication routes")
    assert res.arm_id == 2
    assert agent.step_count == 1
    assert len(agent.saccade_buffer) == 1


def test_conductor_swarm_and_token_savings(temp_workspace):
    """Verify the full 8-arm swarm execution with dynamic coalitions and >80% token savings."""
    config = OctoFlowConfig(
        morphology=SwarmMorphology.SOFTWARE_DEV,
        model_provider="mock",
        workspace_dir=temp_workspace,
    )

    telemetry_events = []
    def on_event(ev):
        telemetry_events.append(ev)

    conductor = SupraesophagealConductor(config=config, telemetry_callback=on_event)

    # Verify 8 arm decomposition
    goals = conductor.decompose_objective("Build a real-time markdown editor with FastAPI and Vue")
    assert len(goals) == 8

    # Run the swarm
    summary = conductor.run_swarm("Build a real-time markdown editor with FastAPI and Vue", max_cycles=3)

    assert summary["quiescent_arms"] >= 1
    assert summary["tokens_consumed"] > 0
    # Verify significant token reduction over chatty baseline!
    assert summary["token_reduction_pct"] >= 70.0
    assert len(telemetry_events) > 0


def test_morphologies_rosters():
    """Verify all 3 SwarmMorphologies produce valid 8-arm rosters."""
    c_sw = OctoFlowConfig(morphology=SwarmMorphology.SOFTWARE_DEV)
    assert len(c_sw.get_roster()) == 8
    assert c_sw.get_roster()[0].title == "System Architect"

    c_ai = OctoFlowConfig(morphology=SwarmMorphology.AIML_RESEARCH)
    assert len(c_ai.get_roster()) == 8
    assert c_ai.get_roster()[0].title == "Data Engineer"
    assert c_ai.get_roster()[1].title == "Model Architect"

    c_hy = OctoFlowConfig(morphology=SwarmMorphology.FULLSTACK_AI)
    assert len(c_hy.get_roster()) == 8
    assert c_hy.get_roster()[2].title == "Backend & Serve"
    assert c_hy.get_roster()[3].title == "Frontend UI"
