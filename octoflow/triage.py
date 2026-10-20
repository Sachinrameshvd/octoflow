"""OctoFlow Interactive Terminal Patch Inspector & Diff Triage.

Allows developers to review, accept, discard, or stage 8-arm workspace modifications
on a file-by-file basis before committing, complete with AST validity verification.
"""

import ast
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from octoflow.config import SOFTWARE_DEV_ROSTER
from octoflow.themes import get_theme


def get_workspace_diff_items(workspace_dir: str = ".") -> List[Dict[str, Any]]:
    """Retrieve list of modified files with diff content, responsible arm, and AST check."""
    ws = Path(workspace_dir).resolve()
    items: List[Dict[str, Any]] = []

    try:
        st_res = subprocess.run(["git", "status", "--porcelain"], cwd=str(ws), capture_output=True, text=True)
        if st_res.returncode != 0:
            return []

        for line in st_res.stdout.splitlines():
            if len(line) < 4:
                continue
            status_code = line[:2].strip()
            rel_file = line[3:].strip()
            full_path = ws / rel_file

            # Get diff
            diff_res = subprocess.run(["git", "diff", rel_file], cwd=str(ws), capture_output=True, text=True)
            diff_text = diff_res.stdout

            # If untracked file, create unified diff representation
            if not diff_text and full_path.exists():
                try:
                    f_content = full_path.read_text(encoding="utf-8")
                    diff_text = f"+++ b/{rel_file}\n" + "\n".join(f"+{l}" for l in f_content.splitlines()[:50])
                except Exception:
                    diff_text = f"+++ b/{rel_file} (binary or unreadable)"

            # Preflight AST check
            ast_valid = True
            ast_error = None
            if rel_file.endswith(".py") and full_path.exists():
                try:
                    ast.parse(full_path.read_text(encoding="utf-8"))
                except SyntaxError as e:
                    ast_valid = False
                    ast_error = f"L{e.lineno}: {e.msg}"
            elif rel_file.endswith(".json") and full_path.exists():
                try:
                    json.loads(full_path.read_text(encoding="utf-8"))
                except Exception as e:
                    ast_valid = False
                    ast_error = str(e)

            # Determine responsible arm
            arm_id = 2  # Default to backend logic
            arm_title = "Backend API"
            fn_lower = rel_file.lower()
            if any(k in fn_lower for k in ["arch", "config", "core", "main"]):
                arm_id = 0; arm_title = "System Architect"
            elif any(k in fn_lower for k in ["db", "model", "schema", "sql", "migration"]):
                arm_id = 1; arm_title = "Database & Schemas"
            elif any(k in fn_lower for k in ["ui", "view", "component", "css", "html", "jsx", "tsx"]):
                arm_id = 3; arm_title = "Frontend UI"
            elif any(k in fn_lower for k in ["state", "store", "cache", "context"]):
                arm_id = 4; arm_title = "State & Hooks"
            elif any(k in fn_lower for k in ["test", "spec", "qa"]):
                arm_id = 5; arm_title = "QA & Testing"
            elif any(k in fn_lower for k in ["auth", "security", "guard", "cert", "token"]):
                arm_id = 6; arm_title = "Security & Profiling"
            elif any(k in fn_lower for k in ["docker", "workflow", "action", "readme", "deploy"]):
                arm_id = 7; arm_title = "DevOps & Deploy"

            # Count added / removed lines
            added = len([l for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++")])
            removed = len([l for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---")])

            items.append({
                "file": rel_file,
                "status_code": status_code,
                "diff": diff_text,
                "arm_id": arm_id,
                "arm_title": arm_title,
                "ast_valid": ast_valid,
                "ast_error": ast_error,
                "lines_added": added,
                "lines_removed": removed,
            })
    except Exception:
        pass

    return items


def triage_workspace_diffs(
    workspace_dir: str = ".",
    interactive: bool = False,
    auto_approve: bool = False,
    console: Optional[Console] = None,
) -> Dict[str, Any]:
    """Triage uncommitted workspace diffs file-by-file with AST safety checks."""
    ws = Path(workspace_dir).resolve()
    c = console or Console()
    th = get_theme("tokyo_night")

    items = get_workspace_diff_items(str(ws))

    accepted: List[str] = []
    discarded: List[str] = []
    skipped: List[str] = []

    if not items:
        return {
            "total_files": 0,
            "accepted": [],
            "discarded": [],
            "skipped": [],
            "message": "Zero uncommitted changes in workspace.",
        }

    for item in items:
        f_name = item["file"]
        arm_title = item["arm_title"]
        ast_badge = "[bold green]✔ AST VALID[/]" if item["ast_valid"] else f"[bold red]✖ SYNTAX ERROR: {item['ast_error']}[/]"
        diff_stats = f"[green]+{item['lines_added']}[/] [red]-{item['lines_removed']}[/]"

        if not interactive or auto_approve:
            if item["ast_valid"]:
                subprocess.run(["git", "add", f_name], cwd=str(ws), capture_output=True)
                accepted.append(f_name)
            else:
                skipped.append(f_name)
            continue

        # Interactive Mode
        header_text = f"[bold white]{f_name}[/] • [cyan]{arm_title}[/] • {diff_stats} • {ast_badge}"
        c.print(f"\n[bold]{header_text}[/bold]")

        # Render first 25 lines of diff
        syntax_chunk = "\n".join(item["diff"].splitlines()[:25])
        if len(item["diff"].splitlines()) > 25:
            syntax_chunk += "\n... [truncated]"

        syntax = Syntax(syntax_chunk, "diff", theme="monokai", line_numbers=True)
        c.print(syntax)

        choice = c.input(f"[{th.rich_primary}]Action ([bold]y[/bold]=Accept & Stage, [bold]n[/bold]=Discard, [bold]s[/bold]=Skip, [bold]q[/bold]=Quit): [/{th.rich_primary}]").strip().lower()

        if choice in ["y", "yes", "a", "accept"]:
            subprocess.run(["git", "add", f_name], cwd=str(ws), capture_output=True)
            accepted.append(f_name)
            c.print(f"[{th.rich_success}]✔ Staged {f_name}[/{th.rich_success}]")
        elif choice in ["n", "no", "d", "discard"]:
            target_path = ws / f_name
            if target_path.exists():
                subprocess.run(["git", "checkout", "--", f_name], cwd=str(ws), capture_output=True)
                if target_path.exists():  # untracked
                    try:
                        target_path.unlink()
                    except Exception:
                        pass
            discarded.append(f_name)
            c.print(f"[{th.rich_warning}]▲ Discarded changes to {f_name}[/{th.rich_warning}]")
        elif choice in ["q", "quit", "exit"]:
            skipped.append(f_name)
            break
        else:
            skipped.append(f_name)
            c.print(f"[dim]Skipped {f_name}[/dim]")

    return {
        "total_files": len(items),
        "accepted": accepted,
        "discarded": discarded,
        "skipped": skipped,
        "message": f"Triage complete: {len(accepted)} accepted, {len(discarded)} discarded, {len(skipped)} skipped.",
    }
