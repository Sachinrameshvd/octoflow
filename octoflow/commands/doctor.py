"""Doctor CLI command for system environment and dependency diagnostics."""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

from octoflow.config import get_octoflow_dir, load_secure_config
from octoflow.themes import load_saved_theme

console = Console()


def run_doctor(workspace: str = ".", fix: bool = False):
    """Run system environment and dependency diagnostics (like 'ruflo doctor')."""
    theme = load_saved_theme()
    ws = Path(workspace).resolve()

    console.print(
        f"\n[{theme.rich_primary}]◈ OctoFlow Diagnostic Doctor v1.0.0[/{theme.rich_primary}]"
    )
    console.print(
        "[dim]Inspecting runtime environment, neural assets, git safety, and provider endpoints...[/dim]\n"
    )

    doc_table = Table(
        title="System & Neural Swarm Health", border_style=theme.rich_border, expand=True
    )
    doc_table.add_column("Subsystem", style=theme.rich_primary, width=22)
    doc_table.add_column("Status", width=12)
    doc_table.add_column("Diagnostics & Details", style="white")

    all_passed = True

    # 1. Python Runtime
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        doc_table.add_row(
            "Python Runtime",
            f"[{theme.rich_success}]● PASS[/{theme.rich_success}]",
            f"v{py_ver} (64-bit {sys.platform})",
        )
    else:
        doc_table.add_row(
            "Python Runtime",
            f"[{theme.rich_danger}]✖ FAIL[/{theme.rich_danger}]",
            f"v{py_ver} (Requires Python >= 3.10)",
        )
        all_passed = False

    # 2. Workspace & Git Safety
    is_git = False
    git_branch = "none"
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            timeout=1,
        )
        if r.returncode == 0 and "true" in r.stdout:
            is_git = True
            b_r = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(ws),
                capture_output=True,
                text=True,
                timeout=1,
            )
            git_branch = b_r.stdout.strip()
    except Exception:
        pass

    if is_git:
        branch_style = (
            theme.rich_warning if git_branch in ["main", "master"] else theme.rich_success
        )
        doc_table.add_row(
            "Git Repository",
            f"[{theme.rich_success}]● PASS[/{theme.rich_success}]",
            f"Root: {ws.name} | Branch: [{branch_style}]{git_branch}[/{branch_style}]",
        )
    else:
        doc_table.add_row(
            "Git Repository",
            f"[{theme.rich_warning}]▲ WARN[/{theme.rich_warning}]",
            "Not inside a git worktree. /rollback requires git.",
        )
        if fix:
            try:
                subprocess.run(["git", "init"], cwd=str(ws), capture_output=True)
                console.print(
                    f"[{theme.rich_success}]✔ [doctor --fix] Initialized git repository in {ws}[/{theme.rich_success}]"
                )
            except Exception:
                pass

    # 3. Precompiled 3D Visualizer Assets
    dist_dir = Path(__file__).parent.parent / "dist"
    has_dist = (dist_dir / "index.html").exists() and (dist_dir / "assets").exists()
    if has_dist:
        doc_table.add_row(
            "3D Visualizer Dist",
            f"[{theme.rich_success}]● PASS[/{theme.rich_success}]",
            f"Bundled package assets verified ({dist_dir})",
        )
    else:
        doc_table.add_row(
            "3D Visualizer Dist",
            f"[{theme.rich_danger}]✖ FAIL[/{theme.rich_danger}]",
            "Missing octoflow/dist bundle. Zero-node visualizer unavailable.",
        )
        all_passed = False

    # 4. Port 8088 Visualizer Bridge
    port_status = "Available"
    port_color = theme.rich_success
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        in_use = s.connect_ex(("127.0.0.1", 8088)) == 0
        if in_use:
            port_status = "Active / In Use (Bridge Live)"
            port_color = theme.rich_secondary
    doc_table.add_row("Telemetry Port 8088", f"[{port_color}]● INFO[/{port_color}]", port_status)

    # 5. LLM API Providers & Credentials
    cfg_file = get_octoflow_dir() / "config.json"
    saved_cfg = load_secure_config(cfg_file) if cfg_file.exists() else {}

    has_anthropic = bool(saved_cfg.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(saved_cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY"))

    ant_status = (
        f"[{theme.rich_success}]● READY[/{theme.rich_success}]"
        if has_anthropic
        else "[dim]○ UNSET[/dim]"
    )
    oai_status = (
        f"[{theme.rich_success}]● READY[/{theme.rich_success}]"
        if has_openai
        else "[dim]○ UNSET[/dim]"
    )
    doc_table.add_row(
        "Anthropic API",
        ant_status,
        "Claude 3.7 Sonnet / Claude 3.5 Haiku" if has_anthropic else "Not configured",
    )
    doc_table.add_row(
        "OpenAI API", oai_status, "o3-mini / GPT-4o-mini" if has_openai else "Not configured"
    )

    # 6. Local Ollama Daemon
    ollama_ok = False
    ollama_models = []
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=0.8)
        if resp.status_code == 200:
            ollama_ok = True
            data = resp.json()
            ollama_models = [m.get("name") for m in data.get("models", [])][:4]
    except Exception:
        pass

    if ollama_ok:
        models_str = (
            f"Models: {', '.join(ollama_models)}"
            if ollama_models
            else "Daemon online (no models pulled yet)"
        )
        doc_table.add_row(
            "Local Ollama",
            f"[{theme.rich_success}]● ONLINE[/{theme.rich_success}]",
            f"http://localhost:11434 | {models_str}",
        )
    else:
        doc_table.add_row(
            "Local Ollama",
            "[dim]○ OFFLINE[/dim]",
            "No local Ollama daemon found (optional offline LLM)",
        )

    # 7. Vertical Lobe Memory
    mem_file = Path.home() / ".octoflow" / "vertical_lobe.json"
    if mem_file.exists():
        try:
            mem_data = json.loads(mem_file.read_text(encoding="utf-8"))
            count = len(mem_data.get("entries", []))
            doc_table.add_row(
                "Vertical Lobe LTP",
                f"[{theme.rich_success}]● PASS[/{theme.rich_success}]",
                f"{count} Hebbian heuristics stored",
            )
        except Exception:
            doc_table.add_row(
                "Vertical Lobe LTP",
                f"[{theme.rich_warning}]▲ WARN[/{theme.rich_warning}]",
                "Unreadable memory file",
            )
    else:
        doc_table.add_row(
            "Vertical Lobe LTP",
            f"[{theme.rich_secondary}]● INITIAL[/{theme.rich_secondary}]",
            "Will initialize upon first error consolidation",
        )

    # 8. ML Subsystem & Encoder Backend
    from octoflow.encoder import _get_configured_backend, _is_torch_available, get_encoder

    has_torch = _is_torch_available()
    cfg_backend = _get_configured_backend()

    if cfg_backend == "torch" and not has_torch:
        doc_table.add_row(
            "ML / Encoder Backend",
            f"[{theme.rich_danger}]✖ FAIL[/{theme.rich_danger}]",
            r"Configured backend='torch' but \[ml] extra is not installed. (Hint: run 'pip install \"octoflow\[ml]\"')",
        )
        all_passed = False
    else:
        active_encoder = get_encoder(backend="auto")
        ml_status = (
            r"installed" if has_torch else r"not installed (optional: pip install 'octoflow\[ml\]')"
        )
        doc_table.add_row(
            "ML / Encoder Backend",
            f"[{theme.rich_success}]● PASS[/{theme.rich_success}]",
            f"Active: {active_encoder.backend} (default: numpy) | \\[ml\\] extra: {ml_status}",
        )

    console.print(doc_table)

    if all_passed:
        console.print(
            f"\n[{theme.rich_success}]✔ All critical subsystems nominal. Cephalopod Swarm is deployment-ready![/{theme.rich_success}]\n"
        )
    else:
        console.print(
            f"\n[{theme.rich_warning}]▲ Action items detected above. Run [bold]octos setup[/bold] to configure credentials.[/{theme.rich_warning}]\n"
        )


def doctor_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    fix: bool = typer.Option(
        False, "--fix", help="Automatically repair missing directories and initialize git if needed"
    ),
):
    """Run OctoFlow environment and provider diagnostics (like 'ruflo doctor')."""
    run_doctor(workspace=workspace, fix=fix)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register doctor command with Typer apps."""
    app.command("doctor")(doctor_cli_cmd)
    octos_app.command("doctor")(doctor_cli_cmd)
