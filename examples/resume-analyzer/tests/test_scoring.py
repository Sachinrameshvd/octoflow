"""Unit tests for ATS scoring heuristics and weight computations."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure parent example directory is on sys.path
example_root = Path(__file__).resolve().parent.parent
if str(example_root) not in sys.path:
    sys.path.insert(0, str(example_root))

from models import ATSScoreResult, JobDescription, ResumeData
from scoring import compute_score


@pytest.fixture
def sample_resume():
    return ResumeData(
        raw_text="""
        Jane Doe
        Email: jane.doe@example.com
        Experience
        Senior Software Engineer at TechCorp. Built scalable microservices in Python, FastAPI, and Docker.
        Education
        B.S. in Computer Science
        Skills
        Python, FastAPI, Docker, PostgreSQL, Git, CI/CD
        Projects
        Distributed cache system using Redis.
        """,
        name="Jane Doe",
        email="jane.doe@example.com",
        skills=["python", "fastapi", "docker", "postgresql", "git"],
        experience_years=5.0,
        sections={
            "experience": "Senior Software Engineer...",
            "education": "B.S. in Computer Science",
            "skills": "Python, FastAPI, Docker...",
            "projects": "Distributed cache...",
        },
    )


@pytest.fixture
def sample_jd():
    return JobDescription(
        raw_text="Seeking Senior Backend Engineer proficient in Python, FastAPI, Docker, and Kubernetes.",
        title="Senior Backend Engineer",
        required_skills=["python", "fastapi", "docker", "kubernetes"],
        min_years_experience=4.0,
    )


def test_scoring_high_match(sample_resume, sample_jd):
    result = compute_score(sample_resume, sample_jd)
    assert isinstance(result, ATSScoreResult)
    assert 0.0 <= result.overall_score <= 100.0
    assert "python" in result.matching_keywords
    assert "fastapi" in result.matching_keywords
    assert "docker" in result.matching_keywords
    assert "kubernetes" in result.missing_critical_keywords
    assert result.experience_score == 100.0  # 5 yrs vs 4 yrs min
    assert result.format_score == 100.0  # all 4 sections present
    assert any("kubernetes" in s.lower() for s in result.suggestions)


def test_scoring_zero_experience_requirement():
    resume = ResumeData(raw_text="Junior developer skilled in Python.", experience_years=0.5)
    jd = JobDescription(raw_text="Junior Dev", required_skills=["python"], min_years_experience=0.0)
    result = compute_score(resume, jd)
    assert result.experience_score == 100.0
    assert result.overall_score > 50.0


def test_scoring_fallback_keywords():
    resume = ResumeData(raw_text="Rust and Golang developer with experience and education sections.")
    jd = JobDescription(raw_text="Looking for Rust Golang and Terraform specialists.")
    result = compute_score(resume, jd)
    assert "rust" in result.matching_keywords or "golang" in result.matching_keywords
    assert 0.0 <= result.overall_score <= 100.0
