"""Consortium and Octopolis CLI commands for multi-octopus swarms."""

import typer


def consortium_cmd(
    objective: str = typer.Argument(..., help="Engineering goal for the multi-octopus consortium"),
    octos: str = typer.Option(
        "auto", "--octos", "-o", help="Count of octopuses ('auto', 3 for Triad, 8 for Octopolis)"
    ),
    model: str = typer.Option(
        "mock", "--model", help="LLM backend: 'mock', 'anthropic', 'openai', 'ollama'"
    ),
    budget: float = typer.Option(10.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Target project workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer port"),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"
    ),
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open 3D Visualizer in browser"),
    theme: str | None = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run with mock provider, write no project files"
    ),
    plain: bool = typer.Option(
        False, "--plain", help="Force plain line-oriented output (no Live TUI dashboard)"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress progress telemetry lines"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output final outcome as machine-readable JSON"
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable ANSI color codes (respects NO_COLOR standard)"
    ),
    no_anim: bool = typer.Option(
        False, "--no-anim", help="Disable animations and continuous refresh"
    ),
    ascii_mode: bool = typer.Option(
        False, "--ascii", help="Force plain ASCII-only characters (< 128)"
    ),
    legacy_glyphs: bool = typer.Option(
        False, "--legacy-glyphs", help="Use legacy Unicode glyphs"
    ),
):
    """Deploy the multi-cephalopod consortium (3 to 8 octopuses • 24 to 64 arms) on a project."""
    from octoflow.commands.run import run

    run(
        objective=objective,
        mode="software_dev",
        model=model,
        budget=budget,
        workspace=workspace,
        port=port,
        host=host,
        open_ui=open_ui,
        octos=octos,
        theme=theme,
        dry_run=dry_run,
        plain=plain,
        quiet=quiet,
        json_output=json_output,
        no_color=no_color,
        no_anim=no_anim,
        ascii_mode=ascii_mode,
        legacy_glyphs=legacy_glyphs,
    )


def octos_octopolis(
    objective: str = typer.Argument(
        ..., help="Engineering goal for the 8-octopus Octopolis (64 Arms)"
    ),
    model: str = typer.Option("mock", "--model", help="LLM backend"),
    budget: float = typer.Option(15.00, "--budget", "-b", help="Max cost dollars"),
    workspace: str = typer.Option(".", "--dir", "-d", help="Workspace folder"),
    port: int = typer.Option(8088, "--port", "-p", help="3D Visualizer port"),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"
    ),
    open_ui: bool = typer.Option(False, "--ui", help="Auto-open visualizer"),
    theme: str | None = typer.Option(None, "--theme", "-t", help="Theme palette"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run with mock provider, write no project files"
    ),
    plain: bool = typer.Option(
        False, "--plain", help="Force plain line-oriented output (no Live TUI dashboard)"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress progress telemetry lines"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output final outcome as machine-readable JSON"
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable ANSI color codes (respects NO_COLOR standard)"
    ),
    no_anim: bool = typer.Option(
        False, "--no-anim", help="Disable animations and continuous refresh"
    ),
    ascii_mode: bool = typer.Option(
        False, "--ascii", help="Force plain ASCII-only characters (< 128)"
    ),
    legacy_glyphs: bool = typer.Option(
        False, "--legacy-glyphs", help="Use legacy Unicode glyphs"
    ),
):
    """Deploy the flagship 8-Octopus Octopolis (64 Neural Arms) on an objective."""
    from octoflow.commands.run import run

    run(
        objective=objective,
        mode="software_dev",
        model=model,
        budget=budget,
        workspace=workspace,
        port=port,
        host=host,
        open_ui=open_ui,
        octos="8",
        theme=theme,
        dry_run=dry_run,
        plain=plain,
        quiet=quiet,
        json_output=json_output,
        no_color=no_color,
        no_anim=no_anim,
        ascii_mode=ascii_mode,
        legacy_glyphs=legacy_glyphs,
    )


def register_consortium(app: typer.Typer) -> None:
    """Register consortium command with primary app."""
    app.command(name="consortium")(consortium_cmd)


def register_octopolis(octos_app: typer.Typer) -> None:
    """Register octopolis command with octos app."""
    octos_app.command("octopolis")(octos_octopolis)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register consortium and octopolis commands with Typer apps."""
    register_consortium(app)
    register_octopolis(octos_app)
