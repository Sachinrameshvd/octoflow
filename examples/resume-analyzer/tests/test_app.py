
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_upload_resume():
    with open('tests/resume.pdf', 'rb') as file:
        response = client.post('/upload', files={'file': file})
        assert response.status_code == 200
        assert 'score' in response.json()

def test_input_job_description():
    response = client.post('/score', json={'job_description': 'Python developer'})
    assert response.status_code == 200
    assert 'score' in response.json()

def test_dark_mode():
    response = client.get('/dark-mode')
    assert response.status_code == 200
    assert 'dark-mode' in response.text

def test_keyboard_accessibility():
    response = client.get('/keyboard-accessibility')
    assert response.status_code == 200
    assert 'keyboard-accessible' in response.text
  