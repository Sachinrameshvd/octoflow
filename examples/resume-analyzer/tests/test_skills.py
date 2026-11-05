"""Unit tests for skills taxonomy, alias normalization, and gap analysis."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure parent example directory is on sys.path
example_root = Path(__file__).resolve().parent.parent
if str(example_root) not in sys.path:
    sys.path.insert(0, str(example_root))

from skills import (
    SkillsTaxonomy,
    categorize_skills,
    identify_competencies,
    normalize_skill,
)


def test_normalize_synonyms():
    assert normalize_skill("golang") == "go"
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("postgres") == "postgresql"
    assert normalize_skill("js") == "javascript"
    assert normalize_skill("Python") == "python"


def test_categorize_skills():
    skills = ["Python", "Golang", "FastAPI", "React", "AWS", "Postgres", "Docker"]
    categorized = categorize_skills(skills)
    assert "languages" in categorized
    assert "backend" in categorized
    assert "frontend" in categorized
    assert "cloud" in categorized
    assert "devops" in categorized
    assert "go" in categorized["languages"]
    assert "python" in categorized["languages"]
    assert "fastapi" in categorized["backend"]
    assert "react" in categorized["frontend"]
    assert "postgresql" in categorized.get("data", []) or "postgresql" in categorized.get("languages", []) or "postgresql" in categorized.get("backend", [])


def test_identify_competencies():
    resume_skills = ["Python", "K8s", "Docker", "FastAPI"]
    required_skills = ["python", "kubernetes", "fastapi", "terraform", "redis"]

    result = identify_competencies(resume_skills, required_skills)
    assert "matched" in result
    assert "missing" in result
    assert "coverage_pct" in result
    # Synonym resolution: 'K8s' matches 'kubernetes'
    assert "kubernetes" in result["matched"]
    assert "python" in result["matched"]
    assert "fastapi" in result["matched"]
    assert "terraform" in result["missing"]
    assert "redis" in result["missing"]
    assert result["coverage_pct"] == 60.0  # 3 of 5
