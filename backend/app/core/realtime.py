import os
from supabase import create_client, Client
from app.core.logging import logger

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

_client: Client | None = None

def get_supabase_client() -> Client | None:
    global _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

async def publish_event(event_type: str, payload: dict) -> None:
    client = get_supabase_client()
    if not client:
        logger.info("supabase_not_configured")
        return
    try:
        client.table("events").insert({
            "type": event_type,
            "payload": payload,
        }).execute()
        logger.info("supabase_Event_published", event_type=event_type)
    except Exception as e:
        logger.error("supabase_event_failed", error=str(e))