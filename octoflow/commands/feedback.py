"""Privacy-preserving voluntary feedback command and post-run hint (P12.3).

Constructs prefilled GitHub Issue or Discussion URLs client-side.
Never makes background network requests or transmits telemetry.
"""

from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from octoflow.commands.doctor import generate_bugreport_text
from octoflow.glyphs import glyph
from octoflow.settings import get_default_config_path, load_settings, save_settings

console = Console()

DEFAULT_REPO = "TODO_OWNER_OR_ORG/octoflow"
MAX_URL_LENGTH = 4000


def build_feedback_issue_url(
    title: str,
    body: str,
    labels: list[str] | None = None,
    repo: str = DEFAULT_REPO,
    is_discussion: bool = False,
    discussion_category: str | None = None,
) -> str:
    """Build a prefilled GitHub issue or discussion URL, safely URL-encoded."""
    if is_discussion:
        base_url = f"https://github.com/{repo}/discussions/new"
        params: dict[str, str] = {
            "title": title,
            "body": body,
        }
        if discussion_category:
            params["category"] = discussion_category
    else:
        base_url = f"https://github.com/{repo}/issues/new"
        params = {
            "title": title,
            "body": body,
        }
        if labels:
            params["labels"] = ",".join(labels)

    encoded = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{encoded}"

    # Truncate body if URL exceeds max safe length for browser address bars
    if len(full_url) > MAX_URL_LENGTH:
        overflow = len(full_url) - MAX_URL_LENGTH + 120
        truncated_body = (
            body[:-overflow]
            + "\n\n... [Diagnostics truncated for URL length: run `octoflow bugreport` for full report]"
        )
        params["body"] = truncated_body
        encoded = urllib.parse.urlencode(params)
        full_url = f"{base_url}?{encoded}"

    return full_url


def maybe_show_post_run_feedback_hint(
    console_out: Console | None = None,
    cfg_path: Path | None = None,
) -> bool:
    """Display a one-time polite feedback hint after a run, respecting user settings.

    Returns True if hint was displayed, False otherwise.
    """
    if os.getenv("OCTOFLOW_NO_FEEDBACK_PROMPT") == "1":
        return False
    if os.getenv("OCTOFLOW_NONINTERACTIVE") == "1":
        return False
    if not sys.stdout.isatty():
        return False

    out = console_out or console
    cfg_file = cfg_path or get_default_config_path()

    try:
        settings = load_settings(cfg_path=cfg_file)
    except Exception:
        return False

    # Check settings flags
    if not getattr(settings.ui, "show_feedback_prompt", True):
        return False
    if getattr(settings, "feedback_prompted", False):
        return False

    bullet_sym = glyph("BULLET")
    out.print(
        f"\n[dim]{bullet_sym} Did this work? Run '[bold cyan]octoflow feedback[/bold cyan]' "
        "to share feedback or report issues (voluntary, zero telemetry).[/dim]\n"
    )

    try:
        settings.feedback_prompted = True
        save_settings(settings, cfg_path=cfg_file)
        return True
    except Exception:
        return False


