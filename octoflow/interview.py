"""Pre-Flight Architect Interview & Interactive Requirement Clarification (P13.2).

Detects architectural branch points in high-level swarm goals (e.g. database choice,
frontend framework, authentication strategy) and presents rapid multiple-choice
terminal prompts with recommended defaults so developers can steer the project.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@dataclass
class InterviewQuestion:
    """An architectural question presented to the developer before swarm deployment."""

    id: str
    question: str
    category: str  # "database" | "frontend" | "auth" | "api" | "testing"
    options: list[str]
    default_index: int = 0
    help_text: str = ""

    @property
    def default_value(self) -> str:
        if 0 <= self.default_index < len(self.options):
            return self.options[self.default_index]
        return self.options[0] if self.options else ""


@dataclass
class ProjectConsortiumBlueprint:
    """Blueprint detailing detected project topology, assigned guild, and deployed octopuses."""

    project_type: str
    guild_id: str
    scale_tier: str  # "SOLO (8 Arms)" | "TRIAD (24 Arms)" | "OCTOPOLIS (64 Arms)" | "MONOREPO"
    octopus_count: int
    octopuses: list[dict[str, Any]] = field(default_factory=list)
    detected_frameworks: list[str] = field(default_factory=list)
    is_monorepo: bool = False


def detect_project_consortium(workspace: str = ".", objective: str = "") -> ProjectConsortiumBlueprint:
    """Inspect workspace directory and objective to determine optimal consortium topology and guild."""
    from pathlib import Path

    from octoflow.config import SwarmMorphology
    from octoflow.consortium import (
        detect_morphology_from_objective,
        get_consortium_guilds,
    )
    from octoflow.monorepo import scan_monorepo_topology

    ws = Path(workspace).resolve()
    obj_lower = objective.lower()

    # 1. Check monorepo topology
    mono = scan_monorepo_topology(str(ws))
    detected_frameworks: list[str] = []

    # Check common manifests for framework signals
    has_pkg_json = (ws / "package.json").exists()
    has_pyproject = (ws / "pyproject.toml").exists() or (ws / "requirements.txt").exists()
    has_cargo = (ws / "Cargo.toml").exists()
    has_docker = (ws / "Dockerfile").exists() or (ws / "docker-compose.yml").exists()
    has_mobile = (ws / "ios").is_dir() or (ws / "android").is_dir() or (ws / "pubspec.yaml").exists()

    if has_pkg_json:
        detected_frameworks.append("Node/npm")
    if has_pyproject:
        detected_frameworks.append("Python")
    if has_cargo:
        detected_frameworks.append("Rust")
    if has_docker:
        detected_frameworks.append("Docker")
    if has_mobile:
        detected_frameworks.append("Mobile")

    # 2. Determine Scale Tier and Octopus Count
    if mono.get("is_monorepo") and mono.get("package_count", 0) >= 2:
        pkg_count = min(8, max(2, mono["package_count"]))
        packages = mono.get("packages", [])
        octo_list = []
        for idx, pkg in enumerate(packages[:pkg_count]):
            octo_list.append(
                {
                    "octopus_id": idx,
                    "name": pkg["name"],
                    "title": f"Package: {pkg['name']}",
                    "description": f"Dedicated swarm for {pkg['rel_path']} ({pkg['type']})",
                    "color_hex": "#3B82F6" if pkg["type"] == "backend" else "#EC4899",
                    "focus_domain": pkg["type"],
                }
            )
        return ProjectConsortiumBlueprint(
            project_type=f"Multi-Package Monorepo ({len(packages)} packages)",
            guild_id="software_dev",
            scale_tier=f"MONOREPO ({pkg_count * 8} Arms)",
            octopus_count=pkg_count,
            octopuses=octo_list,
            detected_frameworks=detected_frameworks,
            is_monorepo=True,
        )

    # 3. Domain determination
    morphology = detect_morphology_from_objective(objective)

    if has_cargo or "rust" in obj_lower or "c++" in obj_lower or "embedded" in obj_lower:
        guild_id = "systems_embedded"
        project_type = "Low-Level Systems & Embedded (Rust/C++)"
        count = 1
    elif has_mobile or "ios" in obj_lower or "android" in obj_lower or "flutter" in obj_lower:
        guild_id = "mobile_apps"
        project_type = "Mobile Application (iOS/Android/Cross-Platform)"
        count = 1
    elif morphology == SwarmMorphology.AIML_RESEARCH:
        guild_id = "aiml_research"
        project_type = "AI/ML Research & Model Training Pipeline"
        count = 1
    elif morphology == SwarmMorphology.FULLSTACK_AI or "fullstack" in obj_lower or (has_pkg_json and has_pyproject):
        guild_id = "web_fullstack"
        project_type = "Full-Stack Application (Frontend + Backend + Database)"
        count = 3
    else:
        # Check scale from objective keywords
        is_large = any(k in obj_lower for k in ["enterprise", "microservices", "large", "distributed", "suite"])
        is_fullstack = any(k in obj_lower for k in ["fullstack", "full-stack", "dashboard", "fastapi and react", "api and ui"])
        if is_large:
            count = 8
            project_type = "Enterprise Cephalopod System (Octopolis)"
        elif is_fullstack:
            count = 3
            project_type = "Full-Stack Web Application (The Triad)"
        else:
            count = 1
            project_type = "Targeted Module / Software Service (Solo)"
        guild_id = "software_dev"

    # Get guild configurations for each octopus
    octo_configs = get_consortium_guilds(morphology, count)
    octo_list = [
        {
            "octopus_id": cfg.octopus_id,
            "name": cfg.name,
            "title": cfg.title,
            "description": cfg.description,
            "color_hex": cfg.color_hex,
            "focus_domain": cfg.focus_domain,
        }
        for cfg in octo_configs
    ]

    tier_name = (
        "SOLO (8 Arms)"
        if count == 1
        else ("TRIAD (24 Arms)" if count == 3 else f"OCTOPOLIS ({count * 8} Arms)")
    )

    return ProjectConsortiumBlueprint(
        project_type=project_type,
        guild_id=guild_id,
        scale_tier=tier_name,
        octopus_count=count,
        octopuses=octo_list,
        detected_frameworks=detected_frameworks,
        is_monorepo=False,
    )


def generate_architect_interview(
    objective: str, blueprint: ProjectConsortiumBlueprint | None = None
) -> list[InterviewQuestion]:
    """Generate 1-3 targeted pre-flight clarification questions based on goal branch points."""
    text = objective.lower()
    questions: list[InterviewQuestion] = []

    # 1. Database choice
    needs_db = any(
        kw in text
        for kw in [
            "database", "db", "models", "store", "persist", "sqlite", "postgres",
            "sql", "notes", "users", "auth", "crud", "todo", "posts", "items", "entities", "data"
        ]
    )
    if needs_db:
        questions.append(
            InterviewQuestion(
                id="database",
                category="database",
                question="Database Engine & Storage",
                options=[
                    "SQLite (Zero-config local file storage)",
                    "PostgreSQL (Relational client via asyncpg/psycopg)",
                    "In-Memory / JSON File persistence",
                ],
                default_index=0,
                help_text="SQLite is fast, zero-setup, and runs completely locally.",
            )
        )

    # 2. Frontend framework
    needs_ui = any(
        kw in text
        for kw in [
            "frontend", "ui", "react", "vue", "next", "vite", "web", "dashboard",
            "html", "views", "interface", "app", "pages", "client"
        ]
    )
    if needs_ui:
        questions.append(
            InterviewQuestion(
                id="frontend",
                category="frontend",
                question="Frontend Architecture & Styling",
                options=[
                    "React + Vite + Tailwind CSS (Fast, modern component UI)",
                    "Vanilla HTML5 + Modern CSS (Zero bundler dependencies)",
                    "Next.js / SSR Framework",
                ],
                default_index=0,
                help_text="React + Vite enables immediate live hot-reloading with Phase 4 Live Ignition.",
            )
        )

    # 3. Authentication mechanism
    needs_auth = any(
        kw in text
        for kw in [
            "auth", "login", "jwt", "tokens", "session", "user", "password", "oauth",
            "signup", "rbac", "permissions", "protected"
        ]
    )
    if needs_auth:
        questions.append(
            InterviewQuestion(
                id="auth",
                category="auth",
                question="Authentication & Security Mechanism",
                options=[
                    "JWT Bearer Tokens (Stateless, OpenAPI/Swagger compatible)",
                    "Session Cookies (HTTP-only secure browser cookies)",
                    "Basic API Key header validation",
                ],
                default_index=0,
                help_text="JWT tokens work seamlessly across mobile, web, and curl API clients.",
            )
        )

    return questions


def render_blueprint_panel(blueprint: ProjectConsortiumBlueprint, theme: Any = None) -> Panel:
    """Render a rich terminal panel showcasing the detected project and deployed octopuses."""
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(style="bold cyan", width=22)
    table.add_column(style="white")

    table.add_row("◈ PROJECT TOPOLOGY", f"[bold white]{blueprint.project_type}[/bold white]")
    table.add_row("◈ SWARM DEPLOYMENT", f"[bold green]{blueprint.octopus_count} Octopuses[/bold green]  [dim]({blueprint.scale_tier})[/dim]")
    table.add_row("◈ SPECIALIST GUILD", f"[cyan]{blueprint.guild_id}[/cyan]")
    if blueprint.detected_frameworks:
        table.add_row("◈ DETECTED STACK", ", ".join(blueprint.detected_frameworks))

    table.add_row("", "")
    table.add_row("[dim]Active Cephalopod Consortium:[/dim]", "")

    for octo in blueprint.octopuses:
        o_id = octo["octopus_id"]
        o_title = octo.get("title", f"Octopus {o_id}")
        o_desc = octo.get("description", "")
        table.add_row(
            f"  [bold cyan]● Octopus {o_id}:[/bold cyan]",
            f"[bold white]{o_title}[/bold white]  [dim]— {o_desc}[/dim]",
        )

    title = "[bold cyan]◈ OctoFlow Consortium Blueprint[/bold cyan]"
    return Panel(table, title=title, border_style="cyan", padding=(1, 2))


def conduct_architect_interview(
    questions: list[InterviewQuestion],
    console: Console | None = None,
    non_interactive: bool = False,
) -> dict[str, str]:
    """Conduct the interactive multiple-choice architect interview in the terminal."""
    c = console or Console()
    answers: dict[str, str] = {}

    if not questions:
        return answers

    if non_interactive or not (sys.stdin.isatty() and sys.stdout.isatty()):
        # Auto-pick defaults in non-interactive/test environments
        for q in questions:
            answers[q.id] = q.default_value.split(" (")[0]
        return answers

    c.print(
        f"\n[bold cyan]◈ The Swarm Architect has {len(questions)} quick design choices before deploying:[/bold cyan]"
    )
    c.print("[dim]Press [Enter] to accept the recommended default, or choose an option number.[/dim]\n")

    for idx, q in enumerate(questions, 1):
        c.print(f"[bold white]{idx}. {q.question}:[/bold white]")
        for opt_idx, opt in enumerate(q.options, 1):
            is_def = opt_idx - 1 == q.default_index
            tag = " [bold green][Default][/bold green]" if is_def else ""
            c.print(f"   [cyan][{opt_idx}][/cyan] {opt}{tag}")

        default_num = q.default_index + 1
        prompt_label = f"   [dim]Choice [1-{len(q.options)}, default: {default_num}]: [/dim]"
        c.print(prompt_label, end="")

        try:
            raw = sys.stdin.readline().strip()
        except (KeyboardInterrupt, EOFError):
            raw = ""

        if not raw:
            chosen_opt = q.default_value
        elif raw.isdigit() and 1 <= int(raw) <= len(q.options):
            chosen_opt = q.options[int(raw) - 1]
        else:
            chosen_opt = raw

        clean_choice = chosen_opt.split(" (")[0]
        answers[q.id] = clean_choice
        c.print(f"   [bold green]✔ Locked in:[/] {clean_choice}\n")

    return answers


def format_interview_constraints(decisions: dict[str, str]) -> str:
    """Format architectural decisions into an explicit constraint string for LLM prompts."""
    if not decisions:
        return ""
    items = [f"{k.capitalize()}: {v}" for k, v in decisions.items()]
    return "Architectural Constraints: " + "; ".join(items)
