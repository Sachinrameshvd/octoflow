"""CLI commands for managing OctoFlow typed configuration and settings."""

from __future__ import annotations

import json

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from octoflow.settings import (
    ConfigurationError,
    get_default_config_path,
    load_settings,
    mask_secret_value,
    migrate_config_if_needed,
    restore_config_backup,
    set_config_value,
)

config_app = typer.Typer(
    name="config",
    help="Inspect, validate, and update OctoFlow typed configuration settings.",
    no_args_is_help=True,
)
console = Console()


def _handle_error(e: Exception) -> None:
    """Print clean single-line error and exit code 3 without traceback."""
    if isinstance(e, ConfigurationError):
        console.print(f"[bold red]{e.format_one_liner()}[/bold red]")
    elif isinstance(e, ValidationError):
        first_err = e.errors()[0]
        loc = ".".join(str(p) for p in first_err["loc"])
        msg = first_err["msg"]
        console.print(f"[bold red]Configuration error in '{loc}': {msg}[/bold red]")
    else:
        console.print(f"[bold red]Configuration error: {e}[/bold red]")
    raise typer.Exit(code=3)


@config_app.command("path")
def cmd_config_path() -> None:
    """Display the filesystem path of the configuration file."""
    cfg_path = get_default_config_path()
    typer.echo(str(cfg_path))


@config_app.command("show")
def cmd_config_show(
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output raw JSON with masked secrets."
    ),
) -> None:
    """Display current active configuration settings with masked secrets."""
    try:
        settings = load_settings()
    except Exception as e:
        _handle_error(e)

    masked_data = settings.to_dict(mask_secrets=True)

    if json_output:
        console.print(json.dumps(masked_data, indent=2))
        return

    # Rich styled output
    table = Table(title="◈ OctoFlow Active Configuration", border_style="cyan", expand=True)
    table.add_column("Section", style="bold cyan", width=18)
    table.add_column("Property", style="bold white", width=26)
    table.add_column("Active Value", style="green")

    # Defaults
    table.add_row("defaults", "default_provider", str(settings.defaults.default_provider))
    table.add_row("defaults", "default_model", str(settings.defaults.default_model or ""))
    table.add_row("defaults", "default_scale", f"{settings.defaults.default_scale} octopus")

    # UI
    table.add_row("ui", "theme", str(settings.ui.theme))
    table.add_row("ui", "animation", str(settings.ui.animation))
    table.add_row("ui", "color", str(settings.ui.color))
    table.add_row("ui", "ascii", str(settings.ui.ascii))

    # Server
    table.add_row("server", "host", str(settings.server.host))
    table.add_row("server", "ws_port", str(settings.server.ws_port))
    table.add_row("server", "http_port", str(settings.server.http_port))

    # Providers
    if settings.providers:
        for p_name, p_data in settings.providers.items():
            key_masked = mask_secret_value(p_data.api_key)
            val_summary = f"enabled={p_data.enabled}"
            if p_data.model:
                val_summary += f", model={p_data.model}"
            if p_data.base_url:
                val_summary += f", url={p_data.base_url}"
            if key_masked:
                val_summary += f", key={key_masked}"
            table.add_row("providers", p_name, val_summary)
    else:
        table.add_row("providers", "(none configured)", "[dim]No provider overrides[/dim]")

    # Extras
    if settings.extras:
        for k, v in settings.extras.items():
            table.add_row("extras", k, str(v))

    console.print(table)


@config_app.command("set")
def cmd_config_set(
    key: str = typer.Argument(..., help="Setting key path (e.g. ui.theme, server.ws_port)"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a single configuration key value, validate, and write atomically."""
    try:
        updated = set_config_value(key, value)
    except Exception as e:
        _handle_error(e)

    disp_val = value
    if any(s in key.lower() for s in ("key", "secret", "token", "password")):
        disp_val = mask_secret_value(value)

    cfg_path = get_default_config_path()
    console.print(
        f"[bold green]✔ Successfully set '{key}' = '{disp_val}' in {cfg_path}[/bold green]"
    )


@config_app.command("validate")
def cmd_config_validate() -> None:
    """Validate current configuration file against Pydantic schema."""
    cfg_path = get_default_config_path()
    if not cfg_path.exists():
        console.print(
            f"[yellow]Notice: Configuration file does not exist at {cfg_path} (defaults active).[/yellow]"
        )
        return

    try:
        settings = load_settings(cfg_path=cfg_path)
    except Exception as e:
        _handle_error(e)

    console.print(
        f"[bold green]✔ Configuration valid: {cfg_path} (schema_version={settings.schema_version})[/bold green]"
    )


@config_app.command("migrate")
def cmd_config_migrate(
    down: bool = typer.Option(
        False, "--down", "--restore", help="Restore configuration from the latest backup."
    ),
) -> None:
    """Migrate configuration to latest schema or restore from backup."""
    cfg_path = get_default_config_path()
    if down:
        try:
            bak_path = restore_config_backup(cfg_path)
            console.print(f"[bold green]✔ Restored configuration from {bak_path.name}[/bold green]")
        except Exception as e:
            _handle_error(e)
        return

    try:
        migrated, bak_path = migrate_config_if_needed(cfg_path)
        if migrated and bak_path:
            console.print(
                f"[bold green]✔ Migrated {cfg_path.name} to schema_version=1 (Backup saved to {bak_path.name})[/bold green]"
            )
        else:
            console.print(
                f"[bold green]✔ Configuration is already up to date ({cfg_path.name}).[/bold green]"
            )
    except Exception as e:
        _handle_error(e)


def register(app: typer.Typer, octos_app: typer.Typer | None = None) -> None:
    """Register config command group into Typer app(s)."""
    app.add_typer(config_app, name="config")
    if octos_app is not None:
        octos_app.add_typer(config_app, name="config")
