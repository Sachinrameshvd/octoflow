import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_no_pii_uploaded(client):
    # Assuming the API endpoint for analysis is /analyze
    response = client.post('/analyze', json={"resume": "non-PII content"})
    assert response.status_code == 200
    assert 'uploads' not in response.json