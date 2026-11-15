"""Inter-Octopus Phase Checkpoints and Interactive Steering Controller (Milestone 3).

Provides human-in-the-loop pause gates between consortium phase transitions:
1. Records verifiable phase checkpoints (deliverables, completed octopuses, next phase goals)
2. Renders interactive checkpoint review cards in the terminal
3. Allows developers to steer mid-flight (add new constraints, alter specifications, or redirect)
4. Injects human steering directives adaptively across the Synaptic Bus into downstream octopuses
5. Supports non-blocking automatic continuation in CI/headless environments
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from octoflow.glyphs import glyph


@dataclass
class PhaseCheckpoint:
    """Snapshot of multi-octopus swarm state at an inter-octopus phase boundary."""

    phase_id: int
    phase_name: str
    completed_octopuses: list[dict[str, Any]] = field(default_factory=list)
    upcoming_octopuses: list[dict[str, Any]] = field(default_factory=list)
    files_delivered: list[str] = field(default_factory=list)
    steering_directives: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    total_cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize checkpoint state to a JSON-compatible dictionary."""
        return asdict(self)


@dataclass
class SteeringResult:
    """Decision resulting from an interactive phase checkpoint review."""

    action: str  # "continue" | "steer" | "abort"
    guidance: str = ""


def render_phase_checkpoint_card(checkpoint: PhaseCheckpoint, theme: Any = None) -> Panel:
    """Render a rich terminal card summarizing phase completion and presenting steering options."""
    ok_sym = glyph("OK")
    bolt_sym = glyph("BOLT")
    diamond_sym = glyph("DIAMOND")
    bullet_sym = glyph("BULLET")

    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(style="bold cyan", width=16)
    table.add_column(style="white")

    table.add_row("◈ PHASE GATE", f"[bold green]{ok_sym} {checkpoint.phase_name}[/bold green]")
    mins, secs = divmod(int(time.time() - checkpoint.timestamp), 60)
    table.add_row("◈ CHECKPOINT", f"{mins:02d}:{secs:02d} elapsed  [dim](Cost: ${checkpoint.total_cost:.3f})[/dim]")

    if checkpoint.completed_octopuses:
        table.add_row("", "")
        table.add_row(f"[bold cyan]{ok_sym} Completed:[/bold cyan]", "")
        for octo in checkpoint.completed_octopuses:
            o_id = octo.get("octopus_id", 0)
            o_title = octo.get("title", f"Octopus {o_id}")
            o_summary = octo.get("summary", "Phase deliverable established")
            table.add_row(
                f"  [green]● Octo {o_id}:[/green]",
                f"[bold white]{o_title}[/bold white]  [dim]— {o_summary}[/dim]",
            )

    if checkpoint.files_delivered:
        table.add_row("", "")
        table.add_row(f"[dim]{bullet_sym} Files Created:[/dim]", f"[dim]{', '.join(checkpoint.files_delivered[:8])}[/dim]")

    if checkpoint.upcoming_octopuses:
        table.add_row("", "")
        table.add_row(f"[bold yellow]{bolt_sym} Upcoming:[/bold yellow]", "")
        for octo in checkpoint.upcoming_octopuses:
            o_id = octo.get("octopus_id", 0)
            o_title = octo.get("title", f"Octopus {o_id}")
            o_goal = octo.get("goal", "Upcoming domain sprint")
            table.add_row(
                f"  [yellow]○ Octo {o_id}:[/yellow]",
                f"[bold white]{o_title}[/bold white]  [dim]— {o_goal[:65]}...[/dim]" if len(o_goal) > 65 else f"[bold white]{o_title}[/bold white]  [dim]— {o_goal}[/dim]",
            )

    if checkpoint.steering_directives:
        table.add_row("", "")
        table.add_row(f"[cyan]{diamond_sym} Directives:[/cyan]", "")
        for idx, direct in enumerate(checkpoint.steering_directives, 1):
            table.add_row(f"  [dim]#{idx}:[/dim]", f"[italic cyan]{direct}[/italic cyan]")

    table.add_row("", "")
    table.add_row(
        "[bold cyan]◈ STEERING[/bold cyan]",
        "[bold green][1/C] Continue[/bold green]  |  "
        "[bold yellow][2/S] Steer Swarm[/bold yellow]  |  "
        "[bold red][3/Q] Abort & Save[/bold red]",
    )

    title = f"[bold cyan]◈ OctoFlow Phase Checkpoint Gate: {checkpoint.phase_name}[/bold cyan]"
    return Panel(table, title=title, border_style="cyan", padding=(1, 2))