def feedback_cli_cmd(
    category: str = typer.Option(
        "feedback",
        "--category",
        "-c",
        help="Feedback category: 'feedback', 'bug', 'idea', 'show-and-tell'",
    ),
    title: str | None = typer.Option(None, "--title", "-t", help="Optional custom title"),
    diagnostics: bool | None = typer.Option(
        None,
        "--diagnostics/--no-diagnostics",
        "-d/-D",
        help="Attach sanitized environment diagnostics from octoflow bugreport",
    ),
    browser: bool = typer.Option(
        True,
        "--browser/--no-browser",
        help="Open prefilled URL in system browser",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview prefilled issue URL without opening browser",
    ),
    workspace: str = typer.Option(
        ".",
        "--dir",
        "-w",
        help="Workspace directory for diagnostics",
    ),
) -> None:
    """Open or print a prefilled voluntary feedback URL (zero background telemetry)."""
    bullet_sym = glyph("BULLET")
    cat_clean = category.strip().lower()

    # 1. Determine whether to attach sanitized diagnostics
    attach_diags = False
    if diagnostics is True:
        attach_diags = True
    elif diagnostics is None:
        if sys.stdin.isatty() and os.getenv("OCTOFLOW_NONINTERACTIVE") != "1":
            attach_diags = Confirm.ask(
                "Would you like to include sanitized diagnostics from 'octoflow bugreport'?",
                default=False,
            )

    diag_text = ""
    if attach_diags:
        raw_diag = generate_bugreport_text(workspace=workspace)
        if sys.stdin.isatty() and os.getenv("OCTOFLOW_NONINTERACTIVE") != "1" and not dry_run:
            console.print(
                Panel(
                    raw_diag,
                    title=f"{bullet_sym} Sanitized Diagnostics Preview (Review before attaching)",
                    border_style="cyan",
                )
            )
            confirm_attach = Confirm.ask(
                "Attach this sanitized diagnostic summary to the feedback issue?",
                default=True,
            )
            if confirm_attach:
                diag_text = raw_diag
        else:
            diag_text = raw_diag

    # 2. Construct Issue / Discussion Parameters
    if cat_clean == "bug":
        issue_title = title or "[Bug]: "
        labels = ["bug", "needs-repro"]
        body_parts = [
            "### Description",
            "Please describe what happened, what was expected, and reproduction steps.",
            "",
        ]
        if diag_text:
            body_parts.extend(
                ["### Environment Diagnostics (Sanitized)", "```markdown", diag_text, "```"]
            )
        url = build_feedback_issue_url(title=issue_title, body="\n".join(body_parts), labels=labels)

    elif cat_clean in ("idea", "feature", "enhancement"):
        issue_title = title or "[Idea]: "
        labels = ["enhancement"]
        body_parts = [
            "### Proposal Summary",
            "What problem does this solve? How does it align with local-first, truthful swarm moats?",
            "",
        ]
        if diag_text:
            body_parts.extend(
                ["### Environment Diagnostics (Sanitized)", "```markdown", diag_text, "```"]
            )
        url = build_feedback_issue_url(title=issue_title, body="\n".join(body_parts), labels=labels)

    elif cat_clean == "show-and-tell":
        issue_title = title or "[Show and Tell]: "
        body_parts = [
            "### What I built with OctoFlow",
            "Share your project, custom specialist guild, or benchmark results with the community!",
            "",
        ]
        if diag_text:
            body_parts.extend(
                ["### Environment Diagnostics (Sanitized)", "```markdown", diag_text, "```"]
            )
        url = build_feedback_issue_url(
            title=issue_title,
            body="\n".join(body_parts),
            is_discussion=True,
            discussion_category="show-and-tell",
        )

    else:
        # Default: general qualitative feedback
        issue_title = title or "[Feedback]: "
        labels = ["feedback"]
        body_parts = [
            "### Experience Summary",
            "- What worked smoothly?",
            "- What was confusing, unexpected, or slow?",
            "",
        ]
        if diag_text:
            body_parts.extend(
                ["### Environment Diagnostics (Sanitized)", "```markdown", diag_text, "```"]
            )
        url = build_feedback_issue_url(title=issue_title, body="\n".join(body_parts), labels=labels)

    # 3. Print Information
    diamond_sym = glyph("DIAMOND")
    check_sym = glyph("CHECK")
    console.print(f"\n{diamond_sym} [bold cyan]OctoFlow Voluntary Feedback[/bold cyan]")
    console.print(
        "[dim]OctoFlow contains zero background telemetry. Feedback is submitted manually by you.[/dim]\n"
    )
    console.print(
        f"{bullet_sym} [bold]Prefilled Feedback URL:[/bold]\n  [cyan underline]{url}[/cyan underline]\n"
    )

    if dry_run or not browser:
        return

    # 4. Open in browser if requested
    can_prompt = sys.stdin.isatty() and os.getenv("OCTOFLOW_NONINTERACTIVE") != "1"
    open_now = True
    if can_prompt:
        open_now = Confirm.ask("Open this URL in your default browser?", default=True)

    if open_now:
        try:
            import webbrowser

            webbrowser.open(url)
            console.print(f"[{check_sym}] Opened browser to GitHub feedback form.")
        except Exception as e:
            console.print(f"[dim]Could not open browser automatically: {e}[/dim]")
            console.print("[dim]Please copy and paste the URL above into your browser.[/dim]")


def register(app: typer.Typer, octos_app: typer.Typer) -> None:
    """Register feedback command with Typer CLI apps."""
    app.command("feedback")(feedback_cli_cmd)
    octos_app.command("feedback")(feedback_cli_cmd)
