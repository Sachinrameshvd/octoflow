"""Tests verifying dashboard static asset serving and accessibility landmarks."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure parent example directory is on sys.path
example_root = Path(__file__).resolve().parent.parent
if str(example_root) not in sys.path:
    sys.path.insert(0, str(example_root))

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_dashboard_served_at_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    content = response.text
    assert "AI Resume & ATS Match Analyzer" in content
    assert "dropzone" in content
    assert "Run ATS Gauntlet Analysis" in content


def test_dashboard_static_files_served(client):
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "handleFileSelected" in response.text


def test_accessibility_landmarks_present(client):
    response = client.get("/")
    assert response.status_code == 200
    content = response.text
    # Accessibility assertions
    assert 'role="main"' in content
    assert 'aria-live="polite"' in content
    assert 'role="button"' in content
    assert 'aria-label=' in content
    assert 'tabindex="0"' in content

