"""Git checkpoint, safe rollback, and run provenance tracker for OctoFlow.

Guarantees that every live run in a git repository starts from a recorded checkpoint,
runs on an isolated octoflow/run-<id> branch, commits all generated changes (or WIP on failure),
and can be cleanly and safely undone in one command without risking user data.
"""

import json
import os
import subprocess
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from octoflow.logging_config import get_logger

logger = get_logger("checkpoint")


def get_runs_dir() -> Path:
    """Return the base directory for storing run provenance metadata."""
    override = os.environ.get("OCTOFLOW_RUNS_DIR")
    if override:
        base = Path(override).resolve()
    else:
        base = Path.home() / ".octoflow" / "runs"
    base.mkdir(parents=True, exist_ok=True)
    return base


class RunMetadata(BaseModel):
    """Metadata describing a single OctoFlow execution run and its git provenance."""

    run_id: str
    goal: str
    mode: str = "software_dev"
    model_provider: str = "mock"
    created_at: float = Field(default_factory=time.time)
    workspace_dir: str
    is_git: bool = True
    original_branch: str | None = None
    original_head: str | None = None
    run_branch: str | None = None
    stash_hash: str | None = None
    status: str = "INITIALIZED"  # INITIALIZED, RUNNING, COMPLETED, WIP, FAILED, UNDONE, NO_CHANGES
    commit_hash: str | None = None
    files_written: list[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Low-Level Git Operations (Safe, Local Only, Never Destructive to User Branches)
# -----------------------------------------------------------------------------


def run_git_cmd(
    args: list[str],
    cwd: str | Path,
    check: bool = False,
    capture: bool = True,
) -> subprocess.CompletedProcess:
    """Execute a git plumbing command safely inside the given workspace directory."""
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    env.setdefault("GIT_AUTHOR_NAME", "OctoFlow Swarm")
    env.setdefault("GIT_AUTHOR_EMAIL", "swarm@octoflow.dev")
    env.setdefault("GIT_COMMITTER_NAME", "OctoFlow Swarm")
    env.setdefault("GIT_COMMITTER_EMAIL", "swarm@octoflow.dev")
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            check=check,
            capture_output=capture,
            text=True,
            env=env,
        )
        return res
    except Exception as e:
        logger.debug("Git command git %s failed in %s: %s", " ".join(args), cwd, e)
        raise


def is_git_repo(workspace: str | Path) -> bool:
    """Check if the target directory is inside an active git working tree."""
    ws = Path(workspace)
    if not ws.exists():
        return False
    res = run_git_cmd(["rev-parse", "--is-inside-work-tree"], cwd=ws)
    return res.returncode == 0 and res.stdout.strip().lower() == "true"


def get_git_root(workspace: str | Path) -> Path | None:
    """Return the root path of the git repository."""
    res = run_git_cmd(["rev-parse", "--show-toplevel"], cwd=workspace)
    if res.returncode == 0 and res.stdout.strip():
        return Path(res.stdout.strip()).resolve()
    return None


def get_current_head(workspace: str | Path) -> str | None:
    """Return the full 40-character commit hash of HEAD."""
    res = run_git_cmd(["rev-parse", "HEAD"], cwd=workspace)
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return None


def get_current_branch(workspace: str | Path) -> str:
    """Return the name of the current git branch, or HEAD commit if detached."""
    res = run_git_cmd(["symbolic-ref", "--short", "HEAD"], cwd=workspace)
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    head = get_current_head(workspace)
    return head or "HEAD"


def is_working_tree_clean(workspace: str | Path) -> bool:
    """Check if the working tree has no staged, unstaged, or untracked changes."""
    res = run_git_cmd(["status", "--porcelain"], cwd=workspace)
    return res.returncode == 0 and len(res.stdout.strip()) == 0


def create_stash_snapshot(workspace: str | Path) -> str | None:
    """Create a stash-like snapshot of dirty changes without modifying the working tree.

    Uses 'git stash create' which writes a stash commit object and prints its hash
    without updating refs/stash. Stages untracked files temporarily so untracked user files
    are preserved, creates the stash commit, and immediately resets the index.
    """
    ws = Path(workspace)
    status = run_git_cmd(["status", "--porcelain"], cwd=ws)
    if not status.stdout.strip():
        return None
    # Temporarily stage changes so git stash create captures untracked user files as well
    run_git_cmd(["add", "-A"], cwd=ws)
    res = run_git_cmd(["stash", "create"], cwd=ws)
    stash_hash = res.stdout.strip() if res.returncode == 0 and res.stdout.strip() else None
    run_git_cmd(["reset"], cwd=ws)
    return stash_hash


