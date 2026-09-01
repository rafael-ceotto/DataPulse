import httpx
from app.core.config import settings

async def send_slack_alert(message: str) -> None:
    if not settings.SLACK_WEBHOOK_URL:
        print("Slack webhook not configured, skipping alert")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(settings.SLACK_WEBHOOK_URL, json={"text": message},)
    except Exception as e:
        print(f"Slack alert failed: {e}")