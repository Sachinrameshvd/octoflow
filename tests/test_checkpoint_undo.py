"""Unit and integration tests for git checkpointing, rollback, and run provenance tracking."""

import subprocess
from pathlib import Path

import pytest
from octoflow.checkpoint import (
    branch_exists,
    create_stash_snapshot,
    finalize_run,
    get_current_branch,
    get_current_head,
    init_git_repo,
    is_git_repo,
    is_working_tree_clean,
    list_runs,
    preflight_and_start_run,
    undo_run,
)
from octoflow.cli import app
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def temp_runs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate OctoFlow runs ledger into a temporary directory."""
    runs_dir = tmp_path / "octoflow_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OCTOFLOW_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("OCTOFLOW_TESTING", "1")
    return runs_dir


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a clean git repository configured with test user credentials."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@octoflow.dev"], cwd=repo, check=True)
    readme = repo / "README.md"
    readme.write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)
    return repo


def test_git_primitives_clean_repo(git_repo: Path):
    """Verify low-level git primitives identify clean repo state."""
    assert is_git_repo(git_repo)
    assert is_working_tree_clean(git_repo)
    head = get_current_head(git_repo)
    assert head is not None and len(head) == 40
    branch = get_current_branch(git_repo)
    assert branch in ["main", "master"]


def test_git_primitives_dirty_repo(git_repo: Path):
    """Verify dirty working tree detection and stash snapshotting."""
    readme = git_repo / "README.md"
    readme.write_text("# Test Repo Modified\n", encoding="utf-8")
    assert not is_working_tree_clean(git_repo)

    stash_hash = create_stash_snapshot(git_repo)
    assert stash_hash is not None and len(stash_hash) == 40
    # Working tree should still be dirty (stash create does not modify tree)
    assert not is_working_tree_clean(git_repo)


def test_clean_run_lifecycle_and_undo(git_repo: Path, temp_runs_dir: Path):
    """Verify full clean run: starts branch, commits changes, and undo deletes branch returning to original."""
    orig_branch = get_current_branch(git_repo)
    orig_head = get_current_head(git_repo)

    meta = preflight_and_start_run(
        workspace_dir=git_repo,
        goal="Build authentication module with jwt",
        mode="software_dev",
        model="fake",
    )
    assert meta is not None
    assert meta.is_git is True
    assert meta.original_branch == orig_branch
    assert meta.original_head == orig_head
    assert meta.run_branch is not None
    assert meta.run_branch.startswith("octoflow/run-")
    assert get_current_branch(git_repo) == meta.run_branch

    # Swarm generates files
    gen_file = git_repo / "auth.py"
    gen_file.write_text("def authenticate(): return True\n", encoding="utf-8")

    meta = finalize_run(meta, success=True, files_written=["auth.py"])
    assert meta.status == "COMPLETED"
    assert meta.commit_hash is not None
    assert gen_file.exists()

    # Now execute undo
    undo_res = undo_run(workspace_dir=git_repo, run_id=meta.run_id, confirm=False)
    assert undo_res["status"] == "SUCCESS"
    assert undo_res["original_branch"] == orig_branch
    assert get_current_branch(git_repo) == orig_branch
    assert not branch_exists(git_repo, meta.run_branch)
    # Generated file should be completely gone
    assert not gen_file.exists()
    assert (git_repo / "README.md").exists()


def test_dirty_working_tree_aborts_without_allow_dirty(git_repo: Path, temp_runs_dir: Path):
    """Dirty tree without --allow-dirty aborts with a clear message and modifies nothing."""
    dirty_file = git_repo / "uncommitted.txt"
    dirty_file.write_text("Uncommitted work\n", encoding="utf-8")
    orig_branch = get_current_branch(git_repo)

    with pytest.raises(ValueError) as excinfo:
        preflight_and_start_run(
            workspace_dir=git_repo,
            goal="Add feature",
            allow_dirty=False,
        )
    assert "Working tree has uncommitted changes" in str(excinfo.value)
    assert "--allow-dirty" in str(excinfo.value)
    assert get_current_branch(git_repo) == orig_branch
    assert dirty_file.exists()


def test_dirty_working_tree_with_allow_dirty_and_undo_restores_stash(
    git_repo: Path, temp_runs_dir: Path
):
    """Dirty tree with --allow-dirty captures stash, commits run, and undo restores dirty changes."""
    orig_branch = get_current_branch(git_repo)
    readme = git_repo / "README.md"
    readme.write_text("# Modified Before Run\n", encoding="utf-8")
    draft = git_repo / "draft_notes.txt"
    draft.write_text("important user notes\n", encoding="utf-8")

    meta = preflight_and_start_run(
        workspace_dir=git_repo,
        goal="Task with dirty tree",
        allow_dirty=True,
    )
    assert meta is not None
    assert meta.stash_hash is not None

    # Swarm writes generated code
    code = git_repo / "solution.py"
    code.write_text("print('finished')\n", encoding="utf-8")

    meta = finalize_run(meta, success=True, files_written=["solution.py"])
    assert meta.status == "COMPLETED"

    # Undo run
    undo_res = undo_run(workspace_dir=git_repo, run_id=meta.run_id, confirm=False)
    assert undo_res["status"] == "SUCCESS"
    assert get_current_branch(git_repo) == orig_branch
    assert not code.exists()
    # Stashed uncommitted work is restored!
    assert draft.exists()
    assert draft.read_text(encoding="utf-8") == "important user notes\n"
    assert readme.read_text(encoding="utf-8") == "# Modified Before Run\n"


def test_undo_refuses_to_delete_unrelated_or_unowned_branch(git_repo: Path, temp_runs_dir: Path):
    """Undo strictly rejects deleting branches not created by OctoFlow."""
    # Create an arbitrary user branch that happens to have some name
    subprocess.run(["git", "checkout", "-b", "octoflow/run-fake123"], cwd=git_repo, check=True)
    subprocess.run(["git", "checkout", "master"], cwd=git_repo, check=True)

    with pytest.raises(ValueError) as excinfo:
        undo_run(workspace_dir=git_repo, run_id="fake123", confirm=False)
    assert "not found in OctoFlow run ledger" in str(excinfo.value)

    # Verify branch was NOT deleted
    assert branch_exists(git_repo, "octoflow/run-fake123")


def test_branch_collision_aborts(
    git_repo: Path, temp_runs_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    """Detects and blocks duplicate run branch creation."""
    # Monkeypatch run_id creation to trigger collision
    import octoflow.checkpoint as chk_mod

    class MockUUID:
        hex = "collision-test"

    monkeypatch.setattr(chk_mod.uuid, "uuid4", lambda: MockUUID())
    monkeypatch.setattr(chk_mod.time, "time", lambda: 0)

    # Branch name will be octoflow/run-0-collis (since hex[:6] is collis)
    colliding_branch = "octoflow/run-0-collis"
    subprocess.run(["git", "branch", colliding_branch], cwd=git_repo, check=True)

    with pytest.raises(ValueError) as excinfo:
        preflight_and_start_run(
            workspace_dir=git_repo,
            goal="Collision goal",
        )
    assert "already exists" in str(excinfo.value)


def test_non_git_directory_behavior(tmp_path: Path, temp_runs_dir: Path):
    """Non-git workspace requires --init-git or --no-checkpoint."""
    non_git = tmp_path / "plain_dir"
    non_git.mkdir()

    # Without flags -> raises ValueError with helpful message
    with pytest.raises(ValueError) as excinfo:
        preflight_and_start_run(
            workspace_dir=non_git,
            goal="Goal in plain folder",
            init_git=False,
            no_checkpoint=False,
        )
    assert "Workspace is not a git repository" in str(excinfo.value)
    assert "--init-git" in str(excinfo.value)
    assert "--no-checkpoint" in str(excinfo.value)

    # With --no-checkpoint -> runs without git
    meta_no_chk = preflight_and_start_run(
        workspace_dir=non_git,
        goal="Goal in plain folder without git",
        no_checkpoint=True,
    )
    assert meta_no_chk is not None
    assert meta_no_chk.is_git is False
    assert not is_git_repo(non_git)

    # With --init-git -> initializes git repository
    meta_init = preflight_and_start_run(
        workspace_dir=non_git,
        goal="Goal with git init",
        init_git=True,
    )
    assert meta_init is not None
    assert meta_init.is_git is True
    assert is_git_repo(non_git)
    assert meta_init.run_branch is not None
    assert meta_init.run_branch.startswith("octoflow/run-")


def test_dry_run_creates_no_checkpoint(git_repo: Path, temp_runs_dir: Path):
    """Dry runs do not create branches or checkpoints."""
    orig_branch = get_current_branch(git_repo)
    meta = preflight_and_start_run(
        workspace_dir=git_repo,
        goal="Dry run test",
        dry_run=True,
    )
    assert meta is None
    assert get_current_branch(git_repo) == orig_branch


def test_failed_run_commits_as_wip(git_repo: Path, temp_runs_dir: Path):
    """If run fails or is interrupted, generated changes are committed as WIP so nothing is lost."""
    meta = preflight_and_start_run(
        workspace_dir=git_repo,
        goal="Incomplete task",
    )
    wip_file = git_repo / "partial.py"
    wip_file.write_text("# work in progress\n", encoding="utf-8")

    meta = finalize_run(meta, success=False, files_written=["partial.py"])
    assert meta.status == "WIP"
    assert meta.commit_hash is not None

    log_res = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=git_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "[wip]" in log_res.stdout


def test_cli_runs_and_undo_commands(git_repo: Path, temp_runs_dir: Path):
    """Test CLI commands 'octoflow runs' and 'octoflow undo --yes'."""
    meta = preflight_and_start_run(
        workspace_dir=git_repo,
        goal="CLI integration goal",
    )
    f = git_repo / "cli_created.py"
    f.write_text("x = 1\n", encoding="utf-8")
    finalize_run(meta, success=True, files_written=["cli_created.py"])

    # Test octoflow runs
    res_runs = runner.invoke(app, ["runs", "--dir", str(git_repo)])
    assert res_runs.exit_code == 0
    assert meta.run_id in res_runs.output
    assert "COMPLETED" in res_runs.output

    # Test octoflow undo
    res_undo = runner.invoke(app, ["undo", meta.run_id, "--dir", str(git_repo), "--yes"])
    assert res_undo.exit_code == 0
    assert "Cleanly undone OctoFlow run" in res_undo.output
    assert not f.exists()


def test_cli_run_dirty_abort_and_allow_dirty(
    git_repo: Path, temp_runs_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test octoflow run CLI command behavior with dirty working tree."""
    (git_repo / "dirty.txt").write_text("dirty content", encoding="utf-8")

    # Clean run without --allow-dirty should fail
    res = runner.invoke(app, ["run", "test goal", "--model", "fake", "--dir", str(git_repo)])
    assert res.exit_code != 0
    assert (
        "Working tree has uncommitted changes" in res.output
        or "CHECKPOINT PRE-FLIGHT ERROR" in res.output
    )

    # With --allow-dirty, it proceeds
    res_allow = runner.invoke(
        app, ["run", "test goal", "--model", "fake", "--dir", str(git_repo), "--allow-dirty"]
    )
    assert res_allow.exit_code == 0


