from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'healthy'}

def test_analyze_endpoint_with_pdf():
    # Assuming you have a PDF file named 'test_resume.pdf' in the workspace
    with open('test_resume.pdf', 'rb') as file:
        response = client.post('/api/analyze', files={'file': file})
    assert response.status_code == 200

def test_analyze_endpoint_with_json():
    data = {
        'resume': 'John Doe, Software Engineer, Experience in Python, Flask, and FastAPI.'
    }
    response = client.post('/api/analyze', json=data)
    assert response.status_code == 200