def init_git_repo(workspace: str | Path) -> bool:
    """Initialize a git repository in workspace. Ensures at least one commit exists."""
    ws = Path(workspace)
    res = run_git_cmd(["init"], cwd=ws)
    if res.returncode != 0:
        return False
    # If repo has no commits, create an initial empty commit so HEAD and branches exist
    head = get_current_head(ws)
    if not head:
        run_git_cmd(
            ["commit", "--allow-empty", "-m", "chore: initial repository structure"], cwd=ws
        )
    return True


def branch_exists(workspace: str | Path, branch_name: str) -> bool:
    """Check if a specific branch ref exists in the repository."""
    res = run_git_cmd(["rev-parse", "--verify", f"refs/heads/{branch_name}"], cwd=workspace)
    return res.returncode == 0


def get_diff_summary(workspace: str | Path, from_ref: str, to_ref: str | None = None) -> str:
    """Return a human-readable stat summary of changes between two git refs."""
    range_spec = f"{from_ref}..{to_ref}" if to_ref else from_ref
    res = run_git_cmd(["diff", "--stat", range_spec], cwd=workspace)
    if res.returncode == 0:
        return res.stdout.strip()
    return ""


# -----------------------------------------------------------------------------
# Metadata Persistence
# -----------------------------------------------------------------------------


def save_run_metadata(meta: RunMetadata) -> Path:
    """Save run metadata to ~/.octoflow/runs/<run_id>/meta.json with mode 0600."""
    runs_dir = get_runs_dir()
    runs_dir.mkdir(parents=True, exist_ok=True)
    try:
        runs_dir.chmod(0o700)
    except OSError:
        pass

    run_dir = runs_dir / meta.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        run_dir.chmod(0o700)
    except OSError:
        pass

    meta_file = run_dir / "meta.json"
    meta_file.write_text(json.dumps(meta.model_dump(), indent=2), encoding="utf-8")
    try:
        meta_file.chmod(0o600)
    except OSError:
        pass

    # Record as latest run for this workspace
    latest_file = runs_dir / "latest_run_id"
    latest_file.write_text(meta.run_id, encoding="utf-8")
    try:
        latest_file.chmod(0o600)
    except OSError:
        pass
    return meta_file


def load_run_metadata(run_id: str) -> RunMetadata | None:
    """Load run metadata from ~/.octoflow/runs/<run_id>/meta.json."""
    meta_file = get_runs_dir() / run_id / "meta.json"
    if not meta_file.exists():
        return None
    try:
        raw = json.loads(meta_file.read_text(encoding="utf-8"))
        return RunMetadata.model_validate(raw)
    except Exception as e:
        logger.warning("Failed to parse metadata from %s: %s", meta_file, e)
        return None


def get_latest_run_metadata(workspace: str | Path | None = None) -> RunMetadata | None:
    """Retrieve metadata for the most recent run, optionally filtered by workspace."""
    runs = list_runs(workspace_dir=workspace, limit=1)
    return runs[0] if runs else None


def list_runs(workspace_dir: str | Path | None = None, limit: int = 20) -> list[RunMetadata]:
    """List recent runs in descending order of creation time."""
    runs_dir = get_runs_dir()
    if not runs_dir.exists():
        return []

    target_ws = str(Path(workspace_dir).resolve()) if workspace_dir else None
    metas: list[RunMetadata] = []

    for child in runs_dir.iterdir():
        if child.is_dir() and (child / "meta.json").exists():
            meta = load_run_metadata(child.name)
            if meta:
                if target_ws:
                    try:
                        m_ws = str(Path(meta.workspace_dir).resolve())
                        if m_ws != target_ws:
                            continue
                    except Exception:
                        pass
                metas.append(meta)

    metas.sort(key=lambda m: m.created_at, reverse=True)
    return metas[:limit]


# -----------------------------------------------------------------------------
# Pre-Flight, Checkpoint Creation & Run Finalization
# -----------------------------------------------------------------------------


