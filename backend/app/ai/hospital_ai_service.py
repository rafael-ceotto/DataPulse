import json
import re

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import HOSPITAL_SYSTEM_PROMPT
from app.core.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"


async def ask_hospital_ai(session: AsyncSession, question: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": HOSPITAL_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": question,
                    },
                ],
                "temperature": 0.1,
            }
        )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    content = re.sub(r'[\x00-\x1f\x7f]', ' ', content)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON: {content}")

    sql = parsed["sql"]
    explanation = parsed["explanation"]

    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError(f"Only SELECT queries are allowed. Got: {sql}")

    result = await session.execute(text(sql))
    rows = result.mappings().all()

    return {
        "question": question,
        "sql": sql,
        "explanation": explanation,
        "results": [
            dict({
                k: float(v) if hasattr(v, '__float__') and not isinstance(v, (int, str, bool, type(None))) else v
                for k, v in row.items()
            })
            for row in rows
        ],
    }