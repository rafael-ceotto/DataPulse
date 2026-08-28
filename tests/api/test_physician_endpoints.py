import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac


async def test_list_physicians(client):
    response = await client.get("/api/v1/physicians")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "total" in data


async def test_list_physicians_filter_by_state(client):
    response = await client.get("/api/v1/physicians?state=OH&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert data.get("total", 0) >= 0


async def test_physician_state_analysis(client):
    response = await client.get("/api/v1/physicians/state-analysis/OH")
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "OH"
    assert "physician_count" in data
    assert "hospital_count" in data
    assert "avg_hospital_rating" in data
    assert "physicians_per_hospital" in data


async def test_physician_cache_status(client):
    response = await client.get("/api/v1/physicians/cache-status")
    assert response.status_code == 200
    data = response.json()
    assert "national_specialty_cache" in data