def preflight_and_start_run(
    workspace_dir: str | Path,
    goal: str,
    mode: str = "software_dev",
    model: str = "mock",
    dry_run: bool = False,
    allow_dirty: bool = False,
    init_git: bool = False,
    no_checkpoint: bool = False,
    interactive: bool = False,
    interactive_confirm: Callable[[str], bool] | None = None,
) -> RunMetadata | None:
    """Perform pre-flight verification, record checkpoint, and create isolated run branch.

    Dry runs skip checkpointing and return None.
    In git workspaces, verifies clean tree (or captures stash snapshot with --allow-dirty)
    and switches to branch octoflow/run-<id>.
    In non-git workspaces, offers git init or permits --no-checkpoint.
    """
    if dry_run:
        return None

    ws = Path(workspace_dir).resolve()
    if not ws.exists():
        ws.mkdir(parents=True, exist_ok=True)

    # 1. Non-git workspace handling
    if not is_git_repo(ws):
        if no_checkpoint:
            run_id = f"{int(time.time())}-{uuid.uuid4().hex[:6]}"
            meta = RunMetadata(
                run_id=run_id,
                goal=goal,
                mode=mode,
                model_provider=model,
                workspace_dir=str(ws),
                is_git=False,
                status="RUNNING",
            )
            save_run_metadata(meta)
            return meta

        if init_git:
            init_git_repo(ws)
        else:
            if interactive and interactive_confirm:
                wants_git = interactive_confirm(
                    "Workspace is not a git repository. Initialize git repository for safe rollback? [y/N]"
                )
                if wants_git:
                    init_git_repo(ws)
                else:
                    wants_no_chk = interactive_confirm(
                        "Proceed without checkpoint rollback protection? [y/N]"
                    )
                    if wants_no_chk:
                        run_id = f"{int(time.time())}-{uuid.uuid4().hex[:6]}"
                        meta = RunMetadata(
                            run_id=run_id,
                            goal=goal,
                            mode=mode,
                            model_provider=model,
                            workspace_dir=str(ws),
                            is_git=False,
                            status="RUNNING",
                        )
                        save_run_metadata(meta)
                        return meta
                    raise ValueError(
                        "Workspace is not a git repository. Pass --init-git to initialize git for checkpoint safety, or --no-checkpoint to run without git versioning."
                    )
            else:
                raise ValueError(
                    "Workspace is not a git repository. Pass --init-git to initialize git for checkpoint safety, or --no-checkpoint to run without git versioning."
                )

    # 2. Git repo pre-flight: require clean tree or --allow-dirty
    stash_hash = None
    if not is_working_tree_clean(ws):
        if allow_dirty:
            stash_hash = create_stash_snapshot(ws)
            logger.info("Recorded stash snapshot of dirty working tree: %s", stash_hash)
        else:
            raise ValueError(
                "Working tree has uncommitted changes. Please commit or stash your changes before running OctoFlow, or pass --allow-dirty to snapshot uncommitted changes and proceed."
            )

    # 3. Create run-id and run branch
    run_id = f"{int(time.time())}-{uuid.uuid4().hex[:6]}"
    run_branch = f"octoflow/run-{run_id}"

    if branch_exists(ws, run_branch):
        raise ValueError(
            f"Run branch '{run_branch}' already exists. Aborting to prevent branch collision."
        )

    orig_head = get_current_head(ws)
    orig_branch = get_current_branch(ws)

    # 4. Switch to new run branch
    checkout_res = run_git_cmd(["checkout", "-b", run_branch], cwd=ws)
    if checkout_res.returncode != 0:
        raise RuntimeError(
            f"Failed to create run branch '{run_branch}': {checkout_res.stderr.strip()}"
        )

    # 5. Record metadata
    meta = RunMetadata(
        run_id=run_id,
        goal=goal,
        mode=mode,
        model_provider=model,
        created_at=time.time(),
        workspace_dir=str(ws),
        is_git=True,
        original_branch=orig_branch,
        original_head=orig_head,
        run_branch=run_branch,
        stash_hash=stash_hash,
        status="RUNNING",
    )
    save_run_metadata(meta)
    return meta


