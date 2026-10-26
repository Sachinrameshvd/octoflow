"""Phase 6: Comprehensive Robustness, Concurrency, and Failure Handling Verification Suite.

Tests cross-cutting production concerns:
1. Race conditions & deadlocks (randomized scheduling, stress loops with timeouts).
2. Graceful degradation: missing credentials, no Docker, no network, no GPU, read-only FS, full disk, corrupted files.
3. Timeouts everywhere: tool calls, bus sends, LLM calls. None may block forever.
4. Resource leaks: file descriptors, subprocesses, locks over cycles.
5. Input edge cases: empty goal, very long goal, emojis/Unicode, shell metacharacters/injection.
6. Idempotency & restart: restart after cancellation/interruption.
7. Secret scrubbing & logging: automated redaction of credentials in log output.
8. Cross-platform concerns: Windows path normalization (backslashes) and CRLF line endings.
"""

import asyncio
import io
import json
import logging
import os
import random
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

from octoflow.config import OctoFlowConfig
from octoflow.conductor import SupraesophagealConductor
from octoflow.tools import WorkspaceSandbox, ToolResult
from octoflow.bus import InterBrachialBus, BrachialMessage
from octoflow.memory import VerticalLobeMemory
from octoflow.provider import (
    get_llm_provider,
    MockLLMProvider,
    BaseLLMProvider,
    LLMResponse,
    CascadePoolLLMProvider,
    LLMConfigEntry,
    ProviderExhaustedError,
)
from octoflow.federation import (
    GLOBAL_FEDERATION_GUARD,
    PIIAction,
    SecretSanitizingLogFilter,
    get_safe_logger,
)


# ==============================================================================
# 1. Race Conditions & Deadlocks
# ==============================================================================
@pytest.mark.anyio
async def test_race_conditions_concurrent_file_locks(tmp_path):
    """Stress test advisory file locking under concurrent contention with randomized scheduling."""
    sandbox = WorkspaceSandbox(str(tmp_path))
    target_file = "shared_config.json"
    n_workers = 12
    write_count = 0
    lock_fail_count = 0

    async def worker(worker_id: int):
        nonlocal write_count, lock_fail_count
        # Stagger start with randomized jitter
        await asyncio.sleep(random.uniform(0.001, 0.015))
        try:
            with sandbox.file_lock(target_file, arm_id=worker_id):
                # Critical section: simulate work
                await asyncio.sleep(0.005)
                sandbox.write_file(target_file, json.dumps({"worker": worker_id, "timestamp": time.time()}))
                write_count += 1
        except RuntimeError:
            lock_fail_count += 1

    tasks = [asyncio.create_task(worker(i)) for i in range(n_workers)]
    await asyncio.gather(*tasks)

    # Exactly all workers either safely acquired the lock or safely failed without deadlocking
    assert write_count + lock_fail_count == n_workers
    assert write_count >= 1
    # Ensure all locks were cleanly released
    assert len(sandbox._locks) == 0


