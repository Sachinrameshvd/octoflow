"""Doctor CLI command for system environment and dependency diagnostics."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.table import Table

from octoflow.config import get_octoflow_dir, load_secure_config
from octoflow.themes import load_saved_theme

console = Console()


def collect_doctor_diagnostics(workspace: str = ".", fix: bool = False) -> dict[str, Any]:
    """Inspect runtime environment, neural assets, git safety, and provider endpoints."""
    ws = Path(workspace).resolve()

    subsystems: list[dict[str, str]] = []
    all_passed = True

    # 1. Python Runtime
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):  # noqa: UP036 - intentional runtime diagnostic check for CLI users
        subsystems.append(
            {
                "subsystem": "Python Runtime",
                "status": "PASS",
                "details": f"v{py_ver} (64-bit {sys.platform})",
            }
        )
    else:
        subsystems.append(
            {
                "subsystem": "Python Runtime",
                "status": "FAIL",
                "details": f"v{py_ver} (Requires Python >= 3.10)",
            }
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
        subsystems.append(
            {
                "subsystem": "Git Repository",
                "status": "PASS",
                "details": f"Root: {ws.name} | Branch: {git_branch}",
            }
        )
    else:
        subsystems.append(
            {
                "subsystem": "Git Repository",
                "status": "WARN",
                "details": "Not inside a git worktree. /rollback requires git.",
            }
        )
        if fix:
            try:
                subprocess.run(["git", "init"], cwd=str(ws), capture_output=True)
            except Exception:
                pass

    # 3. Precompiled 3D Visualizer Assets
    dist_dir = Path(__file__).parent.parent / "dist"
    has_dist = (dist_dir / "index.html").exists() and (dist_dir / "assets").exists()
    if has_dist:
        subsystems.append(
            {
                "subsystem": "3D Visualizer Dist",
                "status": "PASS",
                "details": f"Bundled package assets verified ({dist_dir})",
            }
        )
    else:
        subsystems.append(
            {
                "subsystem": "3D Visualizer Dist",
                "status": "FAIL",
                "details": "Missing octoflow/dist bundle. Zero-node visualizer unavailable.",
            }
        )
        all_passed = False

    # 4. Port 8088 Visualizer Bridge
    port_status = "Available"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        in_use = s.connect_ex(("127.0.0.1", 8088)) == 0
        if in_use:
            port_status = "Active / In Use (Bridge Live)"
    subsystems.append(
        {
            "subsystem": "Telemetry Port 8088",
            "status": "INFO",
            "details": port_status,
        }
    )

    # 5. LLM API Providers & Credentials
    cfg_file = get_octoflow_dir() / "config.json"
    saved_cfg = load_secure_config(cfg_file) if cfg_file.exists() else {}

    has_anthropic = bool(saved_cfg.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(saved_cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY"))

    subsystems.append(
        {
            "subsystem": "Anthropic API",
            "status": "READY" if has_anthropic else "UNSET",
            "details": "Claude 3.7 Sonnet / Claude 3.5 Haiku"
            if has_anthropic
            else "Not configured",
        }
    )
    subsystems.append(
        {
            "subsystem": "OpenAI API",
            "status": "READY" if has_openai else "UNSET",
            "details": "o3-mini / GPT-4o-mini" if has_openai else "Not configured",
        }
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
        subsystems.append(
            {
                "subsystem": "Local Ollama",
                "status": "ONLINE",
                "details": f"http://localhost:11434 | {models_str}",
            }
        )
    else:
        subsystems.append(
            {
                "subsystem": "Local Ollama",
                "status": "OFFLINE",
                "details": "No local Ollama daemon found (optional offline LLM)",
            }
        )

    # 7. Vertical Lobe Memory
    mem_file = Path.home() / ".octoflow" / "vertical_lobe.json"
    if mem_file.exists():
        try:
            mem_data = json.loads(mem_file.read_text(encoding="utf-8"))
            count = len(mem_data.get("entries", []))
            subsystems.append(
                {
                    "subsystem": "Vertical Lobe LTP",
                    "status": "PASS",
                    "details": f"{count} Hebbian heuristics stored",
                }
            )
        except Exception:
            subsystems.append(
                {
                    "subsystem": "Vertical Lobe LTP",
                    "status": "WARN",
                    "details": "Unreadable memory file",
                }
            )
    else:
        subsystems.append(
            {
                "subsystem": "Vertical Lobe LTP",
                "status": "INITIAL",
                "details": "Will initialize upon first error consolidation",
            }
        )

    # 8. ML Subsystem & Encoder Backend
    from octoflow.encoder import _get_configured_backend, _is_torch_available, get_encoder

    has_torch = _is_torch_available()
    cfg_backend = _get_configured_backend()

    if cfg_backend == "torch" and not has_torch:
        subsystems.append(
            {
                "subsystem": "ML / Encoder Backend",
                "status": "FAIL",
                "details": "Configured backend='torch' but [ml] extra is not installed.",
            }
        )
        all_passed = False
    else:
        active_encoder = get_encoder(backend="auto")
        ml_status = (
            "installed" if has_torch else "not installed (optional: pip install 'octoflow[ml]')"
        )
        subsystems.append(
            {
                "subsystem": "ML / Encoder Backend",
                "status": "PASS",
                "details": f"Active: {active_encoder.backend} (default: numpy) | [ml] extra: {ml_status}",
            }
        )

    return {
        "overall_status": "PASS" if all_passed else "FAIL",
        "all_passed": all_passed,
        "subsystems": subsystems,
    }


def run_doctor(
    workspace: str = ".", fix: bool = False, json_output: bool = False
) -> dict[str, Any]:
    """Run system environment and dependency diagnostics (like 'ruflo doctor')."""
    theme = load_saved_theme()
    result_payload = collect_doctor_diagnostics(workspace=workspace, fix=fix)

    if json_output:
        sys.stdout.write(json.dumps(result_payload, indent=2) + "\n")
        sys.stdout.flush()
        return result_payload

    # Terminal Rich Table output
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

    for item in result_payload["subsystems"]:
        st = item["status"]
        if st in ("PASS", "READY", "ONLINE"):
            badge = f"[{theme.rich_success}]● {st}[/{theme.rich_success}]"
        elif st in ("FAIL",):
            badge = f"[{theme.rich_danger}]✖ {st}[/{theme.rich_danger}]"
        elif st in ("WARN", "INITIAL"):
            badge = f"[{theme.rich_warning}]▲ {st}[/{theme.rich_warning}]"
        else:
            badge = f"[{theme.rich_secondary}]● {st}[/{theme.rich_secondary}]"
        doc_table.add_row(item["subsystem"], badge, item["details"])

    console.print(doc_table)

    if result_payload["all_passed"]:
        console.print(
            f"\n[{theme.rich_success}]✔ All critical subsystems nominal. Cephalopod Swarm is deployment-ready![/{theme.rich_success}]\n"
        )
    else:
        console.print(
            f"\n[{theme.rich_warning}]▲ Action items detected above. Run [bold]octos setup[/bold] to configure credentials.[/{theme.rich_warning}]\n"
        )

    return result_payload


def doctor_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    fix: bool = typer.Option(
        False, "--fix", help="Automatically repair missing directories and initialize git if needed"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output diagnostic report as structured JSON"
    ),
):
    """Run OctoFlow environment and provider diagnostics (like 'ruflo doctor')."""
    run_doctor(workspace=workspace, fix=fix, json_output=json_output)


def bugreport_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
):
    """Generate a redacted environment summary to paste into GitHub issues."""
    import platform

    from octoflow import __version__
    from octoflow.provider import redact_secrets
    from octoflow.redactor import redact_outbound_text

    ws = Path(workspace).resolve()

    # 1. System & Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

    git_info = "Not inside a git worktree"
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            timeout=1,
        )
        if r.returncode == 0 and r.stdout.strip():
            commit = r.stdout.strip()
            b = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(ws),
                capture_output=True,
                text=True,
                timeout=1,
            )
            branch = b.stdout.strip() or "detached"
            git_info = f"branch '{branch}' @ {commit}"
    except Exception:
        pass

    # 2. Run Diagnostics silently
    diag_res = collect_doctor_diagnostics(workspace=workspace, fix=False)

    # 3. Collect and Mask Settings
    cfg_file = get_octoflow_dir() / "config.json"
    saved_cfg = load_secure_config(cfg_file) if cfg_file.exists() else {}
    masked_cfg: dict[str, Any] = {}
    for k, v in saved_cfg.items():
        k_lower = str(k).lower()
        if any(
            term in k_lower for term in ("key", "secret", "token", "password", "auth", "canary")
        ):
            masked_cfg[k] = "[REDACTED_CREDENTIAL]"
        else:
            masked_cfg[k] = redact_secrets(str(v)) if isinstance(v, str) else v

    # 4. Collect and Mask Relevant Environment Variables
    masked_env: dict[str, str] = {}
    relevant_prefixes = (
        "OCTOFLOW_",
        "ANTHROPIC_",
        "OPENAI_",
        "GEMINI_",
        "GROK_",
        "DEEPSEEK_",
        "OLLAMA_",
        "CANARY_",
    )
    for env_k, env_v in sorted(os.environ.items()):
        if any(env_k.startswith(p) for p in relevant_prefixes):
            k_lower = env_k.lower()
            if any(
                term in k_lower for term in ("key", "secret", "token", "password", "auth", "canary")
            ):
                masked_env[env_k] = "[REDACTED_CREDENTIAL]"
            else:
                clean_val, _ = redact_outbound_text(redact_secrets(env_v))
                masked_env[env_k] = clean_val

    # 5. Collect and Redact Last 50 Log Lines
    log_candidates = [
        Path.home() / ".octoflow" / "logs" / "octoflow.log",
        Path.home() / ".octoflow" / "octoflow.log",
        Path.home() / ".octoflow" / "last_error.log",
        Path.home() / ".octoflow" / "logs" / "dev_telemetry.log",
    ]
    log_lines: list[str] = []
    for cand in log_candidates:
        if cand.exists() and cand.is_file():
            try:
                raw_lines = cand.read_text(encoding="utf-8").splitlines()
                if raw_lines:
                    log_lines = raw_lines[-50:]
                    break
            except Exception:
                pass

    redacted_logs: list[str] = []
    for log_line in log_lines:
        c1, _ = redact_outbound_text(redact_secrets(log_line))
        redacted_logs.append(c1)

    log_excerpt = "\n".join(redacted_logs) if redacted_logs else "(No local log file found)"

    # Format Markdown
    diag_lines = []
    for sub in diag_res.get("subsystems", []):
        diag_lines.append(f"- **{sub['subsystem']}:** {sub['status']} ({sub['details']})")
    diagnostics_md = "\n".join(diag_lines)

    report_md = f"""### OctoFlow Bug Report Environment Summary

#### System & Environment
- **OctoFlow Version:** {__version__}
- **Python Version:** {py_ver} ({sys.executable})
- **Operating System:** {os_info}
- **Git State:** {git_info}
- **Doctor Status:** {diag_res.get("overall_status", "UNKNOWN")}

#### Diagnostics Findings
{diagnostics_md}

#### Config Settings (Masked)
```json
{json.dumps(masked_cfg, indent=2)}
```

#### Environment Variables (Masked)
```json
{json.dumps(masked_env, indent=2)}
```

#### Recent Log Excerpt (Last 50 Lines, Redacted)
```text
{log_excerpt}
```
"""
    # Final defense-in-depth scrubbing
    final_output, _ = redact_outbound_text(redact_secrets(report_md))
    console.print(final_output)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register doctor and bugreport commands with Typer apps."""
    app.command("doctor")(doctor_cli_cmd)
    octos_app.command("doctor")(doctor_cli_cmd)
    app.command("bugreport")(bugreport_cli_cmd)
    octos_app.command("bugreport")(bugreport_cli_cmd)
