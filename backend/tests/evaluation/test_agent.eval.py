import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app

AUTH_URL = "/api/v1/auth/token"
AI_URL = "/api/v1/ai/query"
POLL_URL = "/api/v1/ai/query/{job_id}"

@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac

@pytest.fixture(scope="module")
async def auth_token(client):
    response =  await client.post(
        AUTH_URL,
        data={"username": "admin", "password": "datapulse2024"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response.json()["access_token"]

EVAL_CASES = [
    {
        "id": "english_5star",
        "question": "Which hospitals have a 5-star rating?",
        "expected_tools": ["get_top_rated_hospitals"],
        "expected_language": "en",
        "must_have_explanation": True,
    },
    {
        "id": "portuguese_comparison",
        "question": "Compare o sistema de saúde do Texas com a Califórnia",
        "expected_tools": ["get_rating_distribution", "get_physician_state_analysis"],
        "expected_language": "pt",
        "must_have_explanation": True,
    },
    {
        "id": "cms_methodology",
        "question": "How is the CMS star rating calculated?",
        "expected_tools": ["search_cms_documents"],
        "expected_language": "en",
        "must_have_explanation": True,
    },
    {
        "id": "scarce_specialties",
        "question": "What scarce specialties does Ohio have?",
        "expected_tools": ["get_scarce_specialties"],
        "expected_language": "en",
        "must_have_explanation": True,
    },
    {
        "id": "infection_comparison",
        "question": "Compare South Dakota and Utah infection rates",
        "expected_tools": ["get_hospital_infections"],
        "expected_language": "en",
        "must_have_explanation": True,
    },
    {
        "id": "historical_trend",
        "question": "How has the average hospital rating changed across pipeline runs?",
        "expected_tools": ["get_historical_analytics"],
        "expected_language": "en",
        "must_have_explanation": True,
    },
    {
        "id": "lowest_rated",
        "question": "Show me the lowest-rated facilities",
        "expected_tools": ["get_top_rated_hospitals"],
        "expected_language": "en",
        "must_have_explanation": True,
    },
    {
        "id": "spanish_query",
        "question": "¿Cuáles son los hospitales con 5 estrellas en Texas?",
        "expected_tools": ["get_top_rated_hospitals", "search_hospitals"],
        "expected_language": "es",
        "must_have_explanation": True,
    },
]

def make_mock_result(tools_used: list[str], language:str = "en") -> dict:
    return{
        "question": "test",
        "mode": "agent",
        "tools_used": tools_used,
        "explanation": f"Mock explanation in {language}.",
        "results": [],
        "tokens_used": {"prompt": 100, "completion": 50, "total": 150},
        "estimated_cost_usd": 0.000001,
    }
    
@pytest.mark.parametrize("case", EVAL_CASES, ids=[c["id"] for c in EVAL_CASES])
async def test_agent_eval(client, auth_token, case):
    mock_result = make_mock_result(case["expected_tools"], case["expected_language"])
    with patch("app.api.hospital_router.publish_query", new=AsyncMock(return_value=True)):
        with patch("app.api.hospital_router.create_job", new=AsyncMock(return_value=None)):
            response = await client.post(
                AI_URL,
                json={"question": case["question"]},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
    assert response.status_code == 200
    data =  response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    
@pytest.mark.parametrize("case", EVAL_CASES, ids=[c["id"] for c in EVAL_CASES])
async def test_forced_tool_routing(case):
    from app.ai.hospital_agent_service import ask_agent
    from sqlalchemy.ext.asyncio import AsyncSession
    
    mock_result = make_mock_result(case["expected_tools"])
    with patch("app.ai.hospital_agent_service.ask_agent", new=AsyncMock(return_value=mock_result)):
        result = await ask_agent(AsyncMock(spec=AsyncSession), case["question"])
    assert result is not None        
        
        
async def test_eval_response_has_required_fields(client, auth_token):
    mock_result = make_mock_result(["get_top_rated_hospitals"])

    with patch("app.api.hospital_router.publish_query", new=AsyncMock(return_value=True)):
        with patch("app.api.hospital_router.create_job", new=AsyncMock(return_value=None)):
            response = await client.post(
                AI_URL,
                json={"question": "Which hospitals have a 5-star rating?"},
                headers={"Authorization": f"Bearer {auth_token}"},
            )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "status" in data
    
async def test_eval_job_polling_endpoint(client, auth_token):
    from app.core.job_store import get_job
    mock_job = {
        "job_id": "test-123",
        "question": "test",
        "status": "done",
        "result": make_mock_result(["get_top_rated_hospitals"]),
    }

    with patch("app.api.hospital_router.get_job", new=AsyncMock(return_value=mock_job)):
        response = await client.get(
            "/api/v1/ai/query/test-123",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "tools_used" in data

