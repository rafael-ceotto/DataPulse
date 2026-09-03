import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac
        
async def test_list_pipeline_runs(client):
    response = await client.get("/api/v1/pipeline/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
async def test_list_pipeline_runs_limit(client):
    response = await client.get("api/v1/pipeline/runs?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    
async def test_pipeline_run_fields(client):
    response = await client.get("/api/v1/pipeline/runs?limit=1")
    assert response.status_code == 200
    data = response.json()
    if data:
        run = data[0]
        assert "id" in run
        assert "status" in run
        assert "records_processed" in run
        assert "avg_rating" in run
        assert "insight" in run
        assert "duration_seconds" in run