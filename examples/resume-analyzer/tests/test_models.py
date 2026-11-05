"""Unit tests for Resume Analyzer data models."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure parent example directory is on sys.path
example_root = Path(__file__).resolve().parent.parent
if str(example_root) not in sys.path:
    sys.path.insert(0, str(example_root))

from models import ATSScoreResult, JobDescription, ResumeData


def test_resume_data_defaults():
    resume = ResumeData(raw_text="Experienced engineer skilled in Python and Docker.")
    assert resume.raw_text == "Experienced engineer skilled in Python and Docker."
    assert resume.name is None
    assert resume.skills == []
    assert resume.experience_years == 0.0
    assert resume.sections == {}


def test_resume_data_with_fields():
    resume = ResumeData(
        raw_text="Jane Doe\nEmail: jane@example.com\nSkills: Python, Go",
        name="Jane Doe",
        email="jane@example.com",
        phone="555-0199",
        skills=["Python", "Go"],
        experience_years=4.5,
        sections={"skills": "Python, Go"},
    )
    assert resume.name == "Jane Doe"
    assert resume.email == "jane@example.com"
    assert resume.skills == ["Python", "Go"]
    assert resume.experience_years == 4.5
    assert "skills" in resume.sections


def test_job_description_validation():
    jd = JobDescription(
        raw_text="Looking for a Senior Python Developer with Kubernetes experience.",
        title="Senior Python Developer",
        required_skills=["Python", "Kubernetes", "PostgreSQL"],
        min_years_experience=5.0,
    )
    assert jd.title == "Senior Python Developer"
    assert len(jd.required_skills) == 3
    assert jd.min_years_experience == 5.0


def test_ats_score_result_bounds():
    result = ATSScoreResult(
        overall_score=85.5,
        keyword_match_score=90.0,
        experience_score=80.0,
        format_score=85.0,
        matching_keywords=["python", "fastapi"],
        missing_critical_keywords=["redis"],
        suggestions=["Add Redis"],
        summary="Good match",
    )
    assert 0.0 <= result.overall_score <= 100.0
    assert result.matching_keywords == ["python", "fastapi"]
    assert result.missing_critical_keywords == ["redis"]
