"""Unit tests for in-memory PDF extraction and resume section parsing."""

from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Ensure parent example directory is on sys.path
example_root = Path(__file__).resolve().parent.parent
if str(example_root) not in sys.path:
    sys.path.insert(0, str(example_root))

from models import ResumeData
from parser import (
    estimate_experience_years,
    extract_contact_info,
    extract_sections,
    extract_text_from_pdf,
    parse_resume,
)


def create_synthetic_pdf(
    name: str = "Alice Johnson",
    email: str = "alice.j@example.com",
    phone: str = "415-555-0142",
    years_text: str = "5+ years of software engineering experience",
) -> bytes:
    """Generate valid in-memory PDF binary stream without writing to disk."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, name)
    c.drawString(100, 735, f"Email: {email} | Phone: {phone}")
    c.drawString(100, 710, "Summary")
    c.drawString(100, 695, f"Full stack engineer with {years_text}.")
    c.drawString(100, 670, "Experience")
    c.drawString(100, 655, "Senior Developer at Acme Corp (2019 - Present)")
    c.drawString(100, 640, "Architected high-throughput APIs using Python, FastAPI, and Postgres.")
    c.drawString(100, 615, "Education")
    c.drawString(100, 600, "B.S. in Computer Engineering, State University, 2018")
    c.drawString(100, 575, "Skills")
    c.drawString(100, 560, "Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, CI/CD")
    c.drawString(100, 535, "Projects")
    c.drawString(100, 520, "Open-source distributed scheduler handling 50k events/sec.")
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def test_extract_text_from_pdf_bytes():
    pdf_bytes = create_synthetic_pdf()
    text = extract_text_from_pdf(pdf_bytes)
    assert "Alice Johnson" in text
    assert "alice.j@example.com" in text
    assert "Experience" in text
    assert "FastAPI" in text


def test_extract_text_from_pdf_stream():
    pdf_bytes = create_synthetic_pdf()
    stream = BytesIO(pdf_bytes)
    text = extract_text_from_pdf(stream)
    assert "Acme Corp" in text
    assert "Kubernetes" in text


def test_extract_contact_info():
    text = "Alice Johnson\nEmail: alice.j@example.com\nPhone: (415) 555-0142\nSan Francisco, CA"
    name, email, phone = extract_contact_info(text)
    assert name == "Alice Johnson"
    assert email == "alice.j@example.com"
    assert "415" in phone and "0142" in phone


def test_extract_sections():
    text = (
        "Alice Johnson\n"
        "Summary\nTalented engineer.\n"
        "Experience\nWorked 5 years at startup.\n"
        "Education\nBS CS 2018\n"
        "Skills\nPython, Go, Docker\n"
        "Projects\nBuilt search engine\n"
    )
    sections = extract_sections(text)
    assert "summary" in sections
    assert "experience" in sections
    assert "education" in sections
    assert "skills" in sections
    assert "projects" in sections


def test_estimate_experience_years():
    text1 = "Senior Engineer with 6+ years of professional backend experience."
    assert estimate_experience_years(text1) == 6.0

    text2 = "Software Engineer at Google (2018 - 2022)"
    assert estimate_experience_years(text2) == 4.0


def test_parse_resume_end_to_end_in_memory(tmp_path):
    pdf_bytes = create_synthetic_pdf()

    # Track directory state to prove zero disk writes
    initial_files = list(tmp_path.iterdir())

    resume_data = parse_resume(pdf_bytes)
    assert isinstance(resume_data, ResumeData)
    assert resume_data.name == "Alice Johnson"
    assert resume_data.email == "alice.j@example.com"
    assert "experience" in resume_data.sections
    assert resume_data.experience_years >= 5.0

    # Assert no new files were created on disk
    final_files = list(tmp_path.iterdir())
    assert initial_files == final_files