def conduct_phase_steering(
    checkpoint: PhaseCheckpoint,
    console: Console | None = None,
    non_interactive: bool = False,
) -> SteeringResult:
    """Prompt the developer at an inter-octopus phase checkpoint to continue, steer, or abort."""
    c = console or Console()

    # Always render the phase summary card so progress is visible
    c.print()
    c.print(render_phase_checkpoint_card(checkpoint))
    c.print()

    # Auto-continue in non-interactive/automated pipelines
    if non_interactive or not (sys.stdin.isatty() and sys.stdout.isatty()):
        return SteeringResult(action="continue")

    c.print("[bold white]Phase checkpoint reached.[/bold white] Select an option:")
    c.print("   [bold green][1/C][/bold green] Continue to next phase as planned [dim](Default)[/dim]")
    c.print("   [bold yellow][2/S][/bold yellow] Steer swarm (Inject directives, adjust specifications, or alter tech choices)")
    c.print("   [bold red][3/Q][/bold red] Abort swarm safely (Persist checkpoint and exit)\n")

    c.print("[dim]Choice [1/2/3, default: 1]: [/dim]", end="")
    try:
        raw = sys.stdin.readline().strip().lower()
    except (KeyboardInterrupt, EOFError):
        c.print("\n[yellow]Keyboard interrupt detected. Aborting cleanly...[/yellow]")
        return SteeringResult(action="abort")

    if not raw or raw in ("1", "c", "continue"):
        c.print("[bold green]✔ Proceeding with next phase sprint.[/bold green]\n")
        return SteeringResult(action="continue")

    if raw in ("3", "q", "abort", "quit", "exit"):
        c.print("[bold red]✖ Swarm execution halted by developer. Checkpoint saved.[/bold red]\n")
        return SteeringResult(action="abort")

    if raw in ("2", "s", "steer", "modify"):
        c.print("\n[bold yellow]◈ Developer Steering Mode Active[/bold yellow]")
        c.print("[dim]Type your steering directive, adjustments, or additional constraints for the upcoming phase:[/dim]")
        c.print("[yellow]steering ❯ [/yellow]", end="")
        try:
            directive = sys.stdin.readline().strip()
        except (KeyboardInterrupt, EOFError):
            directive = ""

        if directive:
            c.print(f"\n[bold green]✔ Injected Human Steering Directive:[/] [italic cyan]{directive}[/italic cyan]\n")
            return SteeringResult(action="steer", guidance=directive)
        else:
            c.print("[dim]No directives provided. Continuing with original plan.[/dim]\n")
            return SteeringResult(action="continue")

    return SteeringResult(action="continue")


def save_phase_checkpoint(workspace: str, checkpoint: PhaseCheckpoint) -> Path:
    """Persist phase checkpoint data to .octoflow/checkpoint.json and phase-specific snapshot."""
    ws = Path(workspace).resolve()
    ckpt_dir = ws / ".octoflow"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    # 1. Main rolling checkpoint
    main_ckpt = ckpt_dir / "checkpoint.json"
    data = checkpoint.to_dict()
    main_ckpt.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # 2. Phase-indexed snapshot
    phase_snap = ckpt_dir / f"checkpoint_phase_{checkpoint.phase_id}.json"
    phase_snap.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return main_ckpt


def format_steering_history(directives: list[str]) -> str:
    """Format list of steering directives into directive constraint text."""
    if not directives:
        return ""
    lines = [f"- {d}" for d in directives]
    return "Human Steering Directives Applied Across Phases:\n" + "\n".join(lines)
