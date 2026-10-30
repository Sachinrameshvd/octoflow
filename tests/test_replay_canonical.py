"""Offline verification of canonical tasks using recorded LLM cassettes.

Verifies that rate_limiter and fastapi_todo pass acceptance testing offline
without calling any live external LLM endpoints.
"""

from pathlib import Path

from octoflow.bench import BENCHMARK_SUITE, run_single_benchmark_run
from octoflow.cassette import ReplayProvider

REPO_ROOT = Path(__file__).resolve().parent.parent
RATE_LIMITER_CASSETTE = REPO_ROOT / "cassettes" / "rate_limiter"
FASTAPI_TODO_CASSETTE = REPO_ROOT / "cassettes" / "fastapi_todo"


def test_replay_canonical_rate_limiter(tmp_path):
    """Replay rate-limiter cassette offline and verify acceptance tests pass."""
    assert RATE_LIMITER_CASSETTE.exists()
    assert (RATE_LIMITER_CASSETTE / "cassette.json").exists()

    task = next(t for t in BENCHMARK_SUITE if t.id == "rate_limiter")
    replay_provider = ReplayProvider(
        cassette_dir=RATE_LIMITER_CASSETTE,
        workspace_root=tmp_path,
    )

    result = run_single_benchmark_run(
        task=task,
        mode="gated",
        provider_name="replay",
        workspace_dir=str(tmp_path),
        custom_provider=replay_provider,
        max_cycles=3,
    )

    assert result["task"] == "rate_limiter"
    assert result["acceptance_test_passed"] is True
    assert "limiter.py" in result["files_written"]


def test_replay_canonical_fastapi_todo(tmp_path):
    """Replay fastapi_todo cassette offline and verify acceptance tests pass."""
    assert FASTAPI_TODO_CASSETTE.exists()
    assert (FASTAPI_TODO_CASSETTE / "cassette.json").exists()

    task = next(t for t in BENCHMARK_SUITE if t.id == "fastapi_todo")
    replay_provider = ReplayProvider(
        cassette_dir=FASTAPI_TODO_CASSETTE,
        workspace_root=tmp_path,
    )

    result = run_single_benchmark_run(
        task=task,
        mode="gated",
        provider_name="replay",
        workspace_dir=str(tmp_path),
        custom_provider=replay_provider,
        max_cycles=3,
    )

    assert result["task"] == "fastapi_todo"
    assert result["acceptance_test_passed"] is True
    assert "app.py" in result["files_written"]
