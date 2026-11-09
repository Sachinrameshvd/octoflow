"""OctoFlow CLI & Typer Application Wiring.

Registers all modularized command groups from octoflow.commands.* with lazy imports
to ensure `octoflow --help` starts up fast.
"""

import os
import sys
import traceback
from typing import Any

import click
import typer
from rich.console import Console
from typer.core import TyperGroup

from octoflow.errors import OctoFlowError
from octoflow.glyphs import (
    is_no_color,
    set_ascii_mode,
    set_legacy_glyphs_mode,
    set_no_anim_mode,
    set_no_color_mode,
    set_plain_mode,
)
from octoflow.logging_config import get_log_file, get_logger, is_trace_mode, setup_logging

logger = get_logger("cli")


def _is_trace_active(args: list | None = None, ctx: click.Context | None = None) -> bool:
    if is_trace_mode():
        return True
    if os.getenv("OCTOFLOW_DEBUG") == "1" or os.getenv("OCTOFLOW_TRACE") == "1":
        return True
    if "--trace" in sys.argv:
        return True
    if args and "--trace" in args:
        return True
    if ctx:
        curr: click.Context | None = ctx
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


def _version_callback(value: bool) -> None:
    if value:
        from octoflow import __version__

        typer.echo(f"OctoFlow v{__version__}")
        raise typer.Exit()


class OctoFlowGroup(TyperGroup):
    """Custom TyperGroup intercepting OctoFlowError and unexpected fatal exceptions."""

    def main(self, *args: Any, **kwargs: Any) -> Any:
        raw_args = args[0] if args else None
        arg_list = list(raw_args) if isinstance(raw_args, (list, tuple)) else sys.argv[1:]
        if "--no-color" in arg_list:
            set_no_color_mode(True)
        if "--no-anim" in arg_list:
            set_no_anim_mode(True)
        if "--ascii" in arg_list:
            set_ascii_mode(True)
        if "--legacy-glyphs" in arg_list:
            set_legacy_glyphs_mode(True)
        if "--plain" in arg_list:
            set_plain_mode(True)
        if is_no_color():
            console.no_color = True

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
            typer.Exit,
            typer.Abort,
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
            typer.Exit,
            typer.Abort,
            SystemExit,
            KeyboardInterrupt,
        ):
            raise
        except Exception as exc:
            _handle_unexpected_error(exc, trace=trace)


# Typer apps
app = typer.Typer(
    cls=OctoFlowGroup,
    help=(
        "OctoFlow is an autonomous multi-agent coding framework that plans, develops, and tests software projects using coordinated AI specialists. "
        "It combines local change detection with checkpoint safety to implement goals while keeping you in full control.\n\n"
        "Cephalopod Architecture Metaphor:\n"
        "  • Conductor: Planner coordinating high-level objectives and task graph execution\n"
        "  • Arm: Specialist agent executing targeted code and test operations\n"
        "  • Gate: Change detector measuring sensory surprise on file edits\n"
        "  • Bus: Message channel enabling low-latency agent-to-agent events\n"
        "  • Vertical Lobe: Memory system retaining heuristics and learned patterns across runs"
    ),
)
octos_app = typer.Typer(
    cls=OctoFlowGroup,
    help=(
        "OctosFlow coordinates multiple cephalopod swarms working in consortium on large-scale software engineering tasks. "
        "It distributes complex multi-repo and monorepo objectives across specialized multi-agent teams.\n\n"
        "Cephalopod Architecture Metaphor:\n"
        "  • Conductor: Planner coordinating high-level objectives and task graph execution\n"
        "  • Arm: Specialist agent executing targeted code and test operations\n"
        "  • Gate: Change detector measuring sensory surprise on file edits\n"
        "  • Bus: Message channel enabling low-latency agent-to-agent events\n"
        "  • Vertical Lobe: Memory system retaining heuristics and learned patterns across runs"
    ),
)
console = Console()