def test_undo_defaults_to_latest_run(git_repo: Path, temp_runs_dir: Path):
    """When run_id is omitted, undo targets the most recent run for the workspace."""
    meta1 = preflight_and_start_run(workspace_dir=git_repo, goal="First run")
    (git_repo / "f1.txt").write_text("1")
    finalize_run(meta1, success=True, files_written=["f1.txt"])

    # Checkout master again to do a second run
    subprocess.run(["git", "checkout", "master"], cwd=git_repo, check=True, capture_output=True)

    meta2 = preflight_and_start_run(workspace_dir=git_repo, goal="Second run")
    (git_repo / "f2.txt").write_text("2")
    finalize_run(meta2, success=True, files_written=["f2.txt"])

    # Undo without specifying run_id should undo meta2 (the latest run)
    undo_res = undo_run(workspace_dir=git_repo, run_id=None, confirm=False)
    assert undo_res["status"] == "SUCCESS"
    assert undo_res["run_id"] == meta2.run_id
    assert not (git_repo / "f2.txt").exists()


def test_undo_confirmation_cancelled(git_repo: Path, temp_runs_dir: Path):
    """If user declines undo confirmation prompt, the run branch is not touched."""
    meta = preflight_and_start_run(workspace_dir=git_repo, goal="Run to cancel undo")
    (git_repo / "keep_me.txt").write_text("keep me")
    finalize_run(meta, success=True, files_written=["keep_me.txt"])

    # interactive_confirm returns False
    undo_res = undo_run(
        workspace_dir=git_repo,
        run_id=meta.run_id,
        confirm=True,
        interactive_confirm=lambda prompt, diff: False,
    )
    assert undo_res["status"] == "CANCELLED"
    assert branch_exists(git_repo, meta.run_branch)
    assert (git_repo / "keep_me.txt").exists()


def test_list_runs_filtering_and_provenance(tmp_path: Path, temp_runs_dir: Path):
    """Verify list_runs correctly filters by workspace directory and sorts by created_at."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    init_git_repo(ws1)
    init_git_repo(ws2)

    m1 = preflight_and_start_run(workspace_dir=ws1, goal="WS1 run")
    finalize_run(m1, success=True)

    m2 = preflight_and_start_run(workspace_dir=ws2, goal="WS2 run")
    finalize_run(m2, success=True)

    ws1_runs = list_runs(workspace_dir=ws1)
    assert len(ws1_runs) == 1
    assert ws1_runs[0].run_id == m1.run_id

    all_runs = list_runs()
    assert len(all_runs) >= 2
    assert all_runs[0].created_at >= all_runs[1].created_at
