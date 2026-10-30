import pytest

octo_api = pytest.importorskip("octoflow.api", reason="octoflow.api not implemented")
app = getattr(octo_api, "app", None)
model_mod = pytest.importorskip("octoflow.model", reason="octoflow.model not implemented")
ResumeAnalyzer = getattr(model_mod, "ResumeAnalyzer", None)


@pytest.fixture
async def client():
    async with app.test_client() as client:
        yield client


async def test_analyze_resume(client):
    response = await client.post("/analyze", json={"resume": "path/to/resume.pdf"})
    assert response.status_code == 200
    assert "score" in response.json
