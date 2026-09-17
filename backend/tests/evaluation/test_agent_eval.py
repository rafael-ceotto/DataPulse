import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app

AUTH_URL = "/api/v1/auth/token"
AI_URL = "/api/v1/ai/query"

EVAL_CASES = [
    {
        "id": "english_5star",
        "question": "Which hospitals have a 5-star rating?",
        "expected_tools": ["get_top_rated_hospitals"],
    },
    {
        "id": "cms_methodology",
        "question": "How is the CMS star rating calculated?",
        "expected_tools": ["search_cms_documents"],
    },
    {
        "id": "infection_comparison",
        "question": "Compare South Dakota and Utah infection rates",
        "expected_tools": ["get_hospital_infections"],
    },
    {
        "id": "historical_trend",
        "question": "How has the average hospital rating changed across pipeline runs?",
        "expected_tools": ["get_historical_analytics"],
    },
    {
        "id": "lowest_rated",
        "question": "Show me the lowest-rated facilities",
        "expected_tools": ["get_top_rated_hospitals"],
    },
]


def make_mock_result(tools_used: list[str]) -> dict:
    return {
        "question": "test",
        "mode": "agent",
        "tools_used": tools_used,
        "explanation": "Mock explanation.",
        "results": [],
        "tokens_used": {"prompt": 100, "completion": 50, "total": 150},
        "estimated_cost_usd": 0.000001,
    }


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


@pytest.mark.parametrize("case", EVAL_CASES, ids=[c["id"] for c in EVAL_CASES])
async def test_agent_routing(client, auth_token, case):
    await asyncio.sleep(0.5)  # avoid rate limit in CI

    with patch("app.api.hospital_router.publish_query", new=AsyncMock(return_value=True)):
        with patch("app.api.hospital_router.create_job", new=AsyncMock(return_value=None)):
            response = await client.post(
                AI_URL,
                json={"question": case["question"]},
                headers={"Authorization": f"Bearer {auth_token}"},
            )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


async def test_eval_job_polling(client, auth_token):
    mock_job = {
        "job_id": "eval-test-123",
        "question": "test",
        "status": "done",
        "result": make_mock_result(["get_top_rated_hospitals"]),
    }

    with patch("app.api.hospital_router.get_job", new=AsyncMock(return_value=mock_job)):
        response = await client.get(
            "/api/v1/ai/query/eval-test-123",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "tools_used" in data


async def test_eval_unauthenticated_blocked(client):
    response = await client.post(
        AI_URL,
        json={"question": "Which hospitals have 5 stars?"},
    )
    assert response.status_code == 401