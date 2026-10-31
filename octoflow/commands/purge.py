"""CLI command for safely purging OctoFlow global and workspace data."""

import os
import shutil
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from octoflow.config import get_octoflow_dir
from octoflow.themes import load_saved_theme

console = Console()


def get_dir_size(path: Path) -> int:
    """Calculate total size of file or directory in bytes."""
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = Path(root) / f
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total


def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def collect_purge_targets(
    workspace: Path,
    workspace_only: bool = False,
    global_only: bool = False,
) -> list[dict[str, Any]]:
    """Collect candidate paths for deletion with existence and size metadata."""
    targets = []

    # Global ~/.octoflow targets
    if not workspace_only:
        octo_dir = get_octoflow_dir()
        targets.append(
            {
                "category": "Global",
                "description": "Global Config, Logs, Runs, & Guilds",
                "path": octo_dir,
                "exists": octo_dir.exists(),
                "size": get_dir_size(octo_dir),
                "is_dir": True,
            }
        )

    # Workspace targets
    if not global_only:
        ws_dot_octo = workspace / ".octoflow"
        targets.append(
            {
                "category": "Workspace",
                "description": "Workspace Local Cache & History",
                "path": ws_dot_octo,
                "exists": ws_dot_octo.exists(),
                "size": get_dir_size(ws_dot_octo),
                "is_dir": True,
            }
        )
        ws_dot_mission = workspace / ".octoflow-mission"
        targets.append(
            {
                "category": "Workspace",
                "description": "Workspace Mission Checkpoints",
                "path": ws_dot_mission,
                "exists": ws_dot_mission.exists(),
                "size": get_dir_size(ws_dot_mission),
                "is_dir": True,
            }
        )

        # HTML reports & bench artifacts in workspace
        for pattern in (
            "octoflow-audit-*.html",
            "octoflow-report-*.html",
            "octoflow-bench-*.json",
            "octoflow-bench-*.md",
        ):
            for f in workspace.glob(pattern):
                targets.append(
                    {
                        "category": "Report",
                        "description": f"Generated Report: {f.name}",
                        "path": f,
                        "exists": True,
                        "size": get_dir_size(f),
                        "is_dir": False,
                    }
                )

    return targets


def purge_cli_cmd(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt and proceed immediately"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="List files and directories that would be deleted without deleting",
    ),
    workspace_only: bool = typer.Option(
        False, "--workspace-only", help="Purge only workspace artifacts (.octoflow, reports)"
    ),
    global_only: bool = typer.Option(
        False, "--global-only", help="Purge only global ~/.octoflow directory"
    ),
    workspace_dir: str = typer.Option(
        ".", "--dir", "-d", help="Workspace directory for local artifact cleanup"
    ),
) -> None:
    """Purge OctoFlow local storage: config, logs, run histories, memory, and reports."""
    ws = Path(workspace_dir).resolve()
    cur_theme = load_saved_theme()

    targets = collect_purge_targets(
        workspace=ws,
        workspace_only=workspace_only,
        global_only=global_only,
    )

    existing_targets = [t for t in targets if t["exists"]]
    total_bytes = sum(t["size"] for t in existing_targets)

    if not existing_targets:
        console.print(
            f"[{cur_theme.rich_success}]✔ No OctoFlow data found to purge.[/{cur_theme.rich_success}]"
        )
        return

    table = Table(
        title="◈ OctoFlow Data Purge Candidates",
        border_style=cur_theme.rich_border,
        header_style=f"bold {cur_theme.rich_accent}",
        expand=True,
    )
    table.add_column("Category", style="cyan", width=12)
    table.add_column("Description", style="white")
    table.add_column("Path", style="dim")
    table.add_column("Size", justify="right", style="yellow")

    for t in existing_targets:
        table.add_row(
            t["category"],
            t["description"],
            str(t["path"]),
            format_size(t["size"]),
        )

    console.print(table)
    console.print(
        f"\nTotal Reclaimable Space: [bold yellow]{format_size(total_bytes)}[/bold yellow] across {len(existing_targets)} targets.\n"
    )

    if dry_run:
        console.print(
            f"[{cur_theme.rich_accent}]◈ [DRY-RUN] No files were deleted.[/{cur_theme.rich_accent}]"
        )
        return

    if not yes:
        confirmed = Confirm.ask(
            "[bold red]▲ Permanently delete all listed OctoFlow data and configurations?[/bold red]",
            default=False,
        )
        if not confirmed:
            console.print("[dim]Purge cancelled by user.[/dim]")
            return

    # Execute deletion
    deleted_count = 0
    for t in existing_targets:
        p: Path = t["path"]
        try:
            if t["is_dir"] and p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.is_file():
                p.unlink(missing_ok=True)
            deleted_count += 1
        except Exception as e:
            console.print(f"[red]Failed to remove {p}: {e}[/red]")

    console.print(
        f"\n[{cur_theme.rich_success}]✔ Successfully purged {deleted_count} targets. Reclaimed {format_size(total_bytes)}.[/{cur_theme.rich_success}]"
    )


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register purge command with Typer CLI apps."""
    app.command("purge")(purge_cli_cmd)
    octos_app.command("purge")(purge_cli_cmd)

