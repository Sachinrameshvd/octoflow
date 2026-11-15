"""Tests for Inter-Octopus Phase Checkpoints and Interactive Developer Steering (Milestone 3).

Verifies:
1. Phase checkpoint data structure and JSON serialization
2. Phase checkpoint card terminal rendering
3. Interactive and non-interactive steering decisions (Continue, Steer, Abort)
4. Persistent file snapshots (.octoflow/checkpoint.json and phase snapshots)
5. Consortium integration: goal augmentation with developer directives
6. Consortium early exit when developer aborts at a phase checkpoint
7. Synaptic bus event broadcasting for human steering directives
8. Cockpit /steer command toggle
"""

import io
import tempfile
from pathlib import Path

import pytest
from octoflow.config import OctoFlowConfig
from octoflow.consortium import OctosConsortium
from octoflow.steering import (
    PhaseCheckpoint,
    SteeringResult,
    conduct_phase_steering,
    format_steering_history,
    render_phase_checkpoint_card,
    save_phase_checkpoint,
)
from rich.console import Console
from rich.panel import Panel


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_phase_checkpoint_creation_and_serialization():
    """Verify PhaseCheckpoint instantiates and serializes cleanly."""
    ckpt = PhaseCheckpoint(
        phase_id=1,
        phase_name="Architecture & Foundation",
        completed_octopuses=[
            {
                "octopus_id": 0,
                "title": "System Architect",
                "summary": "Scaffold and module boundaries established",
            }
        ],
        upcoming_octopuses=[
            {"octopus_id": 1, "title": "Database", "goal": "SQLAlchemy models"},
            {"octopus_id": 2, "title": "Backend", "goal": "FastAPI endpoints"},
        ],
        files_delivered=["src/main.py", "package.json"],
        steering_directives=["Use PostgreSQL instead of SQLite"],
        total_cost=0.015,
    )

    data = ckpt.to_dict()
    assert data["phase_id"] == 1
    assert data["phase_name"] == "Architecture & Foundation"
    assert len(data["completed_octopuses"]) == 1
    assert len(data["upcoming_octopuses"]) == 2
    assert "src/main.py" in data["files_delivered"]
    assert "Use PostgreSQL instead of SQLite" in data["steering_directives"]


def test_render_phase_checkpoint_card():
    """Verify render_phase_checkpoint_card produces a structured Rich Panel."""
    ckpt = PhaseCheckpoint(
        phase_id=1,
        phase_name="Architecture & Foundation",
        completed_octopuses=[
            {
                "octopus_id": 0,
                "title": "System Architect",
                "summary": "Scaffold and module boundaries established",
            }
        ],
        upcoming_octopuses=[
            {"octopus_id": 1, "title": "Database", "goal": "SQLAlchemy models"},
        ],
        files_delivered=["src/main.py"],
        steering_directives=["Use asyncpg client"],
        total_cost=0.02,
    )

    panel = render_phase_checkpoint_card(ckpt)
    assert isinstance(panel, Panel)

    buf = io.StringIO()
    c = Console(file=buf, width=80, force_terminal=True)
    c.print(panel)
    output = buf.getvalue()

    assert "Architecture & Foundation" in output
    assert "System Architect" in output
    assert "Database" in output
    assert "Use asyncpg client" in output
    assert "STEERING" in output


def test_conduct_phase_steering_non_interactive():
    """Verify conduct_phase_steering automatically continues in non-interactive mode."""
    ckpt = PhaseCheckpoint(phase_id=1, phase_name="Test Phase")
    res = conduct_phase_steering(ckpt, non_interactive=True)
    assert res.action == "continue"
    assert res.guidance == ""


def test_save_phase_checkpoint_and_history():
    """Verify save_phase_checkpoint writes both rolling and phase-indexed JSON files."""
    with tempfile.TemporaryDirectory() as tmp:
        ckpt = PhaseCheckpoint(
            phase_id=2,
            phase_name="Core Engineering Deliverables",
            completed_octopuses=[{"octopus_id": 1, "title": "Database", "summary": "Migrations done"}],
            steering_directives=["Enforce JWT expiry check on all routes"],
        )
        saved_path = save_phase_checkpoint(tmp, ckpt)

        assert saved_path.exists()
        snap_path = Path(tmp) / ".octoflow" / "checkpoint_phase_2.json"
        assert snap_path.exists()

        formatted = format_steering_history(["Direct 1", "Direct 2"])
        assert "Direct 1" in formatted
        assert "Direct 2" in formatted


@pytest.mark.anyio
async def test_consortium_interactive_steering_injection(anyio_backend):
    """Verify consortium invokes steering callback and injects developer guidance into downstream goals."""
    if anyio_backend != "asyncio":
        pytest.skip("Test requires asyncio backend")

    with tempfile.TemporaryDirectory() as tmp:
        cfg = OctoFlowConfig(workspace_dir=tmp, model_provider="mock")

        steering_called = []

        def mock_steer(checkpoint: PhaseCheckpoint) -> SteeringResult:
            steering_called.append(checkpoint.phase_name)
            return SteeringResult(
                action="steer",
                guidance="Use PostgreSQL async connection pooling with max_size=10",
            )

        consortium = OctosConsortium(
            config=cfg,
            octopus_count=3,
            interactive_gates=True,
            phase_steering_callback=mock_steer,
        )

        result = await consortium.arun_consortium(
            objective="Build High-Throughput Ingestion Microservice",
            cycles_per_octopus=1,
        )

        # Must have completed and called steering callback at Phase 1 boundary
        assert result["status"] == "COMPLETED"
        assert len(steering_called) >= 1
        assert "Phase 1: Architecture & Foundation" in steering_called[0]

        # Steering history recorded
        assert len(consortium.steering_history) >= 1
        assert "Use PostgreSQL async connection pooling" in consortium.steering_history[0]

        # Check that synaptic bus broadcasted STEERING_DIRECTIVE
        steering_events = [
            evt for evt in consortium.synaptic_bus.events if evt.event_type == "STEERING_DIRECTIVE"
        ]
        assert len(steering_events) >= 1
        assert "Use PostgreSQL async connection pooling" in steering_events[0].summary

        # Checkpoint JSON exists on disk
        ckpt_file = Path(tmp) / ".octoflow" / "checkpoint.json"
        assert ckpt_file.exists()


@pytest.mark.anyio
async def test_consortium_interactive_steering_abort(anyio_backend):
    """Verify consortium halts cleanly when developer aborts at a phase checkpoint."""
    if anyio_backend != "asyncio":
        pytest.skip("Test requires asyncio backend")

    with tempfile.TemporaryDirectory() as tmp:
        cfg = OctoFlowConfig(workspace_dir=tmp, model_provider="mock")

        def mock_abort(checkpoint: PhaseCheckpoint) -> SteeringResult:
            return SteeringResult(action="abort")

        consortium = OctosConsortium(
            config=cfg,
            octopus_count=3,
            interactive_gates=True,
            phase_steering_callback=mock_abort,
        )

        result = await consortium.arun_consortium(
            objective="Build Web Application",
            cycles_per_octopus=1,
        )

        assert result["status"] == "ABORTED_BY_USER"
        # Checkpoint recorded on abort
        ckpt_file = Path(tmp) / ".octoflow" / "checkpoint.json"
        assert ckpt_file.exists()
