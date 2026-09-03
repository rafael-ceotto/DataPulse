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


async def test_export_hospitals_requires_auth(client):
    response = await client.get("/api/v1/hospitals/export?state=AL")
    assert response.status_code == 401


async def test_export_hospitals_by_state(client, auth_token):
    response = await client.get(
        "/api/v1/hospitals/export?state=AL",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert all(h["state"] == "AL" for h in data)


async def test_export_hospitals_missing_state(client, auth_token):
    response = await client.get(
        "/api/v1/hospitals/export",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 422


async def test_data_quality_requires_auth(client):
    response = await client.get("/api/v1/hospitals/data-quality")
    assert response.status_code == 401


async def test_data_quality(client, auth_token):
    response = await client.get(
        "/api/v1/hospitals/data-quality",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_hospitals" in data
    assert "rated_hospitals" in data
    assert "unrated_hospitals" in data
    assert "completeness_pct" in data
    assert "low_rated_hospitals" in data
    assert data["total_hospitals"] > 0
    assert data["completeness_pct"] >= 0