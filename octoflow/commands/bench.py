"""Bench CLI command for running 8-arm algorithmic & architectural challenge benchmarks."""

from typing import Optional
import typer
from rich.console import Console
from octoflow.themes import load_saved_theme

console = Console()


_notice_printed = False


def bench_cli_cmd(
    task: Optional[str] = typer.Option(None, "--task", "-t", help="Specific challenge key (rate_limiter, lru_cache, jwt_auth, topological_dag)"),
    mode: str = typer.Option("balanced", "--mode", "-m", help="Execution tier: fast, balanced, powerful"),
    workspace: str = typer.Option(".octoflow_bench", "--dir", "-d", help="Directory for benchmark sandbox execution"),
):
    r"""Run standardized 8-arm algorithmic & architectural challenge benchmarks. \[experimental]"""
    global _notice_printed
    if not _notice_printed:
        console.print("[yellow]Notice: 'bench' is an experimental feature and may change or be removed in future releases.[/yellow]\n")
        _notice_printed = True
    from octoflow.bench import run_swarm_benchmark_suite
    theme = load_saved_theme()
    console.print(f"\n[{theme.rich_primary}]◈ OctoFlow Swarm Benchmark Suite: Starting evaluation harness...[/{theme.rich_primary}]\n")
    run_swarm_benchmark_suite(task_key=task, mode=mode, workspace_dir=workspace, console=console)


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register bench command with Typer apps."""
    app.command("bench")(bench_cli_cmd)
    octos_app.command("bench")(bench_cli_cmd)
