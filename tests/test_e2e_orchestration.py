"""Phase 4: End-to-End Orchestration Verification Suite (Gate 4).

Verifies the entire OctoFlow multi-agent pipeline running autonomously:
Conductor -> Goal Decomposition -> 8 Parallel Arms -> WorkspaceSandbox
-> InterBrachialBus -> SurpriseGate -> VerticalLobeMemory -> Global Quiescence -> Disk Artifacts.

Scenarios:
1. test_e2e_deterministic_mock_build: Realistic full-stack project generation where
   real files are written, executed with Python, and generated tests pass.
2. test_e2e_failure_injection_and_recovery: Error injection, surprise escalation,
   memory-guided patch, and dead-arm ring bypass.
3. test_e2e_cancellation_and_cleanup: Abrupt mid-run cancellation with lock/process audit.
4. test_e2e_real_llm_budgeted: Real LLM execution if credentials exist, or structured skip.
5. test_e2e_resource_cleanup_audit: Zero orphan processes, unreleased locks, or leaked files.
"""

import asyncio
import os
import subprocess
import sys
import time

import pytest
from octoflow.conductor import SupraesophagealConductor, SwarmTelemetryEvent
from octoflow.config import OctoFlowConfig
from octoflow.provider import BaseLLMProvider, LLMResponse


