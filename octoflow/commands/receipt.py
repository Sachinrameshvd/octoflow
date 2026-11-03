"""Receipt CLI command for displaying truthful token expenditure and gate savings."""

from __future__ import annotations

import json
import sys

import typer
from rich.console import Console

from octoflow.receipt import (
    RECEIPT_METHOD_EXPLANATION,
    TokenReceipt,
    load_receipt,
    render_terminal_receipt,
)

console = Console()


def receipt_cli_cmd(
    run_id: str | None = typer.Argument(
        None, help="Optional run ID. Defaults to the latest execution run."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit receipt as machine-readable JSON matching schema."
    ),
    method: bool = typer.Option(
        False, "--method", help="Display the exact mathematical calculation methodology."
    ),
) -> None:
    """Display the truthful token receipt and sensory gate savings for an OctoFlow run."""
    if method:
        if json_output:
            console.print(
                json.dumps(
                    {
                        "method": RECEIPT_METHOD_EXPLANATION,
                        "confidence_rules": {
                            "measured": "All tokens gathered directly from LLM provider API response headers/usage metadata.",
                            "estimated": "Character heuristic ceil(len(text)/4) applied to prompt/response buffers when unmetered.",
                            "avoided": "Estimated prompt size that would have been dispatched to central conductor for local reflex actions.",
                        },
                    },
                    indent=2,
                )
            )
            return

        console.print("\n[bold cyan]OctoFlow Token Receipt Methodology:[/bold cyan]")
        console.print(f"  {RECEIPT_METHOD_EXPLANATION}\n")
        console.print("[bold]Accounting Rules:[/bold]")
        console.print(
            "  • [green]Measured[/green]: Sourced directly from provider API response metadata (e.g. Ollama, Anthropic, OpenAI)."
        )
        console.print(
            "  • [yellow]Estimated[/yellow]: Standard character heuristic `ceil(chars / 4)` applied when unmetered."
        )
        console.print(
            "  • [cyan]Avoided[/cyan]: Prompt token estimate for sensory evaluations resolved by local reflexes without central escalation."
        )
        console.print(
            "  • [magenta]Baseline[/magenta]: Empirical comparisons against recorded benchmarks in benchmarks/results/ (never generic percentages).\n"
        )
        return

    try:
        receipt = load_receipt(run_id=run_id)
    except FileNotFoundError as fnf:
        if json_output:
            console.print(json.dumps({"error": str(fnf)}, indent=2))
            raise typer.Exit(code=1) from None
        console.print(f"[yellow]No token receipt found:[/yellow] {fnf}")
        console.print("Run an autonomous mission with [bold cyan]octoflow run \"<goal>\"[/bold cyan] first.")
        raise typer.Exit(code=1) from None
    except Exception as e:
        if json_output:
            console.print(json.dumps({"error": str(e)}, indent=2))
            raise typer.Exit(code=1) from None
        console.print(f"[red]Error loading token receipt:[/red] {e}")
        raise typer.Exit(code=1) from None

    if json_output:
        # Validate against pydantic schema before printing
        sys.stdout.write(receipt.model_dump_json(indent=2) + "\n")
        return

    # Render terminal receipt block
    block = render_terminal_receipt(receipt)
    console.print()
    console.print(block)
    console.print()


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register receipt command with Typer apps."""
    app.command("receipt")(receipt_cli_cmd)
    octos_app.command("receipt")(receipt_cli_cmd)