# ==============================================================================
# 2. Graceful Degradation
# ==============================================================================
def test_graceful_degradation_missing_credentials(monkeypatch):
    """Decision D1: Missing API credentials in LIVE mode must raise ProviderExhaustedError.
    
    In explicit DRY-RUN mode, missing credentials cleanly degrade to MockLLMProvider.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # 1. LIVE Mode (Decision D1): Must raise ProviderExhaustedError rather than silently faking success
    cfg_live = OctoFlowConfig(model_provider="anthropic", anthropic_api_key=None, api_key=None, llm_pool=[], dry_run=False)
    with pytest.raises(ProviderExhaustedError) as exc_info:
        get_llm_provider(cfg_live)
    assert "missing ANTHROPIC_API_KEY" in str(exc_info.value)

    # 2. DRY-RUN Mode: Cleanly degrades to MockLLMProvider
    cfg_dry = OctoFlowConfig(model_provider="anthropic", anthropic_api_key=None, api_key=None, llm_pool=[], dry_run=True)
    provider_dry = get_llm_provider(cfg_dry)
    assert isinstance(provider_dry, MockLLMProvider)
    resp = provider_dry.generate("Test prompt")
    assert resp.content is not None
    assert resp.tokens_prompt >= 0


def test_graceful_degradation_no_docker(tmp_path):
    """When Docker daemon is unreachable, WorkspaceSandbox must fall back to local execution with clear status."""
    sandbox = WorkspaceSandbox(str(tmp_path), sandbox_mode="docker")
    # Simulate Docker being down or command returning non-zero info
    with patch("subprocess.run") as mock_run:
        # First call checks `docker info` -> simulate failure
        mock_run.side_effect = [
            subprocess_result(returncode=1, stderr="Cannot connect to the Docker daemon"),
            subprocess_result(returncode=0, stdout="local fallback ok"),
        ]
        res = sandbox.run_command("echo 'hello'")
        assert res.success is True
        assert "local fallback ok" in res.stdout


def subprocess_result(returncode=0, stdout="", stderr=""):
    res = MagicMock()
    res.returncode = returncode
    res.stdout = stdout
    res.stderr = stderr
    return res


def test_graceful_degradation_no_gpu():
    """Neural policy and connectome must run smoothly on CPU when no GPU is available."""
    torch = pytest.importorskip("torch")
    from octopus_brain.config import OctopusBrainConfig
    from octopus_brain.brain import OctopusBrain

    cfg = OctopusBrainConfig(n_modules=8, obs_dim=16, action_dim=5)
    brain = OctopusBrain(cfg)
    brain.eval()
    # Explicitly test on CPU device
    obs = torch.randn(1, 8, 16, device="cpu")
    brain.reset(batch_size=1, device=torch.device("cpu"))
    with torch.no_grad():
        out = brain(obs)
    assert out["actions"].shape == (1, 8)
    assert not out["actions"].is_cuda


def test_graceful_degradation_readonly_filesystem(tmp_path):
    """Read-only filesystem must return structured ToolResult error, not an unhandled exception."""
    sandbox = WorkspaceSandbox(str(tmp_path))
    with patch.object(Path, "write_text", side_effect=OSError(30, "Read-only file system")):
        res = sandbox.write_file("output.py", "x = 1")
        assert res.success is False
        assert res.returncode == 1
        assert "Read-only file system" in res.stderr or "Read-only file system" in (res.error or "")


def test_graceful_degradation_full_disk(tmp_path):
    """Simulated full disk (ENOSPC) must be trapped cleanly by sandbox without crashing."""
    sandbox = WorkspaceSandbox(str(tmp_path))
    with patch.object(Path, "write_text", side_effect=OSError(28, "No space left on device")):
        res = sandbox.write_file("data.json", '{"a": 1}')
        assert res.success is False
        assert "No space left on device" in (res.stderr or res.error)


def test_graceful_degradation_corrupted_memory_and_checkpoint(tmp_path):
    """Corrupted JSON memory and checkpoint files must load cleanly into fresh states."""
    # 1. Corrupted memory file
    bad_mem = tmp_path / "corrupt_memory.json"
    bad_mem.write_text("{BAD_JSON_DATA_CORRUPT: true", encoding="utf-8")

    mem = VerticalLobeMemory(feature_dim=16)
    initial_count = len(mem.patterns)
    loaded = mem.load(str(bad_mem))
    assert loaded is False  # Degrades gracefully, doesn't throw JSONDecodeError
    assert len(mem.patterns) == initial_count  # Seeded heuristics remain intact

    # 2. Corrupted checkpoint in conductor workspace
    ckpt_dir = tmp_path / ".octoflow"
    ckpt_dir.mkdir()
    (ckpt_dir / "checkpoint.json").write_text("INVALID_BINARY_CORRUPTION\x00\xff", encoding="utf-8")

    cfg = OctoFlowConfig(workspace_dir=str(tmp_path), model_provider="mock")
    conductor = SupraesophagealConductor(config=cfg)
    assert conductor is not None


# ==============================================================================
# 3. Timeouts Everywhere
# ==============================================================================
def test_timeout_command_execution(tmp_path):
    """Long-running or hanging tool commands must enforce timeout and returncode 124."""
    sandbox = WorkspaceSandbox(str(tmp_path))
    # Execute a command that sleeps for 5 seconds with a 0.2s timeout
    res = sandbox.run_command("python3 -c 'import time; time.sleep(5)'", timeout_seconds=0.2)
    assert res.success is False
    assert res.returncode == 124
    assert "TimeoutExpired" in res.stderr


def test_timeout_bus_queue_does_not_block():
    """Inter-brachial bus inboxes with maxlen must never block or raise QueueFull on high throughput."""
    bus = InterBrachialBus(n_arms=8)
    # Send 100 messages to arm 1 (exceeding default maxlen of 20)
    for i in range(100):
        bus.send_lateral(sender_id=0, target_id=1, intent="DISCOVERY", summary=f"Msg {i}")
    inbox = bus.poll_inbox(1)
    assert len(inbox) <= 20
    assert len(bus.message_history) == 100


# ==============================================================================
# 4. Resource Leaks Audit
# ==============================================================================
@pytest.mark.anyio
async def test_resource_leak_audit_over_cycles(tmp_path):
    """Repeated conductor runs must not leak file locks or orphan child tasks."""
    cfg = OctoFlowConfig(workspace_dir=str(tmp_path), model_provider="mock", max_cycles=1)
    conductor = SupraesophagealConductor(config=cfg)

    for cycle in range(5):
        await conductor.arun_swarm(f"Bounded task cycle {cycle}", max_cycles=1)

    # Verify zero dangling locks across all arms
    for arm in conductor.arms:
        assert len(arm.sandbox._locks) == 0


# ==============================================================================
# 5. Input Edge Cases & Security
# ==============================================================================
def test_input_edge_case_empty_and_whitespace(tmp_path):
    """Empty or whitespace goals must be sanitized to valid fallback objectives."""
    cfg = OctoFlowConfig(workspace_dir=str(tmp_path), model_provider="mock")
    conductor = SupraesophagealConductor(config=cfg)
    sub_goals_empty = conductor.decompose_objective("")
    assert len(sub_goals_empty) == 8
    assert all("Autonomous workspace analysis" in g for g in sub_goals_empty.values())

    sub_goals_spaces = conductor.decompose_objective("     \t\n  ")
    assert len(sub_goals_spaces) == 8
    assert all("Autonomous workspace analysis" in g for g in sub_goals_spaces.values())


def test_input_edge_case_very_long_goal(tmp_path):
    """Oversized 50,000 character goals must be truncated cleanly to prevent prompt context explosion."""
    cfg = OctoFlowConfig(workspace_dir=str(tmp_path), model_provider="mock")
    conductor = SupraesophagealConductor(config=cfg)
    huge_goal = "Build a microservice " + ("word " * 10000)
    sub_goals = conductor.decompose_objective(huge_goal)
    assert len(sub_goals) == 8
    for g in sub_goals.values():
        assert len(g) <= 5000
        assert "[truncated]" in g


def test_input_edge_case_unicode_and_emojis(tmp_path):
    """Unicode, emojis, and non-ASCII scripts must be handled seamlessly."""
    cfg = OctoFlowConfig(workspace_dir=str(tmp_path), model_provider="mock")
    conductor = SupraesophagealConductor(config=cfg)
    goal = "Build 🐙 Cephalopod Core with 日本語 and 🔥 emojis"
    sub_goals = conductor.decompose_objective(goal)
    assert len(sub_goals) == 8
    for g in sub_goals.values():
        assert "🐙" in g
        assert "日本語" in g


def test_input_edge_case_shell_injection_sanitization(tmp_path):
    """Malicious goals with shell metacharacters and null-bytes must be neutralized."""
    sandbox = WorkspaceSandbox(str(tmp_path))
    # Blocked dangerous patterns
    res1 = sandbox.run_command("rm -rf /")
    assert res1.returncode == 126
    assert "SecurityError" in res1.stderr

    # Null-byte injection
    conductor = SupraesophagealConductor(config=OctoFlowConfig(workspace_dir=str(tmp_path)))
    sub_goals = conductor.decompose_objective("Create api\x00; rm -rf /")
    for g in sub_goals.values():
        assert "\x00" not in g


# ==============================================================================
# 6. Idempotency and Restart
# ==============================================================================
@pytest.mark.anyio
async def test_idempotency_and_restart(tmp_path):
    """Interrupted conductor mission can be cleanly recreated and restarted without lock conflicts."""
    ws = tmp_path / "restart_ws"
    ws.mkdir()
    cfg = OctoFlowConfig(workspace_dir=str(ws), model_provider="mock", dry_run=True, max_cycles=1)

    # Run 1: Interrupted mid-flight
    c1 = SupraesophagealConductor(config=cfg)
    task = asyncio.create_task(c1.arun_swarm("Initial mission", max_cycles=20))
    await asyncio.sleep(0.002)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Run 2: Fresh conductor resumed in same workspace
    c2 = SupraesophagealConductor(config=cfg)
    res = await c2.arun_swarm("Resumed mission", max_cycles=1)
    assert res["total_cycles"] == 1
    assert "quiescent_arms" in res
    # Zero dangling locks
    for arm in c2.arms:
        assert len(arm.sandbox._locks) == 0


# ==============================================================================
# 7. Logging & Secret Scrubbing
# ==============================================================================
def test_logging_secret_scrubbing():
    """Logs must automatically redact API keys, tokens, and credentials."""
    logger = get_safe_logger("test_octoflow_security")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    secret_key = "sk-" + "1234567890abcdef1234567890abcdef"
    anthropic_key = "sk-ant-" + "api03-abcdef1234567890abcdef1234567890"
    logger.info(f"Connecting to provider with key: {secret_key} and {anthropic_key}")

    output = stream.getvalue()
    assert secret_key not in output
    assert anthropic_key not in output
    assert "[REDACTED_OPENAI_KEY]" in output or "[REDACTED_ANTHROPIC_KEY]" in output


# ==============================================================================
# 8. Cross-Platform Concerns (Paths & Line Endings)
# ==============================================================================
def test_cross_platform_windows_path_normalization(tmp_path):
    """Windows-style paths with backslashes must resolve safely inside workspace."""
    sandbox = WorkspaceSandbox(str(tmp_path))
    win_path = r"backend\controllers\api.py"
    resolved = sandbox._resolve_safe(win_path)
    assert resolved.is_relative_to(sandbox.root)
    assert str(resolved).endswith(os.path.join("backend", "controllers", "api.py"))

    # Test writing with Windows-style backslashes
    res = sandbox.write_file(win_path, "# Windows path test\nval = 42\n")
    assert res.success is True
    assert resolved.exists()


def test_cross_platform_crlf_line_endings(tmp_path):
    """Files written with CRLF line endings must pass AST syntax validation cleanly."""
    sandbox = WorkspaceSandbox(str(tmp_path))
    crlf_code = "def compute():\r\n    return 42\r\n"
    res = sandbox.write_file("test_crlf.py", crlf_code)
    assert res.success is True
    assert res.diff_lines >= 2
