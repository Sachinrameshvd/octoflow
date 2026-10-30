"""Guild CLI command for managing 8-arm specialist guilds."""

import typer
from rich.console import Console
from rich.table import Table

from octoflow.config import (
    SOFTWARE_DEV_ROSTER,
    list_available_guilds,
    load_custom_guild,
    save_custom_guild,
)
from octoflow.themes import load_saved_theme

console = Console()


def guild_cli_cmd(
    action: str = typer.Argument("list", help="Action: 'list', 'show', 'export'"),
    name: str | None = typer.Argument(None, help="Guild name"),
):
    """Manage 8-arm specialist guilds (custom community rosters)."""
    theme = load_saved_theme()
    if action == "list":
        guilds = list_available_guilds()
        g_table = Table(
            title="Specialist 8-Arm Guilds & Rosters", border_style=theme.rich_border, expand=True
        )
        g_table.add_column("Guild Name", style="bold white", width=18)
        g_table.add_column("Type", style=theme.rich_secondary, width=12)
        g_table.add_column("Description", style="white")

        for g_name, g_desc in guilds.items():
            g_type = (
                "Built-In"
                if g_name in ["software_dev", "aiml_research", "fullstack_ai"]
                else "Community"
            )
            g_table.add_row(g_name, g_type, g_desc)

        console.print(g_table)
        console.print(
            "[dim]Tip: Use in cockpit with [bold]/guild <name>[/bold] or CLI [bold]octos run --guild <name>[/bold][/dim]\n"
        )

    elif action in ["show", "inspect"]:
        if not name:
            console.print(
                f"[{theme.rich_danger}]Error: Please specify guild name (e.g. octos guild show software_dev)[/{theme.rich_danger}]"
            )
            return
        roster = load_custom_guild(name)
        if not roster:
            console.print(f"[{theme.rich_danger}]Guild '{name}' not found.[/{theme.rich_danger}]")
            return

        r_table = Table(title=f"Guild Roster: {name}", border_style=theme.rich_border, expand=True)
        r_table.add_column("Arm", width=6, style=theme.rich_primary)
        r_table.add_column("Role Title", width=22, style="bold white")
        r_table.add_column("Tier", width=10, style=theme.rich_secondary)
        r_table.add_column("Domain Scope & Description", style="white")

        for arm in roster:
            r_table.add_row(
                f"Arm {arm.arm_id}",
                arm.title,
                arm.model_tier.upper(),
                f"{arm.description} (Domains: {', '.join(arm.workspace_domain)})",
            )
        console.print(r_table)

    elif action == "export":
        export_name = name or "custom_template"
        out_file = save_custom_guild(
            export_name, SOFTWARE_DEV_ROSTER, f"Custom {export_name} specialist roster template"
        )
        console.print(
            f"[{theme.rich_success}]✔ Exported guild template to: {out_file}[/{theme.rich_success}]"
        )
        console.print(
            "[dim]Edit the JSON file to customize arm titles, domains, prompts, and model tiers.[/dim]\n"
        )


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register guild command with Typer apps."""
    app.command("guild")(guild_cli_cmd)
    octos_app.command("guild")(guild_cli_cmd)
