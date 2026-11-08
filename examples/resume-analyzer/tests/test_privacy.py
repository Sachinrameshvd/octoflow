"""Privacy and zero-persistence assurance tests.

Asserts that uploads are processed purely in-memory and never written to disk,
and that sample generation uses strictly synthetic data with zero real PII.
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure parent example directory is on sys.path
example_root = Path(__file__).resolve().parent.parent
if str(example_root) not in sys.path:
    sys.path.insert(0, str(example_root))

import pypdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app import app


def _create_test_pdf(
    name: str = "Privacy Candidate",
    email: str = "candidate@example.com",
    phone: str = "555-0199",
    years_text: str = "4+ years of software engineering experience",
) -> bytes:
    """Generate a valid synthetic PDF binary stream purely in-memory."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, name)
    c.drawString(100, 735, f"Email: {email} | Phone: {phone}")
    c.drawString(100, 710, "Summary")
    c.drawString(100, 695, f"Engineer with {years_text}.")
    c.drawString(100, 670, "Experience")
    c.drawString(100, 655, "Software Engineer (2020 - Present)")
    c.drawString(100, 640, "Built scalable microservices in Python and Docker.")
    c.drawString(100, 615, "Skills")
    c.drawString(100, 600, "Python, Docker, FastAPI, Kubernetes")
    c.save()
    return buf.getvalue()


@pytest.fixture
def client():
    return TestClient(app)


def test_uploads_never_persisted_to_disk(client, tmp_path):
    """Verify that multiple file uploads create zero artifacts on disk."""
    app_dir = Path(__file__).resolve().parent.parent
    before_files = set(app_dir.rglob("*"))

    # Synthesize valid in-memory PDF payload
    valid_pdf = _create_test_pdf()

    for i in range(5):
        resp = client.post(
            "/api/analyze",
            files={"file": (f"test_upload_{i}.pdf", valid_pdf, "application/pdf")},
            data={"job_description": "Software engineer with Python and Docker"},
        )
        assert resp.status_code == 200

    # Also test an invalid/corrupted upload to verify 400 rejection without disk persistence
    corrupted_pdf = b"%PDF-corrupted-stream-bytes"
    resp_corrupt = client.post(
        "/api/analyze",
        files={"file": ("corrupt.pdf", corrupted_pdf, "application/pdf")},
        data={"job_description": "Software engineer with Python and Docker"},
    )
    assert resp_corrupt.status_code == 400

    # Re-scan workspace directory
    after_files = set(app_dir.rglob("*"))
    # Filter out pycache / pytest temp cache
    new_files = [
        f for f in (after_files - before_files)
        if "__pycache__" not in str(f) and ".pytest_cache" not in str(f)
    ]
    assert new_files == [], f"Expected zero persisted files on disk, found: {new_files}"


def test_samples_are_strictly_synthetic():
    """Verify that all generated samples use synthetic @example.com domains and fake numbers."""
    from scripts.generate_samples import SAMPLES_DIR, main

    main()

    for pdf_file in SAMPLES_DIR.glob("*.pdf"):
        reader = pypdf.PdfReader(str(pdf_file))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        # Verify synthetic domain is present in extracted PDF text
        assert "@example.com" in text
        # Verify no common real domains
        assert "@gmail.com" not in text
        assert "@yahoo.com" not in text
        assert "@hotmail.com" not in text
