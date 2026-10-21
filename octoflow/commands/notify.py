"""Notify CLI command for dispatching mission status cards to Slack or Discord."""

from typing import Optional
import typer
from rich.console import Console
from octoflow.themes import load_saved_theme

console = Console()


def notify_cli_cmd(
    message: str = typer.Argument("OctoFlow Swarm Mission Update", help="Notification summary text"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Target Slack or Discord webhook URL"),
):
    """Dispatch mission status card to team Slack or Discord webhook."""
    from octoflow.notify import send_mission_notification
    theme = load_saved_theme()
    ok = send_mission_notification(webhook_url=url, custom_message=message)
    if ok:
        console.print(f"[{theme.rich_success}]✔ Successfully dispatched alert to team webhook.[/{theme.rich_success}]\n")
    else:
        console.print(f"[{theme.rich_warning}]▲ Webhook dispatch skipped: No active webhook URL configured or network unreachable.[/{theme.rich_warning}]\n")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register notify command with Typer apps."""
    app.command("notify")(notify_cli_cmd)
    octos_app.command("notify")(notify_cli_cmd)
