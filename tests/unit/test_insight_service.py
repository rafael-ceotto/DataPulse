import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.ai.insight_service import generate_insight

def make_mock_response(content: str):
    mock_response =  MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    mock_response.raise_for_status == MagicMock()
    return mock_response

@pytest.mark.asyncio
async def test_generate_insight_first_run():
    mock_response = make_mock_response("Hospital ratings are stable at 3.21.")
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await generate_insight(3.21, None, [])
    assert result == "Hospital ratings are stable at 3.21."
    
@pytest.mark.asyncio
async def test_generate_insight_with_previous_avg():
    mock_response = make_mock_response("Ratings increased from 3.10 to 3.21.")
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await generate_insight(3.21, None, [])
    assert result == "Ratings increased from 3.10 to 3.21."
    
@pytest.mark.asyncio
async def test_generate_insight_with_history():
    history = [
        {"started_at": "2026-08-31T10:00:00", "avg_rating": 3.20, "insight": "Stable trend."},
        {"started_at": "2026-09-01T10:00:00", "avg_rating": 3.21, "insight": "Slight improvement."},
    ]
    mock_response = make_mock_response("Consecutive improvement detected.")

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await generate_insight(3.22, 3.21, history)

    assert result == "Consecutive improvement detected."
    
@pytest.mark.asyncio
async def test_generate_insight_strips_whitespace():
    mock_response = make_mock_response("  Ratings are stable.  ")

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await generate_insight(3.21, 3.21, [])

    assert result == "Ratings are stable."