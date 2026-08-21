import json
import httpx

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import HOSPITAL_SYSTEM_PROMPT

OLLAMA_URL = "http://localhost:11434/api/chat"

async def ask_hospital_ai(session: AsyncSession, question: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": "llama3.1",
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
                "stream": False,
            }
        )
    response.raise_for_status()
    data = response.json()
    content = data["message"]["content"]
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
        "results": [dict(row) for row in rows],
    }