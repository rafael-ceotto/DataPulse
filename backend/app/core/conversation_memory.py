from app.core.cache import get_cache, set_cache
from app.core.logging import logger

MEMORY_TTL = 86400
MAX_HISTORY = 10

async def get_conversation_history(username: str, conversation_id: str) -> list[dict]:
    key = f"conversation:{username}:{conversation_id}"
    history =  await get_cache(key)
    return history or []

async def append_to_conversation(username: str, conversation_id: str, question: str, answer: str,) -> None:
    key = f"conversation:{username}:{conversation_id}"
    history = await get_cache(key) or []
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
     
    #Last MAX_HISTORY pairs only
    if len(history) > MAX_HISTORY * 2:
         history = history[-(MAX_HISTORY * 2):]
         
    await set_cache(key, history, ttl=MEMORY_TTL)
    logger.info("conversation_updated", username=username, conversation_id=conversation_id, messages=len(history))
    
async def clear_conversation(username: str, conversation_id: str) -> None:
    from app.core.cache import invalidate_cache
    key = f"conversation:{username}:{conversation_id}"
    await invalidate_cache(key)
    logger.info("conversation_cleared", username=username, conversation_id=conversation_id)
    