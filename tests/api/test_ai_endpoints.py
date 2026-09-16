import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app

AUTH_URL = "/api/v1/auth/token"
AI_URL = "/api/v1/ai/query"


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


async def test_ai_query_requires_auth(client):
    response = await client.post(AI_URL, json={"question": "Which hospitals have 5 stars?"})
    assert response.status_code == 401


async def test_ai_query_success(client, auth_token):
    with patch("app.api.hospital_router.ask_agent", new=AsyncMock(return_value={})):
        with patch("app.api.hospital_router.publish_query", new=AsyncMock(return_value=True)):
            with patch("app.api.hospital_router.create_job", new=AsyncMock(return_value=None)):
                response = await client.post(
                    AI_URL,
                    json={"question": "Which hospitals have 5 stars?"},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


async def test_ai_query_empty_question(client, auth_token):
    with patch("app.api.hospital_router.publish_query", new=AsyncMock(return_value=True)):
        with patch("app.api.hospital_router.create_job", new=AsyncMock(return_value=None)):
            response = await client.post(
                AI_URL,
                json={"question": ""},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data