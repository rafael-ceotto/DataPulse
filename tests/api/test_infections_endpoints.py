import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac 
    
async def test_list_infections(client):
    response = await client.get("/api/v1/infections")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
async def test_list_infections_filter_by_state(client):
    response = await client.get("/api/v1/infections?state=AL")
    assert response.status_code == 200
    data = response.json()
    assert all(i["state"] == "AL" for i in data if data)
    
async def test_get_facility_infections(client):
    response = await client.get("/api/v1/infections")
    assert response.status_code == 200
    data = response.json()
    if data:
        facility_id = data[0]["facility_id"]
        response = await client.get(f"/api/v1/infections/{facility_id}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    else:
        pytest.skip("No infections in database")

async def test_get_facility_infections_not_found(client):
    response = await client.get("/api/v1/infections/FACILITY_DOES_NOT_EXIST")
    assert response.status_code == 404

