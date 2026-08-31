import httpx
from app.core.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

INSIGHT_SYSTEM_PROMPT = """You are a healthcare data analyst monitoring CMS hospital quality metrics.
You receive the current pipeline run data and a history of previous insights.
Your job is to generate a concise, actionable insight (2-3 sentences max) about what the data shows.

Rules:
- Be specific with numbers
- Reference trends from history when relevant
- Flag consecutive drops or rises
- If stable, say so briefly
- Always respond in English
- Never use bullet points — write in flowing prose
"""

async def generate_insight(current_avg: float, previous_avg: float | None, history: list[dict],) -> str:
    
    variation = round(current_avg - previous_avg, 3) if previous_avg else None
    direction = None
    
    if variation is not None:
        if variation > 0:
            direction = f"increased by {abs(variation)}"
        elif variation < 0:
            direction = f"decreased by {abs(variation)}"
        else:
            direction = "remained stable"
            
    history_text = ""
    if history:
        history_text = "\n\nPrevious insights (oldest to newest):\n"
        for h in history:
            history_text += f"- {h['started_at'][:10]}: avg={h['avg_rating']} — {h['insight']}\n"
    user_message = f"""Current pipeline run:
    - avg_rating: {current_avg}
    - previous avg_rating: {previous_avg if previous_avg else 'N/A (first run)'}
    - variation: {direction if direction else 'N/A (first run)'}
    {history_text}
    Generate a concise insight about what this data tells us about US hospital quality trends."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.3,
                "max_tokens": 200,   
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    
    