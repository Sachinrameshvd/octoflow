"""Guild CLI command for managing 8-arm specialist guilds (P8.2)."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from octoflow.guild import (
    BUILTIN_GUILD_SPECS,
    GuildSpec,
    list_guilds,
    load_guild,
    save_guild,
    validate_guild_file,
)
from octoflow.themes import load_saved_theme

console = Console()


def guild_cli_cmd(
    action: str = typer.Argument("list", help="Action: 'list', 'show', 'validate', 'export'"),
    name: str | None = typer.Argument(None, help="Guild name or JSON file path"),
) -> None:
    """Manage 8-arm specialist guilds (custom community rosters)."""
    theme = load_saved_theme()
    act = (action or "list").strip().lower()

    if act == "list":
        guild_entries = list_guilds()
        g_table = Table(
            title="Specialist 8-Arm Guilds & Rosters",
            border_style=theme.rich_border,
            expand=True,
        )
        g_table.add_column("Guild Name", style="bold white", width=18)
        g_table.add_column("Source", style=theme.rich_secondary, width=12)
        g_table.add_column("Arms", justify="center", width=6)
        g_table.add_column("Description", style="white")

        for g in guild_entries:
            src_label = {
                "builtin": "Built-In",
                "user": "User (~/.octoflow)",
                "project": "Project",
            }.get(g["source"], g["source"].capitalize())
            g_table.add_row(g["name"], src_label, str(g["arms_count"]), g["description"])

        console.print(g_table)
        console.print(
            "[dim]Tip: Use in CLI with [bold]octoflow run --guild <name>[/bold] or validate with [bold]octoflow guild validate <file.json>[/bold][/dim]\n"
        )

    elif act == "validate":
        if not name:
            console.print(
                f"[{theme.rich_danger}]Error: Please specify a JSON file path to validate (e.g. octoflow guild validate examples/guilds/data_science.json)[/{theme.rich_danger}]"
            )
            raise typer.Exit(code=1)

        target_path = Path(name).expanduser()
        is_valid, errors, spec = validate_guild_file(target_path)

        if not is_valid or spec is None:
            console.print(
                f"[{theme.rich_danger}]✘ Validation failed for '{name}':[/{theme.rich_danger}]"
            )
            for err in errors:
                console.print(f"  [{theme.rich_danger}]• {err}[/{theme.rich_danger}]")
            raise typer.Exit(code=1)

        console.print(
            f"[{theme.rich_success}]✔ Guild specification in '{name}' is valid (8 arms defined for '{spec.name}').[/{theme.rich_success}]"
        )

    elif act in ["show", "inspect"]:
        if not name:
            console.print(
                f"[{theme.rich_danger}]Error: Please specify guild name (e.g. octoflow guild show software_dev)[/{theme.rich_danger}]"
            )
            raise typer.Exit(code=1)

        try:
            # Check if name is an existing JSON file first
            if Path(name).is_file():
                is_valid, _, spec = validate_guild_file(Path(name))
                if not is_valid or spec is None:
                    console.print(
                        f"[{theme.rich_danger}]Failed to load guild file '{name}'.[/{theme.rich_danger}]"
                    )
                    raise typer.Exit(code=1)
            else:
                spec = load_guild(name)
        except Exception as e:
            console.print(
                f"[{theme.rich_danger}]Guild '{name}' not found: {e}[/{theme.rich_danger}]"
            )
            raise typer.Exit(code=1) from e

        r_table = Table(
            title=f"Guild Roster: {spec.name} — {spec.description}",
            border_style=theme.rich_border,
            expand=True,
        )
        r_table.add_column("Arm", width=6, style=theme.rich_primary)
        r_table.add_column("Role", width=18, style="bold white")
        r_table.add_column("Color", width=10)
        r_table.add_column("Tools", width=24, style=theme.rich_secondary)
        r_table.add_column("Domain Scope & Focus", style="white")

        for arm in sorted(spec.arms, key=lambda a: a.id):
            tools_str = ", ".join(arm.tools) if arm.tools else "default"
            scope_str = f"Scope: [{', '.join(arm.file_scope)}]" if arm.file_scope else ""
            focus_str = f"{arm.focus} {scope_str}".strip()
            r_table.add_row(
                f"Arm {arm.id}",
                arm.role,
                f"[{arm.color}]{arm.color}[/{arm.color}]",
                tools_str,
                focus_str,
            )
        console.print(r_table)

    elif act == "export":
        export_name = name or "custom_template"
        template_spec = GuildSpec(
            name=export_name,
            description=f"Custom {export_name} specialist roster template",
            arms=[arm.model_copy() for arm in BUILTIN_GUILD_SPECS["software_dev"].arms],
        )
        out_file = save_guild(template_spec)
        console.print(
            f"[{theme.rich_success}]✔ Exported guild template to: {out_file}[/{theme.rich_success}]"
        )
        console.print(
            "[dim]Edit the JSON file to customize arm roles, colors, tools, and domains.[/dim]\n"
        )
    else:
        console.print(
            f"[{theme.rich_danger}]Unknown guild action '{action}'. Allowed actions: list, show, validate, export[/{theme.rich_danger}]"
        )
        raise typer.Exit(code=1)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register guild command with Typer apps."""
    app.command("guild")(guild_cli_cmd)
    octos_app.command("guild")(guild_cli_cmd)
