import base64
import httpx
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger

GITHUB_API = "https://api.github.com"
INSIGHTS_FILE = "insights.md"


async def commit_insight(avg_rating: float, insight: str) -> bool:
    if not settings.GITHUB_TOKEN or not settings.GITHUB_REPO:
        logger.info("github_not_configured")
        return False

    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{GITHUB_API}/repos/{settings.GITHUB_REPO}/contents/{INSIGHTS_FILE}",
            headers=headers,
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_entry = f"## {now}\n\n**Avg Rating:** {avg_rating}\n\n{insight}\n\n---\n\n"

    if r.status_code == 200:
        data = r.json()
        sha = data["sha"]
        existing = base64.b64decode(data["content"]).decode("utf-8")
        new_content = new_entry + existing
    else:
        sha = None
        new_content = f"# DataPulse Insights\n\n{new_entry}"

    encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"insight: pipeline run {now}",
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(
                f"{GITHUB_API}/repos/{settings.GITHUB_REPO}/contents/{INSIGHTS_FILE}",
                headers=headers,
                json=payload,
            )
        logger.info("github_commit", status=response.status_code)
        return response.status_code in (200, 201)
    except Exception as e:
        logger.error("github_commit_failed", error=str(e))
        return False