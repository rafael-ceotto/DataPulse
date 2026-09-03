import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

AUTH_URL = "/api/v1/auth/token"


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac


@pytest.fixture(scope="session")
async def auth_token(client):
    response = await client.post(
        AUTH_URL,
        data={"username": "admin", "password": "datapulse2024"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_list_pipeline_runs_requires_auth(client):
    response = await client.get("/api/v1/pipeline/runs")
    assert response.status_code == 401


async def test_list_pipeline_runs(client, auth_token):
    response = await client.get(
        "/api/v1/pipeline/runs",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_list_pipeline_runs_limit(client, auth_token):
    response = await client.get(
        "/api/v1/pipeline/runs?limit=5",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


async def test_pipeline_run_fields(client, auth_token):
    response = await client.get(
        "/api/v1/pipeline/runs?limit=1",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
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