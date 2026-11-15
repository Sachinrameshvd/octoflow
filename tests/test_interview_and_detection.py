"""Tests for dynamic project consortium detection and pre-flight architect interview (Milestone 1).

Verifies:
1. Dynamic detection of project types (Solo, Triad, Octopolis, Monorepo)
2. Domain guild mapping (web_fullstack, aiml_research, systems_embedded, software_dev)
3. Pre-flight interview question generation for database, frontend, and auth
4. Interview constraint formatting
5. Non-interactive default fallback behavior
"""

import tempfile
from pathlib import Path

from octoflow.interview import (
    conduct_architect_interview,
    detect_project_consortium,
    format_interview_constraints,
    generate_architect_interview,
    render_blueprint_panel,
)
from rich.console import Console


def test_detect_project_consortium_solo_task():
    """Verify single targeted task is assigned 1 Solo Octopus (8 arms)."""
    with tempfile.TemporaryDirectory() as tmp:
        bp = detect_project_consortium(tmp, "Build a thread-safe sliding window rate limiter")
        assert bp.octopus_count == 1
        assert "8 Arms" in bp.scale_tier
        assert len(bp.octopuses) == 1
        assert bp.guild_id == "software_dev"


def test_detect_project_consortium_fullstack():
    """Verify fullstack objective deploys 3 Triad Octopuses (24 arms)."""
    with tempfile.TemporaryDirectory() as tmp:
        bp = detect_project_consortium(
            tmp, "Build a fullstack markdown notes app with FastAPI backend and React frontend"
        )
        assert bp.octopus_count == 3
        assert "24 Arms" in bp.scale_tier
        assert len(bp.octopuses) == 3
        assert bp.guild_id == "web_fullstack"


def test_detect_project_consortium_aiml():
    """Verify AI/ML model training goal selects aiml_research guild."""
    with tempfile.TemporaryDirectory() as tmp:
        bp = detect_project_consortium(
            tmp, "Train a PyTorch neural network model with loss epochs and dataset ETL"
        )
        assert bp.guild_id == "aiml_research"
        assert "AI/ML" in bp.project_type


def test_detect_project_consortium_systems():
    """Verify Cargo manifest selects systems_embedded guild."""
    with tempfile.TemporaryDirectory() as tmp:
        cargo = Path(tmp) / "Cargo.toml"
        cargo.write_text('[package]\nname = "my_crate"\nversion = "0.1.0"\n')
        bp = detect_project_consortium(tmp, "Implement high performance memory buffer parser")
        assert bp.guild_id == "systems_embedded"
        assert "Rust" in bp.project_type or "Embedded" in bp.project_type


def test_generate_interview_questions():
    """Verify architect interview detects database, frontend, and auth branch points."""
    goal = "Create a fullstack user authentication portal with dashboard and sqlite models"
    questions = generate_architect_interview(goal)

    cat_set = {q.category for q in questions}
    assert "database" in cat_set
    assert "frontend" in cat_set
    assert "auth" in cat_set


def test_format_interview_constraints():
    """Verify formatting of architectural decisions into prompt constraint string."""
    decisions = {
        "database": "SQLite",
        "frontend": "React + Vite",
        "auth": "JWT Bearer Tokens",
    }
    res = format_interview_constraints(decisions)
    assert "Database: SQLite" in res
    assert "Frontend: React + Vite" in res
    assert "Auth: JWT Bearer Tokens" in res


def test_conduct_architect_interview_non_interactive():
    """Verify non-interactive interview selects defaults cleanly."""
    goal = "Build user database"
    questions = generate_architect_interview(goal)
    assert len(questions) >= 1

    answers = conduct_architect_interview(questions, non_interactive=True)
    assert "database" in answers
    assert "SQLite" in answers["database"]


def test_render_blueprint_panel():
    """Verify blueprint panel renders cleanly into a Rich Panel without errors."""
    with tempfile.TemporaryDirectory() as tmp:
        bp = detect_project_consortium(tmp, "Build a fullstack web app")
        panel = render_blueprint_panel(bp)
        c = Console(width=100)
        with c.capture() as capture:
            c.print(panel)
        rendered = capture.get()
        assert "OctoFlow Consortium Blueprint" in rendered
        assert "Octopuses" in rendered

