"""Monorepo CLI command for scanning and partitioning monorepo packages."""

import typer
from rich.console import Console
from rich.table import Table
from octoflow.themes import load_saved_theme

console = Console()


def monorepo_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
):
    """Scan and partition monorepo packages to specialist 8-arm roles."""
    from octoflow.monorepo import scan_monorepo_topology
    theme = load_saved_theme()
    topo = scan_monorepo_topology(workspace)
    t = Table(title="Monorepo Package & Swarm Topology", border_style=theme.rich_border, expand=True)
    t.add_column("Package Name", style="bold white", width=22)
    t.add_column("Subdirectory", style=theme.rich_secondary, width=24)
    t.add_column("Type", width=12)
    t.add_column("Primary Specialist Arm", style=theme.rich_primary)

    arm_titles = {
        0: "System Architect",
        1: "Database & Schemas",
        2: "Backend API",
        3: "Frontend UI",
        4: "State & Caching",
        5: "QA & AST Test",
        6: "Security & Credentials",
        7: "DevOps & Deploy",
    }

    packages = topo.get("packages", [])
    for pkg in packages:
        arm_id = pkg.get("primary_arm", 2)
        arm_title = arm_titles.get(arm_id, f"Arm {arm_id}")
        t.add_row(pkg.get("name", ""), pkg.get("rel_path", ""), str(pkg.get("type", "")).upper(), f"Arm {arm_id} ({arm_title})")

    console.print(t)
    console.print(f"[dim]Total packages detected: [bold]{len(packages)}[/bold] (Monorepo: [bold]{'YES' if topo.get('is_monorepo') else 'NO'}[/bold])[/dim]\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register monorepo command with Typer apps."""
    app.command("monorepo")(monorepo_cli_cmd)
    octos_app.command("monorepo")(monorepo_cli_cmd)
