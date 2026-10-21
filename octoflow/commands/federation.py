"""Federation CLI command for zero-trust agent federation and PII redaction."""

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

console = Console()


def federation_cli_cmd(
    action: str = typer.Argument("status", help="Action: status, peers, test-pii"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Text to test against 14-rule PII filter"),
):
    """Zero-trust multi-machine agent federation and PII redaction pipeline."""
    from octoflow.federation import GLOBAL_FEDERATION_GUARD, PII_RULES
    from octoflow.themes import load_saved_theme
    theme = load_saved_theme()
    if action == "status":
        t = Table(title="Zero-Trust Federation & PII Security Rules", border_style=theme.rich_border)
        t.add_column("Rule Name", style="bold white", width=22)
        t.add_column("Severity", style=theme.rich_secondary, width=12)
        t.add_column("Redacted Mask", style="dim", width=32)
        for r in PII_RULES:
            t.add_row(r.name, r.severity, r.replacement)
        console.print(t)
        console.print(f"[dim]Default PII Action: [bold green]{GLOBAL_FEDERATION_GUARD.default_action.value}[/bold green] | Total Intercepted Events: {len(GLOBAL_FEDERATION_GUARD.audit_log)}[/dim]\n")
    elif action == "test-pii":
        sample = text or ("My key is " + "sk-ant-" + "api03-abcdef123456789012345678 and email is test@company.com")
        cleaned, events = GLOBAL_FEDERATION_GUARD.scan_and_sanitize(sample)
        console.print(f"[{theme.rich_primary}]Original Input:[/{theme.rich_primary}] {sample}")
        console.print(f"[{theme.rich_success}]Sanitized Output:[/{theme.rich_success}] {cleaned}")
        console.print(f"[dim]Intercepted {len(events)} security/PII patterns.[/dim]\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register federation command with Typer apps."""
    app.command("federation")(federation_cli_cmd)
    octos_app.command("federation")(federation_cli_cmd)
