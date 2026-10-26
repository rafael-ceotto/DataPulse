import json
import re

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import build_hospital_sql_prompt
from app.core.config import settings
from app.core.content_moderation import moderate_content
from app.core.logging import logger
from app.repositories.pipeline_run_repository import get_latest_successful_run_at

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

_FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|REVOKE|TRUNCATE|COPY|"
    r"EXECUTE|CALL|VACUUM|REINDEX|MERGE|"
    r"INTO|"
    r"PG_SLEEP|PG_READ_FILE|PG_READ_BINARY_FILE|PG_WRITE_FILE|"
    r"LO_IMPORT|LO_EXPORT|LO_GET|LO_PUT|DBLINK|"
    r"PG_TERMINATE_BACKEND|PG_CANCEL_BACKEND|SET\s+SESSION|SET\s+ROLE"
    r")\b",
    re.IGNORECASE,
)


def _validate_readonly_select(sql: str) -> None:
    cleaned = sql.strip()
    # Allow (and strip) a single trailing semicolon, but reject anything that looks like a second stacked statement.
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()
    if ";" in cleaned:
        raise ValueError("Only a single SQL statement is allowed.")

    if not re.match(r"^\s*(SELECT|WITH)\b", cleaned, re.IGNORECASE):
        raise ValueError(f"Only SELECT queries are allowed. Got: {sql}")

    if _FORBIDDEN_SQL_PATTERN.search(cleaned):
        raise ValueError("Query contains a disallowed keyword or function.")


async def ask_hospital_ai(session: AsyncSession, question: str, country: str = "US"):
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
                        "content": build_hospital_sql_prompt(country),
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

    moderation = await moderate_content(explanation)
    explanation = moderation["text"]
    if moderation["harmful_flagged"] or moderation["pii_categories"]:
        logger.warning(
            "sql_mode_moderation_flagged",
            question=question,
            pii_categories=moderation["pii_categories"],
            harmful_categories=moderation["harmful_categories"],
        )
    latest_run_at = await get_latest_successful_run_at(session)
    data_as_of = latest_run_at.strftime("%Y-%m-%d") if latest_run_at else None

    # Topic-scope guardrail: the prompt tells the model to return "sql": "" for off-topic questions instead of generating a query. 
    # Short-circuit here rather than letting an empty string hit the SELECT validator below.
    if not sql or not sql.strip():
        return {
            "question": question,
            "sql": "",
            "explanation": explanation,
            "results": [],
            "data_as_of": data_as_of,
        }

    _validate_readonly_select(sql)

    # Defense in depth: even a validated single SELECT could still be a resource-exhaustion vector (e.g. a deliberately expensive query), so
    # cap how long it's allowed to run.
    await session.execute(text("SET LOCAL statement_timeout = '5s'"))
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
        "data_as_of": data_as_of,
    }