"""Automated unit test suite for AI Resume & ATS Match Analyzer."""

import pytest
resume_analyzer = pytest.importorskip("api.resume_analyzer", reason="AI Resume Analyzer app not in local pythonpath")
app = resume_analyzer.app
extract_skills = resume_analyzer.extract_skills
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)


def test_extract_skills():
    """Verify keyword and skill tokenizer extracts technical competencies."""
    sample_text = "Proficient in Python, FastAPI, Docker, and PostgreSQL with experience in AWS CI/CD pipelines."
    extracted = extract_skills(sample_text)
    assert "python" in extracted
    assert "fastapi" in extracted
    assert "docker" in extracted
    assert "postgresql" in extracted
    assert "aws" in extracted
    assert "ci/cd" in extracted


def test_api_sample_endpoint(client):
    """Verify /api/sample returns valid non-empty JD and Resume strings."""
    response = client.get("/api/sample")
    assert response.status_code == 200
    data = response.json()
    assert "job_description" in data
    assert "resume_text" in data
    assert len(data["job_description"]) > 50
    assert len(data["resume_text"]) > 50


def test_api_analyze_match_scoring(client):
    """Verify /api/analyze calculates accurate ATS score, keyword tags, and bullet rewrites."""
    payload = {
        "job_description": "We need Python, FastAPI, Docker, PostgreSQL, and Redis experience.",
        "resume_text": "Experienced software developer skilled in Python, Docker, and Redis."
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert 0 <= data["overall_match_score"] <= 100
    assert "python" in data["matching_keywords"]
    assert "docker" in data["matching_keywords"]
    assert "redis" in data["matching_keywords"]
    assert "fastapi" in data["missing_critical_keywords"]
    assert "postgresql" in data["missing_critical_keywords"]
    assert len(data["bullet_improvements"]) >= 1
    assert "executive_summary" in data


def test_index_dashboard_html(client):
    """Verify root / serves the cyber-dark interactive dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "ResumePulse" in response.text
    assert "ATS GAUNTLET" in response.text
    assert "Load Sample" in response.text