# -------------------------------------------------------------------------
# Callbacks (default to interactive cockpit)
# -------------------------------------------------------------------------
@app.callback(invoke_without_command=True)
def app_callback(
    ctx: typer.Context,
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output (INFO logging to stderr)."
    ),
    trace: bool = typer.Option(
        False, "--trace", help="Enable trace mode (DEBUG logging and tracebacks on error)."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show OctoFlow version and exit.",
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable ANSI color codes (respects NO_COLOR standard)."
    ),
    no_anim: bool = typer.Option(
        False, "--no-anim", help="Disable animations and continuous refresh."
    ),
    ascii_mode: bool = typer.Option(
        False, "--ascii", help="Force plain ASCII-only characters (< 128)."
    ),
    legacy_glyphs: bool = typer.Option(
        False, "--legacy-glyphs", help="Use legacy Unicode glyphs (lightning bolt, heavy check)."
    ),
    plain: bool = typer.Option(
        False, "--plain", help="Force plain line-oriented output (no Live TUI dashboard)."
    ),
):
    """Launch interactive cockpit if no command specified."""
    if no_color:
        set_no_color_mode(True)
    if no_anim:
        set_no_anim_mode(True)
    if ascii_mode:
        set_ascii_mode(True)
    if legacy_glyphs:
        set_legacy_glyphs_mode(True)
    if plain:
        set_plain_mode(True)
    if is_no_color():
        console.no_color = True

    setup_logging(verbose=verbose, trace=trace)
    if ctx.invoked_subcommand is None:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            console.print(ctx.get_help())
            raise typer.Exit(code=0)
        from octoflow.first_run import run_guided_first_run, should_run_first_run_wizard

        if should_run_first_run_wizard():
            run_guided_first_run(yes=False, launch_cockpit_after=True)
            return
        interactive_cockpit(host=host)


@octos_app.callback(invoke_without_command=True)
def octos_callback(
    ctx: typer.Context,
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Telemetry server bind host (default: 127.0.0.1)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output (INFO logging to stderr)."
    ),
    trace: bool = typer.Option(
        False, "--trace", help="Enable trace mode (DEBUG logging and tracebacks on error)."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show OctoFlow version and exit.",
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable ANSI color codes (respects NO_COLOR standard)."
    ),
    no_anim: bool = typer.Option(
        False, "--no-anim", help="Disable animations and continuous refresh."
    ),
    ascii_mode: bool = typer.Option(
        False, "--ascii", help="Force plain ASCII-only characters (< 128)."
    ),
    legacy_glyphs: bool = typer.Option(
        False, "--legacy-glyphs", help="Use legacy Unicode glyphs (lightning bolt, heavy check)."
    ),
    plain: bool = typer.Option(
        False, "--plain", help="Force plain line-oriented output (no Live TUI dashboard)."
    ),
):
    """Launch interactive cockpit if no command specified."""
    if no_color:
        set_no_color_mode(True)
    if no_anim:
        set_no_anim_mode(True)
    if ascii_mode:
        set_ascii_mode(True)
    if legacy_glyphs:
        set_legacy_glyphs_mode(True)
    if plain:
        set_plain_mode(True)
    if is_no_color():
        console.no_color = True

    setup_logging(verbose=verbose, trace=trace)
    if ctx.invoked_subcommand is None:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            console.print(ctx.get_help())
            raise typer.Exit(code=0)
        from octoflow.first_run import run_guided_first_run, should_run_first_run_wizard

        if should_run_first_run_wizard():
            run_guided_first_run(yes=False, launch_cockpit_after=True)
            return
        interactive_cockpit(host=host)