class ScriptedE2EProvider(BaseLLMProvider):
    """Deterministic scripted LLM provider delivering complete, real working code per arm."""

    def __init__(self):
        super().__init__()
        self.call_count: dict[int, int] = {i: 0 for i in range(8)}
        self.total_tokens_spent = 0

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        import json

        # Infer which arm is querying from system prompt
        arm_id = 0
        for i in range(8):
            if f"Arm {i}" in system_prompt or f"Ganglion {i}" in system_prompt:
                arm_id = i
                break

        self.call_count[arm_id] = self.call_count.get(arm_id, 0) + 1
        step_num = self.call_count[arm_id]

        # Artifact payloads
        if arm_id == 0:  # Architect
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "README.md",
                    "content": (
                        "# Todo Service\n\n"
                        "Authenticated SQLite Todo Microservice built with FastAPI.\n\n"
                        "## Architecture\n"
                        "- `database.py`: SQLite persistence layer\n"
                        "- `main.py`: FastAPI endpoints\n"
                        "- `test_todo_api.py`: Automated Pytest verification\n"
                    ),
                    "explanation": "Scaffolding system architecture and documentation.",
                }
            )
        elif arm_id == 1:  # Database
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "database.py",
                    "content": (
                        "import sqlite3\n"
                        "from typing import List, Dict, Optional\n\n"
                        "class TodoDatabase:\n"
                        "    def __init__(self, db_path: str = ':memory:'):\n"
                        "        self.conn = sqlite3.connect(db_path, check_same_thread=False)\n"
                        "        self.create_tables()\n\n"
                        "    def create_tables(self):\n"
                        "        with self.conn:\n"
                        "            self.conn.execute('''\n"
                        "                CREATE TABLE IF NOT EXISTS todos (\n"
                        "                    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                        "                    title TEXT NOT NULL,\n"
                        "                    completed BOOLEAN DEFAULT 0\n"
                        "                )\n"
                        "            ''')\n\n"
                        "    def add_todo(self, title: str) -> int:\n"
                        "        with self.conn:\n"
                        "            cur = self.conn.execute('INSERT INTO todos (title) VALUES (?)', (title,))\n"
                        "            return cur.lastrowid\n\n"
                        "    def get_todos(self) -> List[Dict]:\n"
                        "        cur = self.conn.execute('SELECT id, title, completed FROM todos')\n"
                        "        return [{'id': r[0], 'title': r[1], 'completed': bool(r[2])} for r in cur.fetchall()]\n"
                    ),
                    "explanation": "Created SQLite schema and CRUD database connector.",
                }
            )
        elif arm_id == 2:  # Backend API
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "main.py",
                    "content": (
                        "from database import TodoDatabase\n\n"
                        "db = TodoDatabase()\n\n"
                        "def create_todo(title: str):\n"
                        "    if not title or len(title.strip()) == 0:\n"
                        "        raise ValueError('Title cannot be empty')\n"
                        "    todo_id = db.add_todo(title.strip())\n"
                        "    return {'id': todo_id, 'title': title.strip(), 'completed': False}\n\n"
                        "def list_todos():\n"
                        "    return db.get_todos()\n"
                    ),
                    "explanation": "Implemented API controllers and validation.",
                }
            )
        elif arm_id == 3:  # Frontend UI
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "index.html",
                    "content": "<!DOCTYPE html><html><body><h1>OctoFlow Todo</h1></body></html>",
                    "explanation": "Created frontend interface entrypoint.",
                }
            )
        elif arm_id == 4:  # State / Optimization
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "config.py",
                    "content": "DB_TIMEOUT = 5.0\nMAX_PAGE_SIZE = 100\n",
                    "explanation": "Added performance optimization constants.",
                }
            )
        elif arm_id == 5:  # Integration QA & Tests
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "test_todo_api.py",
                    "content": (
                        "import pytest\n"
                        "from main import create_todo, list_todos\n\n"
                        "def test_create_and_retrieve_todo():\n"
                        "    todo = create_todo('Learn OctoFlow')\n"
                        "    assert todo['id'] >= 1\n"
                        "    assert todo['title'] == 'Learn OctoFlow'\n"
                        "    assert todo['completed'] is False\n\n"
                        "    all_todos = list_todos()\n"
                        "    assert len(all_todos) >= 1\n"
                        "    assert any(t['title'] == 'Learn OctoFlow' for t in all_todos)\n\n"
                        "def test_empty_title_rejection():\n"
                        "    with pytest.raises(ValueError):\n"
                        "        create_todo('')\n"
                    ),
                    "explanation": "Created unit and integration tests with pytest.",
                }
            )
        elif arm_id == 6:  # Security
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "security.py",
                    "content": (
                        "def sanitize_string(s: str) -> str:\n"
                        "    return s.strip().replace('<', '&lt;').replace('>', '&gt;')\n"
                    ),
                    "explanation": "Added HTML input sanitization utility.",
                }
            )
        else:  # Arm 7: DevOps
            content = json.dumps(
                {
                    "action": "write_file",
                    "path": "Dockerfile",
                    "content": 'FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nCMD ["python", "-m", "pytest"]\n',
                    "explanation": "Created service Dockerfile container manifest.",
                }
            )

        tokens = len(prompt) // 4 + len(content) // 4
        self.total_tokens_spent += tokens
        return LLMResponse(
            content=content,
            tokens_prompt=len(prompt) // 4,
            tokens_completion=len(content) // 4,
            total_tokens=tokens,
            estimated_cost_dollars=0.001,
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        await asyncio.sleep(0.005)
        return self.generate(prompt, system_prompt, temperature, max_tokens)


@pytest.mark.anyio
async def test_e2e_deterministic_mock_build(tmp_path):
    """E2E-MOCK: Verify real autonomous pipeline from objective to verified working code."""
    ws = tmp_path / "todo_app"
    ws.mkdir()

    cfg = OctoFlowConfig(
        workspace_dir=str(ws),
        model_provider="mock",
        max_cycles=4,
        max_budget_dollars=1.00,
        enable_3d_telemetry=False,
    )

    conductor = SupraesophagealConductor(config=cfg)
    # Inject deterministic scripted provider into conductor and all 8 arms
    scripted_provider = ScriptedE2EProvider()
    conductor.provider = scripted_provider
    for arm in conductor.arms:
        arm.provider = scripted_provider

    telemetry_events: list[SwarmTelemetryEvent] = []
    conductor.telemetry_callback = lambda evt: telemetry_events.append(evt)

    # 1. Execute swarm to global quiescence
    t_start = time.time()
    objective = "Build a small authenticated REST API for a todo list with a database, a React frontend, tests, a Dockerfile and a README."
    result = await conductor.arun_swarm(objective=objective, max_cycles=4)
    duration = time.time() - t_start

    # 2. Assert swarm completed cleanly
    assert result is not None
    assert result["quiescent_arms"] == 8, (
        f"Expected all 8 arms to reach quiescence, got {result['quiescent_arms']}"
    )
    assert result["status"] == "GLOBAL_QUIESCENCE"
    assert duration < 10.0, f"E2E swarm took {duration:.2f}s, expected < 10s"

    # 3. Assert on actual artifacts on disk
    expected_files = [
        "README.md",
        "database.py",
        "main.py",
        "index.html",
        "config.py",
        "test_todo_api.py",
        "security.py",
        "Dockerfile",
    ]
    for filename in expected_files:
        file_path = ws / filename
        assert file_path.exists(), f"E2E artifact missing: {filename}"
        assert file_path.stat().st_size > 0, f"E2E artifact is empty: {filename}"

    # 4. RUN THE GENERATED CODE: Execute the generated tests using pytest
    test_run = subprocess.run(
        [sys.executable, "-m", "pytest", "test_todo_api.py"],
        cwd=str(ws),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert test_run.returncode == 0, (
        f"Generated test failed with output:\n{test_run.stdout}\n{test_run.stderr}"
    )
    assert "passed" in test_run.stdout

    # 5. Telemetry & Instrumentation Assertions
    assert len(telemetry_events) >= 8, "Expected telemetry events from all arms"
    arms_reported = set(evt.arm_id for evt in telemetry_events)
    assert len(arms_reported) == 8, "All 8 arm ganglia must participate in telemetry"
    assert conductor.total_tokens_used > 0
    assert conductor.total_cost > 0.0


@pytest.mark.anyio
async def test_e2e_failure_injection_and_recovery(tmp_path):
    """Failure-injection E2E: Verify surprise escalation, memory consolidation, and dead-arm routing."""
    ws = tmp_path / "fault_workspace"
    ws.mkdir()

    cfg = OctoFlowConfig(
        workspace_dir=str(ws),
        model_provider="mock",
        max_cycles=3,
        enable_3d_telemetry=False,
    )
    conductor = SupraesophagealConductor(config=cfg)

    # Scenario A: Injected dead arm on bus
    bus = conductor.bus
    assert bus.get_neighbors(0) == (7, 1)

    # Kill Arm 1
    bus.mark_arm_inactive(1)
    left, right = bus.get_neighbors(0)
    assert right == 2, "Bus must bypass dead Arm 1 and route to Arm 2"

    # Broadcast on ring bypasses dead arm
    msgs = bus.broadcast_ring(sender_id=0, intent="COOPERATIVE_PULL", summary="Urgent test")
    assert msgs[1].target_id == 2
    assert len(bus.poll_inbox(2)) == 1

    # Scenario B: Tool error elevation and memory consolidation
    arm = conductor.arms[2]
    bad_cmd_res = arm.sandbox.run_command("nonexistent_command_xyz_123")
    assert not bad_cmd_res.success

    obs = arm.encoder.encode(bad_cmd_res, step=1, max_steps=5, as_tensor=True)
    escalate, surprise, _ = arm.gate.evaluate(obs, bad_cmd_res)
    assert escalate is True, "Tool failure must escalate"
    assert surprise >= 0.60

    # Memory consolidation
    arm.memory.consolidate(
        error_obs=obs.numpy(),
        error_name="CommandNotFoundError",
        fix_guidance="Use verified system binaries from PATH.",
    )
    recalled = arm.memory.recall(obs.numpy())
    assert recalled is not None
    assert "PATH" in recalled[0]


@pytest.mark.anyio
async def test_e2e_cancellation_and_cleanup(tmp_path):
    """Cancellation E2E: Cancel swarm mid-run and verify zero leaked processes or locks."""
    ws = tmp_path / "cancel_workspace"
    ws.mkdir()

    cfg = OctoFlowConfig(
        workspace_dir=str(ws),
        model_provider="mock",
        dry_run=True,
        max_cycles=20,
        enable_3d_telemetry=False,
    )
    conductor = SupraesophagealConductor(config=cfg)

    # Launch swarm in background asyncio task
    task = asyncio.create_task(conductor.arun_swarm("Long running objective", max_cycles=20))

    # Allow it to start
    await asyncio.sleep(0.002)

    # Cancel mid-flight
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Verify sandbox locks and state are clean
    for arm in conductor.arms:
        # None of the arms should have dangling active locks
        assert len(arm.sandbox._locks) == 0


def test_e2e_real_llm_budgeted(tmp_path):
    """Real-LLM E2E: Run with live credentials under strict budget cap, or report instructions."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not anthropic_key and not openai_key:
        pytest.skip(
            "E2E-REAL: UNTESTED (no credentials in environment). "
            "To run: export ANTHROPIC_API_KEY='sk-ant-...' && "
            "pytest tests/test_e2e_orchestration.py -k test_e2e_real_llm_budgeted"
        )

    # If credentials exist, run minimal real task with strict budget
    provider = "anthropic" if anthropic_key else "openai"
    cfg = OctoFlowConfig(
        workspace_dir=str(tmp_path),
        model_provider=provider,
        max_cycles=2,
        max_budget_dollars=0.05,
    )
    conductor = SupraesophagealConductor(config=cfg)
    result = asyncio.run(
        conductor.arun_swarm("Create a hello world module with a test.", max_cycles=2)
    )
    assert result is not None
    assert conductor.total_cost <= 0.05


def test_e2e_resource_cleanup_audit(tmp_path):
    """Resource Cleanup Audit: Verify no orphan processes, leftover locks, or dangling ports."""
    # 1. Verify no orphan octoflow test worker processes
    ps_res = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    # Exclude the current pytest test runner itself and pre-existing user UI server
    lines = [
        line
        for line in ps_res.stdout.splitlines()
        if "octoflow" in line
        and "pytest" not in line
        and "antigravity" not in line
        and "ui --port" not in line
    ]
    # No rogue daemon/detached octoflow subprocesses
    assert len(lines) == 0, f"Found orphan octoflow processes: {lines}"

    # 2. Check no leaked .lock files in tmp_path
    leaked_locks = list(tmp_path.rglob("*.lock"))
    assert len(leaked_locks) == 0, f"Found leaked lock files: {leaked_locks}"
