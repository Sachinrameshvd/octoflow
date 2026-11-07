import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

@pytest.fixture
def test_resume_data():
    return {"resume": "path/to/resume.pdf", "job_description": "path/to/job_description.txt"}

@pytest.fixture
def test_job_description():
    return "path/to/job_description.txt"

def test_upload_resume(test_resume_data):
    response = client.post("/upload", json=test_resume_data)
    assert response.status_code == 200
    assert response.json().get("message") == "Resume uploaded successfully"

def test_display_score(test_resume_data):
    response = client.post("/score", json=test_resume_data)
    assert response.status_code == 200
    assert response.json().get("score") is not None

def test_display_badges(test_resume_data):
    response = client.post("/badges", json=test_resume_data)
    assert response.status_code == 200
    assert response.json().get("matched_skills") is not None
    assert response.json().get("missing_skills") is not None

def test_display_suggestions(test_resume_data):
    response = client.post("/suggestions", json=test_resume_data)
    assert response.status_code == 200
    assert response.json().get("suggestions") is not None

def test_dark_mode(test_resume_data):
    response = client.post("/dark_mode", json=test_resume_data)
    assert response.status_code == 200
    assert response.json().get("theme") == "dark"

def test_keyboard_accessible(test_resume_data):
    response = client.post("/keyboard", json=test_resume_data)
    assert response.status_code == 200
    assert response.json().get("accessible") is True