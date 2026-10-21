"""OctoFlow CLI & Typer Application Wiring.

Registers all modularized command groups from octoflow.commands.* with lazy imports
to ensure `octoflow --help` starts up fast.
"""

from typing import Optional
import typer
from rich.console import Console

# Typer apps
app = typer.Typer(help="◈ OctoFlow: Decentralized Cephalopod Multi-Agent Swarm with Sensory Surprise Gating")
octos_app = typer.Typer(help="◈ OctosFlow: Multi-Cephalopod Swarm Consortium (3 to 8 Octopuses • 24 to 64 Arms)")
console = Console()

# -------------------------------------------------------------------------
# Callbacks (default to interactive cockpit)
# -------------------------------------------------------------------------
@app.callback(invoke_without_command=True)
def app_callback(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
):
    """Launch interactive cockpit if no command specified."""
    if ctx.invoked_subcommand is None:
        interactive_cockpit(host=host)


@octos_app.callback(invoke_without_command=True)
def octos_callback(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
):
    """Launch interactive cockpit if no command specified."""
    if ctx.invoked_subcommand is None:
        interactive_cockpit(host=host)


# -------------------------------------------------------------------------
# Command Registration
# -------------------------------------------------------------------------
from octoflow.commands import (
    run,
    consortium,
    ui,
    mcp,
    theme,
    setup,
    doctor,
    guard,
    init,
    review_pr,
    report,
    heal,
    triage,
    notify,
    guild,
    bench,
    monorepo,
    record,
    audit,
    eject,
    install_claude,
    federation,
    manual,
    runner,
    config,
)

# Register command groups in strict ordering to match snapshot baselines
run.register(app, octos_app)
ui.register_app_ui(app)
mcp.register_mcp_serve(app)
consortium.register_consortium(app)
consortium.register_octopolis(octos_app)
ui.register_octos_ui(octos_app)
theme.register(app, octos_app)
setup.register(app, octos_app)
doctor.register(app, octos_app)
mcp.register_mcp(app, octos_app)
guard.register(app, octos_app)
init.register(app, octos_app)
review_pr.register(app, octos_app)
report.register(app, octos_app)
heal.register(app, octos_app)
triage.register(app, octos_app)
notify.register(app, octos_app)
guild.register(app, octos_app)
bench.register(app, octos_app)
monorepo.register(app, octos_app)
record.register(app, octos_app)
audit.register(app, octos_app)
eject.register(app, octos_app)
install_claude.register(app, octos_app)
federation.register(app, octos_app)
manual.register(app, octos_app)
runner.register(app, octos_app)
config.register(app, octos_app)


# -------------------------------------------------------------------------
# Backward-Compatibility Re-Exports
# -------------------------------------------------------------------------
from octoflow.cockpit import (
    run_cockpit,
    interactive_cockpit,
    CockpitSession,
    CockpitInput,
    get_live_cockpit_input,
    confirm_live_cockpit,
    print_welcome_banner,
    get_live_wizard_input,
)
from octoflow.commands.dashboard import (
    render_dashboard,
    render_consortium_dashboard,
)
from octoflow.commands.run import (
    run,
    train,
    octos_run,
)
from octoflow.commands.doctor import (
    run_doctor,
    doctor_cli_cmd,
)
from octoflow.commands.guard import (
    run_guard,
    install_git_hooks,
    guard_cli_cmd,
    install_hooks_cli_cmd,
)
from octoflow.commands.report import (
    export_cli_cmd,
)
from octoflow.commands.theme import (
    app_theme_cmd,
    octos_theme_cmd,
    app_banner_cmd,
    octos_banner_cmd,
    app_screensaver_cmd,
    octos_screensaver_cmd,
)
from octoflow.commands.setup import (
    run_setup_wizard,
    setup_cli_cmd,
)
from octoflow.commands.install_claude import (
    install_claude_cli_cmd,
)


def octos_main():
    """CLI entrypoint for 'octos' command."""
    octos_app()


if __name__ == "__main__":
    app()
