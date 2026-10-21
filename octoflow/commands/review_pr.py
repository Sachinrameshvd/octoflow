"""Review-PR CLI command for 3-arm CI/CD PR diff auditing."""

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from octoflow.themes import load_saved_theme

console = Console()


def review_pr_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
    base: str = typer.Option("HEAD~1", "--base", "-b", help="Base git ref to diff against"),
    summary: bool = typer.Option(True, "--summary/--no-summary", help="Append markdown to $GITHUB_STEP_SUMMARY"),
    export: Optional[str] = typer.Option(None, "--export", "-e", help="Path to export standalone HTML audit report"),
    shadow: bool = typer.Option(False, "--shadow", help="Run advisory audit without blocking PR merge (Shadow CI Mode)"),
):
    """Execute automated 3-Arm CI/CD PR Review over git diffs."""
    from octoflow.ci import review_pull_request
    theme = load_saved_theme()
    mode_label = " [dim](Shadow CI Mode: Non-blocking)[/dim]" if shadow else ""
    console.print(f"\n[{theme.rich_primary}]● OctoFlow Swarm Guard: Auditing Pull Request Diff...{mode_label}[/{theme.rich_primary}]\n")
    res = review_pull_request(workspace=workspace, base_ref=base, write_summary=summary, shadow_mode=shadow)

    # Render Terminal Review Table
    t = Table(title="OctoFlow Swarm Guard PR Audit" + (" [SHADOW CI]" if shadow else ""), border_style=theme.rich_border, expand=True)
    t.add_column("Ganglia Arm", style="bold white", width=22)
    t.add_column("Role Scope", style=theme.rich_secondary, width=20)
    t.add_column("Status", width=12)
    t.add_column("Audit Findings", style="white")

    arm6_ok = not any("CRITICAL" in f for f in res["arm6_findings"])
    arm5_ok = not any("CRITICAL" in f for f in res["arm5_findings"])
    arm0_ok = not any("Inverted" in f for f in res["arm0_findings"])

    t.add_row("Arm 6: Security", "Credentials & Injection", f"[{theme.rich_success}]✔ PASSED[/]" if arm6_ok else f"[{theme.rich_danger}]✖ BLOCKED[/]", " • ".join(res["arm6_findings"]))
    t.add_row("Arm 5: QA & AST", "Syntax & Test Coverage", f"[{theme.rich_success}]✔ PASSED[/]" if arm5_ok else f"[{theme.rich_danger}]✖ BLOCKED[/]", " • ".join(res["arm5_findings"]))
    t.add_row("Arm 0: Architect", "Topology & Contracts", f"[{theme.rich_success}]✔ PASSED[/]" if arm0_ok else f"[{theme.rich_warning}]ℹ ADVISORY[/]", " • ".join(res["arm0_findings"]))

    console.print(t)

    if export:
        from octoflow.report import collect_mission_audit_data, generate_html_audit_report
        m_data = collect_mission_audit_data(workspace=workspace)
        out_html = generate_html_audit_report(m_data, output_path=export, theme_id=theme.id)
        console.print(f"\n[{theme.rich_success}]✔ Exported Standalone Audit Report:[/{theme.rich_success}] [bold white]{out_html}[/bold white]")

    if res["hard_block"] and not shadow:
        console.print(f"\n[{theme.rich_danger}]✖ Merge Blocked: Critical security vulnerabilities or AST syntax errors detected.[/{theme.rich_danger}]\n")
        raise typer.Exit(code=1)
    elif res["hard_block"] and shadow:
        console.print(f"\n[{theme.rich_warning}]▲ Shadow CI: Merge hazards detected, but PR was NOT blocked (Advisory Mode).[/{theme.rich_warning}]\n")
    else:
        console.print(f"\n[{theme.rich_success}]✔ Swarm Verdict: READY TO MERGE. Zero merge hazards detected.[/{theme.rich_success}]\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register review-pr command with Typer apps."""
    app.command("review-pr")(review_pr_cli_cmd)
    octos_app.command("review-pr")(review_pr_cli_cmd)