# -------------------------------------------------------------------------
# Command Registration
# -------------------------------------------------------------------------
from octoflow.commands import (  # noqa: E402 - commands are registered after Typer app instances are initialized
    audit,
    bench,
    checkpoint_cmds,
    config,
    consortium,
    doctor,
    eject,
    feedback,
    federation,
    guard,
    guild,
    heal,
    ignition_cmds,
    init,
    install_claude,
    manual,
    mcp,
    monorepo,
    notify,
    purge,
    receipt,
    record,
    replay,
    report,
    review_pr,
    run,
    runner,
    setup,
    theme,
    triage,
    ui,
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
purge.register(app, octos_app)
from octoflow import first_run  # noqa: E402
first_run.register(app, octos_app)
doctor.register(app, octos_app)
feedback.register(app, octos_app)
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
ignition_cmds.register(app, octos_app)
receipt.register(app, octos_app)
replay.register(app, octos_app)


def glossary_cli_cmd() -> None:
    """Print the plain-language mapping of OctoFlow architecture concepts."""
    from octoflow.messages import render_glossary_table

    console.print()
    console.print(render_glossary_table(console))
    console.print()


def version_cli_cmd() -> None:
    """Show OctoFlow version and exit."""
    from octoflow import __version__

    typer.echo(f"OctoFlow v{__version__}")


app.command("glossary")(glossary_cli_cmd)
octos_app.command("glossary")(glossary_cli_cmd)
app.command("version")(version_cli_cmd)
octos_app.command("version")(version_cli_cmd)


# -------------------------------------------------------------------------
# Backward-Compatibility Re-Exports
# -------------------------------------------------------------------------
from octoflow.cockpit import (  # noqa: E402
    CockpitInput,
    CockpitSession,
    confirm_live_cockpit,
    get_live_cockpit_input,
    get_live_wizard_input,
    interactive_cockpit,
    print_welcome_banner,
    run_cockpit,
)
from octoflow.commands.dashboard import (  # noqa: E402
    render_consortium_dashboard,
    render_dashboard,
)
from octoflow.commands.doctor import (  # noqa: E402
    doctor_cli_cmd,
    run_doctor,
)
from octoflow.commands.guard import (  # noqa: E402
    guard_cli_cmd,
    install_git_hooks,
    install_hooks_cli_cmd,
    run_guard,
)
from octoflow.commands.install_claude import (  # noqa: E402
    install_claude_cli_cmd,
)
from octoflow.first_run import (  # noqa: E402
    first_run_cli_cmd,
)
from octoflow.commands.purge import (  # noqa: E402
    purge_cli_cmd,
)
from octoflow.commands.report import (  # noqa: E402
    export_cli_cmd,
)
from octoflow.commands.run import (  # noqa: E402
    octos_run,
    run,
    train,
)
from octoflow.commands.setup import (  # noqa: E402
    run_setup_wizard,
    setup_cli_cmd,
)
from octoflow.commands.theme import (  # noqa: E402
    app_banner_cmd,
    app_screensaver_cmd,
    app_theme_cmd,
    octos_banner_cmd,
    octos_screensaver_cmd,
    octos_theme_cmd,
)

__all__ = [
    "app",
    "octos_app",
    "octos_main",
    "run_cockpit",
    "interactive_cockpit",
    "CockpitSession",
    "CockpitInput",
    "get_live_cockpit_input",
    "confirm_live_cockpit",
    "print_welcome_banner",
    "get_live_wizard_input",
    "render_dashboard",
    "render_consortium_dashboard",
    "run",
    "train",
    "octos_run",
    "run_doctor",
    "doctor_cli_cmd",
    "run_guard",
    "install_git_hooks",
    "guard_cli_cmd",
    "install_hooks_cli_cmd",
    "export_cli_cmd",
    "app_theme_cmd",
    "octos_theme_cmd",
    "app_banner_cmd",
    "octos_banner_cmd",
    "app_screensaver_cmd",
    "octos_screensaver_cmd",
    "run_setup_wizard",
    "setup_cli_cmd",
    "first_run_cli_cmd",
    "purge_cli_cmd",
    "install_claude_cli_cmd",
    "glossary_cli_cmd",
]


def octos_main():
    """CLI entrypoint for 'octos' command."""
    octos_app()


if __name__ == "__main__":
    app()
