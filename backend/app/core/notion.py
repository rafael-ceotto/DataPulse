import httpx
from app.core.config import settings


async def save_to_notion(question: str, explanation: str, tools_used: list[str]) -> bool:
    if not settings.NOTION_TOKEN or not settings.NOTION_PAGE_ID:
        print("Notion not configured, skipping")
        return False

    tools_text = ", ".join(tools_used) if tools_used else "sql"

    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": question}}]
            }
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": f"Tools used: {tools_text}"}}],
                "icon": {"emoji": "🔧"}
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": explanation[:2000]}}]
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.patch(
                f"https://api.notion.com/v1/blocks/{settings.NOTION_PAGE_ID}/children",
                headers={
                    "Authorization": f"Bearer {settings.NOTION_TOKEN}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28",
                },
                json={"children": blocks}
            )
        print(f"=== NOTION: status={response.status_code} body={response.text[:200]} ===")
        return response.status_code == 200
    except Exception as e:
        import traceback
        print(f"Notion save failed: {e}")
        print(traceback.format_exc())
        return False