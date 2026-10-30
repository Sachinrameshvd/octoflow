"""Report and Export CLI command for standalone HTML mission audit generation."""

import typer
from rich.console import Console

from octoflow.themes import load_saved_theme

console = Console()


def export_cli_cmd(
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    output: str | None = typer.Option(
        None, "--out", "-o", help="Target HTML audit report output path"
    ),
    open_browser: bool = typer.Option(
        False, "--open", help="Open generated HTML report in default browser"
    ),
):
    """Generate standalone self-contained HTML mission audit report with interactive connectome replay."""
    from octoflow.report import collect_mission_audit_data, generate_html_audit_report

    theme = load_saved_theme()
    console.print(
        f"\n[{theme.rich_primary}]◈ Generating Standalone HTML Swarm Mission Audit...[/{theme.rich_primary}]"
    )
    m_data = collect_mission_audit_data(workspace=workspace)
    report_path = generate_html_audit_report(m_data, output_path=output, theme_id=theme.id)
    console.print(
        f"[{theme.rich_success}]✔ Exported Standalone Audit Report:[/{theme.rich_success}] [bold white]{report_path}[/bold white]"
    )
    console.print(
        "[dim]100% self-contained single-file HTML • Zero external CDN dependencies • Connectome replay included.[/dim]\n"
    )
    if open_browser:
        import webbrowser

        webbrowser.open(f"file://{report_path.resolve()}")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register report and export commands with Typer apps."""
    app.command("report")(export_cli_cmd)
    octos_app.command("report")(export_cli_cmd)
    app.command("export")(export_cli_cmd)
    octos_app.command("export")(export_cli_cmd)
