import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app

AUTH_URL = "/api/v1/auth/token"
NOTION_URL = "/api/v1/notion/save"

@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac
        
@pytest.fixture(scope="session")
async def auth_token(client):
    response = await client.post(
        AUTH_URL,
        data={"username": "admin", "password": "datapulse2024"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

async def test_notion_save_required_auth(client):
    response = await client.post(
        NOTION_URL,
        json={
            "question": "Which hospitals have 5 stars?",
            "explanation": "Test explanation",
            "tools_used": [], 
        }
    )
    assert response.status_code == 401
    
async def test_notion_save_success(client, auth_token):
    with patch("app.api.hospital_router.save_to_notion", new=AsyncMock(return_value=True)):
        response = await client.post(
            NOTION_URL,
            json={
                "question": "Which hospitals have 5 stars?",
                "explanation": "Test explanation",
                "tools_used": ["get_top_rated_hospitals"], 
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Saved to Notion successfully"
        
async def test_notion_save_failure(client, auth_token):
     with patch("app.api.hospital_router.save_to_notion", new=AsyncMock(return_value=False)):
        response = await client.post(
            NOTION_URL,
            json={
                "question": "Which hospitals have 5 stars?",
                "explanation": "Test explanation",
                "tools_used": [],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 500