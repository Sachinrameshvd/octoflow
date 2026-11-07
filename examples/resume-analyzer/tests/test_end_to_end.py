
import pytest
from app import app
from models import ResumeData
from parser import parse_resume
from scoring import compute_score
from skills import normalize_skill, categorize_skills

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
    sample_resume = parse_resume('samples/synthetic_resume_1.txt')
    response = client.post('/analyze', json=sample_resume)
    assert response.status_code == 200
    assert 'score' in response.json
    assert 'skills' in response.json

def test_skill_normalization():
    skill = 'Python'
    normalized_skill = normalize_skill(skill)
    assert normalized_skill == 'python'

def test_skill_categorization():
    skill = 'Python'
    category = categorize_skills(skill)
    assert category == 'programming'

def test_score_computation():
    resume_data = ResumeData(
        name='John Doe',
        email='john.doe@example.com',
        phone='123-456-7890',
        skills=['Python', 'Django', 'Flask']
    )
    score = compute_score(resume_data)
    assert score >= 0
