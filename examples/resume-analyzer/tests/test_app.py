"""Integration tests for FastAPI endpoints (/health, /api/analyze)."""

from __future__ import annotations

import io
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Ensure parent example directory is on sys.path
example_root = Path(__file__).resolve().parent.parent
if str(example_root) not in sys.path:
    sys.path.insert(0, str(example_root))

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def make_test_pdf_bytes(name: str = "Morgan Lee") -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, name)
    c.drawString(100, 730, "Email: morgan@example.com | Phone: 415-555-0199")
    c.drawString(100, 700, "Experience")
    c.drawString(100, 680, "Staff Engineer at CloudCorp (2018 - Present)")
    c.drawString(100, 660, "Scaled distributed systems with Python, FastAPI, Docker, and AWS.")
    c.drawString(100, 630, "Education")
    c.drawString(100, 610, "B.S. in Computer Science")
    c.drawString(100, 580, "Skills")
    c.drawString(100, 560, "Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis")
    c.drawString(100, 530, "Projects")
    c.drawString(100, 510, "Event streaming engine processing 100k events/sec.")
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "resume-analyzer"


def test_analyze_endpoint_pdf_upload(client, tmp_path):
    pdf_bytes = make_test_pdf_bytes("Morgan Lee")

    # Record directory state before upload
    before_files = list(tmp_path.iterdir())

    response = client.post(
        "/api/analyze",
        files={"file": ("morgan_resume.pdf", pdf_bytes, "application/pdf")},
        data={
            "job_description": "We need a Staff Engineer skilled in Python, FastAPI, Docker, and Kubernetes.",
            "title": "Staff Engineer",
            "required_skills_csv": "python, fastapi, docker, kubernetes",
            "min_years_experience": "4.0",
        },
    )

    # Assert no uploaded file was persisted to disk
    after_files = list(tmp_path.iterdir())
    assert before_files == after_files

    assert response.status_code == 200
    res = response.json()
    assert "candidate" in res
    assert "score" in res
    assert "skills_analysis" in res
    assert res["candidate"]["name"] == "Morgan Lee"
    assert res["score"]["overall_score"] >= 70.0
    assert "python" in res["score"]["matching_keywords"]
    assert "docker" in res["score"]["matching_keywords"]


def test_analyze_endpoint_json_payload(client):
    payload = {
        "resume_text": "Experienced Python Developer with 3+ years experience skilled in Django, PostgreSQL, and AWS.\nExperience\nSoftware Engineer at Startup (2021 - Present)\nEducation\nBS Computer Science\nSkills\nPython, Django, PostgreSQL, AWS",
        "job_description": "Seeking Python Developer with Django and PostgreSQL.",
        "title": "Python Developer",
        "required_skills": ["python", "django", "postgresql"],
        "min_years_experience": 2.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["score"]["overall_score"] >= 60.0
    assert "python" in res["score"]["matching_keywords"]
    assert "django" in res["score"]["matching_keywords"]


def test_analyze_endpoint_empty_bad_request(client):
    response = client.post("/api/analyze", data={})
    assert response.status_code == 400
    assert "Must provide either" in response.json()["detail"]


def test_dashboard_root_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
