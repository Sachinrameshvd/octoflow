"""Audit CLI command for system readiness and security diagnostic across 5 cephalopod dimensions."""

import typer
from rich.console import Console

console = Console()


def audit_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder to audit"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output audit report as raw JSON"),
):
    """Run 1-100 system readiness and security diagnostic across 5 cephalopod dimensions."""
    from octoflow.audit import evaluate_workspace, print_audit_report
    report = evaluate_workspace(workspace)
    if json_output:
        console.print_json(report.model_dump_json(indent=2))
    else:
        print_audit_report(report, console=console)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register audit command with Typer apps."""
    app.command("audit")(audit_cli_cmd)
    octos_app.command("audit")(audit_cli_cmd)
