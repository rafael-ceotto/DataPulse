import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.slack import send_slack_alert
from app.core.notion import save_to_notion
from app.core.github import commit_insight


# ─── Slack ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_slack_alert_success():
    mock_response = MagicMock()
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        with patch("app.core.slack.settings") as mock_settings:
            mock_settings.SLACK_WEBHOOK_URL = "https://hooks.slack.com/test"
            await send_slack_alert("Test message")


@pytest.mark.asyncio
async def test_send_slack_alert_skips_when_not_configured():
    with patch("app.core.slack.settings") as mock_settings:
        mock_settings.SLACK_WEBHOOK_URL = ""
        await send_slack_alert("Test message")


@pytest.mark.asyncio
async def test_send_slack_alert_handles_exception():
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Connection error"))
        with patch("app.core.slack.settings") as mock_settings:
            mock_settings.SLACK_WEBHOOK_URL = "https://hooks.slack.com/test"
            await send_slack_alert("Test message")


# ─── Notion ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_to_notion_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "{}"

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)
        with patch("app.core.notion.settings") as mock_settings:
            mock_settings.NOTION_TOKEN = "test-token"
            mock_settings.NOTION_PAGE_ID = "test-page-id"
            result = await save_to_notion("Test question", "Test explanation", ["web_search"])

    assert result is True


@pytest.mark.asyncio
async def test_save_to_notion_skips_when_not_configured():
    with patch("app.core.notion.settings") as mock_settings:
        mock_settings.NOTION_TOKEN = ""
        mock_settings.NOTION_PAGE_ID = ""
        result = await save_to_notion("Test question", "Test explanation", [])

    assert result is False


@pytest.mark.asyncio
async def test_save_to_notion_returns_false_on_error():
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad request"

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)
        with patch("app.core.notion.settings") as mock_settings:
            mock_settings.NOTION_TOKEN = "test-token"
            mock_settings.NOTION_PAGE_ID = "test-page-id"
            result = await save_to_notion("Test question", "Test explanation", [])

    assert result is False


# ─── GitHub ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_commit_insight_skips_when_not_configured():
    with patch("app.core.github.settings") as mock_settings:
        mock_settings.GITHUB_TOKEN = ""
        mock_settings.GITHUB_REPO = ""
        result = await commit_insight(3.21, "Test insight")

    assert result is False


@pytest.mark.asyncio
async def test_commit_insight_creates_new_file():
    mock_get = MagicMock()
    mock_get.status_code = 404

    mock_put = MagicMock()
    mock_put.status_code = 201

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_get)
        mock_client.return_value.__aenter__.return_value.put = AsyncMock(return_value=mock_put)
        with patch("app.core.github.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = "test-token"
            mock_settings.GITHUB_REPO = "user/repo"
            result = await commit_insight(3.21, "Test insight")

    assert result is True


@pytest.mark.asyncio
async def test_commit_insight_creates_new_file():
    mock_get = MagicMock()
    mock_get.status_code = 404

    mock_put = MagicMock()
    mock_put.status_code = 201

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_get)
    mock_http.put = AsyncMock(return_value=mock_put)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_http
        with patch("app.core.github.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = "test-token"
            mock_settings.GITHUB_REPO = "user/repo"
            result = await commit_insight(3.21, "Test insight")

    assert result is True