def finalize_run(
    meta: RunMetadata | None,
    success: bool,
    files_written: list[str] | None = None,
    goal: str | None = None,
) -> RunMetadata | None:
    """Commit generated workspace changes at the end of a run (or as WIP if failed).

    Does not touch branches if meta is None or not in a git repository.
    """
    if meta is None or not meta.is_git:
        return meta

    ws = Path(meta.workspace_dir)
    if not ws.exists() or not is_git_repo(ws):
        return meta

    if files_written:
        meta.files_written = list(files_written)

    if not is_working_tree_clean(ws):
        run_git_cmd(["add", "-A"], cwd=ws)
        clean_goal = (goal or meta.goal).replace("\n", " ").strip()
        summary = clean_goal[:50] + ("..." if len(clean_goal) > 50 else "")
        if success:
            commit_msg = f"octoflow: {summary} ({meta.run_id})"
            meta.status = "COMPLETED"
        else:
            commit_msg = f"octoflow: [wip] {summary} ({meta.run_id})"
            meta.status = "WIP"

        res = run_git_cmd(["commit", "-m", commit_msg], cwd=ws)
        if res.returncode == 0:
            meta.commit_hash = get_current_head(ws)
    else:
        meta.status = "COMPLETED" if success else "FAILED"

    save_run_metadata(meta)
    return meta


# -----------------------------------------------------------------------------
# Undo / Rollback
# -----------------------------------------------------------------------------


def undo_run(
    workspace_dir: str | Path,
    run_id: str | None = None,
    confirm: bool = True,
    interactive_confirm: Callable[[str, str], bool] | None = None,
) -> dict[str, Any]:
    """Undo an OctoFlow run by checking out the original branch and deleting the run branch.

    SAFETY CONSTRAINTS:
    - Only deletes branches matching 'octoflow/run-*'.
    - Only deletes branches confirmed to be created by OctoFlow via meta.json.
    - Never touches unrelated branches.
    - Never force-pushes.
    - Never runs 'git clean' on user files.
    - Restores stashed dirty changes if an allow-dirty snapshot was recorded.
    """
    ws = Path(workspace_dir).resolve()
    if not is_git_repo(ws):
        raise ValueError(f"Workspace '{ws}' is not a git repository.")

    # 1. Resolve run metadata
    if run_id:
        meta = load_run_metadata(run_id)
        if not meta:
            raise ValueError(f"Run '{run_id}' not found in OctoFlow run ledger.")
    else:
        meta = get_latest_run_metadata(workspace=ws)
        if not meta:
            raise ValueError("No prior OctoFlow runs found to undo for this workspace.")

    if not meta.is_git:
        raise ValueError(
            f"Run '{meta.run_id}' was executed without git checkpointing and cannot be undone via git."
        )

    # 2. Strict ownership verification
    run_branch = meta.run_branch
    if not run_branch or not run_branch.startswith("octoflow/run-"):
        raise ValueError(f"Refusing to undo: branch '{run_branch}' was not created by OctoFlow.")

    if not branch_exists(ws, run_branch):
        raise ValueError(f"Run branch '{run_branch}' does not exist in repository.")

    if not meta.original_branch:
        raise ValueError("Run metadata is missing original branch information.")

    # 3. Compute diff summary
    diff_stat = get_diff_summary(ws, meta.original_head or meta.original_branch, run_branch)

    # 4. Ask for confirmation if requested
    if confirm and interactive_confirm:
        prompt_text = (
            f"Undo run '{meta.run_id}' on branch '{run_branch}'?\n"
            f"Objective: {meta.goal[:60]}\n"
            f"Original Branch: {meta.original_branch}\n"
        )
        if not interactive_confirm(prompt_text, diff_stat):
            return {
                "status": "CANCELLED",
                "run_id": meta.run_id,
                "message": "Undo cancelled by user.",
            }

    # 5. Switch back to original branch
    checkout_res = run_git_cmd(["checkout", meta.original_branch], cwd=ws)
    if checkout_res.returncode != 0:
        raise RuntimeError(
            f"Failed to checkout original branch '{meta.original_branch}': {checkout_res.stderr.strip()}"
        )

    # 6. Delete the run branch safely (-D only on octoflow/run-* owned by metadata)
    del_res = run_git_cmd(["branch", "-D", run_branch], cwd=ws)
    if del_res.returncode != 0:
        raise RuntimeError(f"Failed to delete run branch '{run_branch}': {del_res.stderr.strip()}")

    # 7. Restore stashed dirty changes if snapshot exists
    restored_stash = False
    if meta.stash_hash:
        stash_res = run_git_cmd(["stash", "apply", meta.stash_hash], cwd=ws)
        restored_stash = stash_res.returncode == 0

    # 8. Mark metadata as undone
    meta.status = "UNDONE"
    save_run_metadata(meta)

    return {
        "status": "SUCCESS",
        "run_id": meta.run_id,
        "original_branch": meta.original_branch,
        "deleted_branch": run_branch,
        "restored_stash": restored_stash,
        "diff_stat": diff_stat,
    }
