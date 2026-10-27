"""Bench CLI command for running 8-arm algorithmic & architectural challenge benchmarks."""

from typing import Optional
import typer
from rich.console import Console

console = Console()

_notice_printed = False


def bench_cli_cmd(
    task: str = typer.Option("all", "--task", "-t", help="Challenge task ID ('all' or specific: rate_limiter, lru_cache, jwt_validator, dag_topo_sort)"),
    mode: str = typer.Option("both", "--mode", "-m", help="Gate mode: gated, ungated, or both"),
    provider: str = typer.Option("mock", "--provider", "-p", help="LLM provider name: mock, fake, anthropic, openai, gemini, ollama, etc."),
    model: Optional[str] = typer.Option(None, "--model", help="Model identifier (optional, uses provider default if omitted)"),
    runs: int = typer.Option(3, "--runs", "-n", help="Number of benchmark repetitions per task and mode (default: 3)"),
    seed: int = typer.Option(42, "--seed", "-s", help="Base pseudo-random seed (default: 42)"),
    out: str = typer.Option("benchmarks/results", "--out", "-o", help="Output directory for run JSONs and summary.md"),
    record_cassette: Optional[str] = typer.Option(None, "--record-cassette", help="Directory to record LLM request/response cassettes"),
):
    r"""Run standardized 8-arm algorithmic & architectural challenge benchmarks. \[experimental]"""
    global _notice_printed
    if not _notice_printed:
        console.print("[yellow]Notice: 'bench' is an experimental feature and may change or be removed in future releases.[/yellow]\n")
        _notice_printed = True
    from octoflow.bench import run_benchmark_harness
    run_benchmark_harness(
        task=task,
        mode=mode,
        provider=provider,
        model=model,
        runs=runs,
        seed=seed,
        out_dir=out,
        console=console,
        record_cassette=record_cassette,
    )


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register bench command with Typer apps."""
    app.command("bench")(bench_cli_cmd)
    octos_app.command("bench")(bench_cli_cmd)
