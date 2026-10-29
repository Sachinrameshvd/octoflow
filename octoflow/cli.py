"""OctoFlow CLI & Typer Application Wiring.

Registers all modularized command groups from octoflow.commands.* with lazy imports
to ensure `octoflow --help` starts up fast.
"""

import os
import sys
import traceback
from typing import Optional, Any
import click
import typer
from typer.core import TyperGroup
from rich.console import Console

from octoflow.errors import OctoFlowError
from octoflow.logging_config import setup_logging, get_log_file, get_logger, is_trace_mode

logger = get_logger("cli")


def _is_trace_active(args: Optional[list] = None, ctx: Optional[click.Context] = None) -> bool:
    if is_trace_mode():
        return True
    if os.getenv("OCTOFLOW_DEBUG") == "1" or os.getenv("OCTOFLOW_TRACE") == "1":
        return True
    if "--trace" in sys.argv:
        return True
    if args and "--trace" in args:
        return True
    if ctx:
        curr: Optional[click.Context] = ctx
        while curr:
            if curr.params and curr.params.get("trace"):
                return True
            curr = curr.parent
    return False


def _handle_octoflow_error(e: OctoFlowError, trace: bool = False) -> None:
    typer.echo(e.format_cli(), err=True)
    if trace:
        traceback.print_exc(file=sys.stderr)
    sys.exit(e.exit_code)


def _handle_unexpected_error(exc: Exception, trace: bool = False) -> None:
    log_file = get_log_file()
    logger.error("Internal unexpected error: %s", exc, exc_info=True)
    if trace:
        traceback.print_exc(file=sys.stderr)
    else:
        typer.echo(f"Internal error: {exc}. See log: {log_file}", err=True)
    sys.exit(70)


class OctoFlowGroup(TyperGroup):
    """Custom TyperGroup intercepting OctoFlowError and unexpected fatal exceptions."""

    def main(self, *args: Any, **kwargs: Any) -> Any:
        raw_args = args[0] if args else None
        trace = _is_trace_active(raw_args)
        verbose = (
            ("--verbose" in (raw_args or []))
            or ("-v" in (raw_args or []))
            or (os.getenv("OCTOFLOW_VERBOSE") == "1")
        )
        setup_logging(verbose=verbose, trace=trace)
        try:
            return super().main(*args, **kwargs)
        except OctoFlowError as e:
            _handle_octoflow_error(e, trace=trace)
        except (
            click.ClickException,
            click.exceptions.Exit,
            click.exceptions.Abort,
            typer.exceptions.TyperException,
            typer.exceptions.Exit,
            typer.exceptions.Abort,
            SystemExit,
            KeyboardInterrupt,
        ):
            raise
        except Exception as exc:
            _handle_unexpected_error(exc, trace=trace)

    def invoke(self, ctx: click.Context) -> Any:
        trace = _is_trace_active(ctx=ctx)
        try:
            return super().invoke(ctx)
        except OctoFlowError as e:
            _handle_octoflow_error(e, trace=trace)
        except (
            click.ClickException,
            click.exceptions.Exit,
            click.exceptions.Abort,
            typer.exceptions.TyperException,
            typer.exceptions.Exit,
            typer.exceptions.Abort,
            SystemExit,
            KeyboardInterrupt,
        ):
            raise
        except Exception as exc:
            _handle_unexpected_error(exc, trace=trace)


# Typer apps
app = typer.Typer(
    cls=OctoFlowGroup,
    help="◈ OctoFlow: Decentralized Cephalopod Multi-Agent Swarm with Sensory Surprise Gating",
)
octos_app = typer.Typer(
    cls=OctoFlowGroup,
    help="◈ OctosFlow: Multi-Cephalopod Swarm Consortium (3 to 8 Octopuses • 24 to 64 Arms)",
)
console = Console()

# -------------------------------------------------------------------------
# Callbacks (default to interactive cockpit)
# -------------------------------------------------------------------------
@app.callback(invoke_without_command=True)
def app_callback(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output (INFO logging to stderr)."),
    trace: bool = typer.Option(False, "--trace", help="Enable trace mode (DEBUG logging and tracebacks on error)."),
):
    """Launch interactive cockpit if no command specified."""
    setup_logging(verbose=verbose, trace=trace)
    if ctx.invoked_subcommand is None:
        interactive_cockpit(host=host)


@octos_app.callback(invoke_without_command=True)
def octos_callback(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output (INFO logging to stderr)."),
    trace: bool = typer.Option(False, "--trace", help="Enable trace mode (DEBUG logging and tracebacks on error)."),
):
    """Launch interactive cockpit if no command specified."""
    setup_logging(verbose=verbose, trace=trace)
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
    checkpoint_cmds,
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
checkpoint_cmds.register(app, octos_app)


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
