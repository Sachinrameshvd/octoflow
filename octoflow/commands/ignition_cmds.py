"""CLI commands for inspecting running ignition services and terminating process groups."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from octoflow.ignition import list_active_ignitions, stop_ignition

console = Console()


def ps_cli_cmd(
    workspace: str | None = typer.Option(
        None, "--dir", "-d", help="Filter services by workspace directory"
    ),
):
    """List actively running Phase 4 ignition application & API servers."""
    ws = Path(workspace).resolve() if workspace else None
    active = list_active_ignitions(workspace_dir=ws)

    if not active:
        console.print("\n[dim]No active ignition services found.[/dim]\n")
        return

    table = Table(title="⚡ OctoFlow Active Ignition Services", border_style="cyan")
    table.add_column("Run ID", style="bold cyan", no_wrap=True)
    table.add_column("Service", style="bold", no_wrap=True)
    table.add_column("PID", style="dim", no_wrap=True)
    table.add_column("Port", style="green", no_wrap=True)
    table.add_column("Primary URL", style="bold cyan")
    table.add_column("Status", style="bold")
    table.add_column("Log File", style="dim")

    for item in active:
        run_id = item.get("run_id", "unknown")
        services = item.get("services", [])
        if not services:
            # Workspace without discrete sub-services
            table.add_row(
                run_id,
                item.get("service_type", "app"),
                ",".join(str(p) for p in item.get("pids", [])),
                str(item.get("frontend_port") or item.get("backend_port") or "-"),
                item.get("primary_url") or "-",
                item.get("status", "READY"),
                "-",
            )
        else:
            for s in services:
                status_color = "green" if s.get("status") in ("READY", "RUNNING") else "yellow"
                status_str = f"[{status_color}]{s.get('status', 'READY')}[/{status_color}]"
                table.add_row(
                    run_id,
                    s.get("name", "service"),
                    str(s.get("pid", "-")),
                    str(s.get("port", "-")),
                    s.get("url") or item.get("primary_url") or "-",
                    status_str,
                    Path(s.get("log_path", "")).name if s.get("log_path") else "-",
                )

    console.print("\n", table, "\n")


def stop_cli_cmd(
    run_id: str | None = typer.Argument(
        None, help="Specific run ID to stop (default: latest active run)"
    ),
    all_services: bool = typer.Option(
        False, "--all", "-a", help="Stop all running ignition services across all runs"
    ),
    workspace: str | None = typer.Option(
        None, "--dir", "-d", help="Target project workspace folder"
    ),
):
    """Stop active ignition application and API background servers."""
    ws = Path(workspace).resolve() if workspace else None
    stopped_pids = stop_ignition(run_id=run_id, stop_all=all_services, workspace_dir=ws)

    if stopped_pids:
        console.print(
            f"\n[bold green]✔ Successfully stopped {len(stopped_pids)} ignition process(es) (PIDs: {', '.join(str(p) for p in stopped_pids)}).[/bold green]\n"
        )
    else:
        target_desc = (
            "all runs" if all_services else (f"run '{run_id}'" if run_id else "latest run")
        )
        console.print(f"\n[dim]No running ignition processes found for {target_desc}.[/dim]\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register ps and stop commands with Typer applications."""
    app.command("ps")(ps_cli_cmd)
    app.command("stop")(stop_cli_cmd)
    octos_app.command("ps")(ps_cli_cmd)
    octos_app.command("stop")(stop_cli_cmd)
