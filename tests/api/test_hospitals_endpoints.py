import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_list_hospitals(client):
    response = await client.get("/api/v1/hospitals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 20


async def test_list_hospitals_filter_by_state(client):
    response = await client.get("/api/v1/hospitals?state=AL")
    assert response.status_code == 200
    data = response.json()
    if data:
        assert all(h["state"] == "AL" for h in data)


async def test_get_hospital_by_id(client):
    response = await client.get("/api/v1/hospitals?limit=1")
    assert response.status_code == 200
    data = response.json()

    if data:
        facility_id = data[0]["facility_id"]
        response = await client.get(f"/api/v1/hospitals/{facility_id}")
        assert response.status_code == 200
        assert response.json()["facility_id"] == facility_id
    else:
        pytest.skip("No hospitals in database")


async def test_get_hospital_not_found(client):
    response = await client.get("/api/v1/hospitals/999999")
    assert response.status_code == 404