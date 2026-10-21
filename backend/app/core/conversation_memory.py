import httpx

from app.core.cache import get_cache, set_cache
from app.core.config import settings
from app.core.logging import logger

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SUMMARY_MODEL = "openai/gpt-oss-20b"

MEMORY_TTL = 86400
MAX_HISTORY = 10
RECENT_PAIRS = 4
SUMMARIZE_AT_PAIRS = 6


async def _summarize_overflow(previous_summary: str | None, overflow_pairs: list[dict]) -> str | None:
    transcript_lines = []
    for msg in overflow_pairs:
        role = "User" if msg["role"] == "user" else "Assistant"
        transcript_lines.append(f"{role}: {msg['content']}")
    transcript = "\n".join(transcript_lines)

    prompt = (
        "Summarize the following part of an ongoing conversation between a user "
        "and a hospital-data assistant, in 3-5 short sentences. Keep concrete "
        "facts (states, hospital names, numbers) the user may refer back to; "
        "drop filler. Reply in the same language as the conversation, with no "
        "preamble, just the summary.\n\n"
    )
    if previous_summary:
        prompt += f"Summary so far: {previous_summary}\n\n"
    prompt += f"New turns to fold in:\n{transcript}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": SUMMARY_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
            )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error("conversation_summarize_failed", error=str(e))
        return None


async def get_conversation_history(username: str, conversation_id: str) -> list[dict]:
    key = f"conversation:{username}:{conversation_id}"
    stored = await get_cache(key)
    if not stored:
        return []    
    if isinstance(stored, list):
        return stored
    summary = stored.get("summary")
    messages = stored.get("messages", [])
    if summary:
        return [{"role": "system", "content": f"[Resumo da conversa anterior]: {summary}"}, *messages]
    return messages


async def append_to_conversation(username: str, conversation_id: str, question: str, answer: str,) -> None:
    key = f"conversation:{username}:{conversation_id}"
    stored = await get_cache(key) or {}
    if isinstance(stored, list):
        stored = {"summary": None, "messages": stored}

    summary = stored.get("summary")
    messages = stored.get("messages", [])
    messages.append({"role": "user", "content": question})
    messages.append({"role": "assistant", "content": answer})

    if len(messages) > SUMMARIZE_AT_PAIRS * 2:
        overflow = messages[: -(RECENT_PAIRS * 2)]
        new_summary = await _summarize_overflow(summary, overflow)
        if new_summary:
            summary = new_summary
            messages = messages[-(RECENT_PAIRS * 2):]
        else:
            messages = messages[-(SUMMARIZE_AT_PAIRS * 2):]

    await set_cache(key, {"summary": summary, "messages": messages}, ttl=MEMORY_TTL)
    logger.info(
        "conversation_updated",
        username=username,
        conversation_id=conversation_id,
        messages=len(messages),
        has_summary=bool(summary),
    )

async def clear_conversation(username: str, conversation_id: str) -> None:
    from app.core.cache import invalidate_cache
    key = f"conversation:{username}:{conversation_id}"
    await invalidate_cache(key)
    logger.info("conversation_cleared", username=username, conversation_id=conversation_id)