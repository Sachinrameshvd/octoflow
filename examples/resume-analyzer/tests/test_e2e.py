import pytest
from app import app
from models import ResumeData
from scoring import compute_score

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'healthy'}

def test_analyze_endpoint(client):
    resume_data = ResumeData(title='Software Engineer', description='Experienced in Python and machine learning.')
    response = client.post('/analyze', json=resume_data.dict())
    assert response.status_code == 200
    assert 'score' in response.json

def test_compute_score_functionality():
    resume_data = ResumeData(title='Software Engineer', description='Experienced in Python and machine learning.')
    score = compute_score(resume_data)
    assert isinstance(score, float)
    assert score >= 0
    assert score <= 100