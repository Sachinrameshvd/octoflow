import pytest
from octoflow.api import app
from octoflow.model import ResumeAnalyzer

@pytest.fixture
async def client():
    async with app.test_client() as client:
        yield client

async def test_analyze_resume(client):
    response = await client.post('/analyze', json={'resume': 'path/to/resume.pdf'})
    assert response.status_code == 200
    assert 'score' in response.json