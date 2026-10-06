import httpx
from app.core.config import settings
from app.core.logging import logger

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

COUNTRY_NAMES = {
    "US": "United States", "BR": "Brazil", "CA": "Canada",
    "GB": "United Kingdom", "FR": "France", "BE": "Belgium",
    "PT": "Portugal", "ES": "Spain", "IT": "Italy", "MT": "Malta",
}

LANGUAGE_MAP = {
    "US": "English", "CA": "English", "GB": "English", "MT": "English",
    "BR": "Brazilian Portuguese", "PT": "European Portuguese",
    "FR": "French", "BE": "French",
    "ES": "Spanish", "IT": "Italian",
}

SUMMARY_SYSTEM_PROMPT = """You are a healthcare data analyst. Generate a concise, 
informative summary (3-4 sentences) about a country's healthcare system.
Include: system type (universal/private/mixed), key characteristics, 
any notable strengths or challenges, and current context.
Be factual, specific, and professional. Respond in the same language as the country's primary language.
Never use bullet points — write in flowing prose."""

async def generate_country_summary(country: str) -> str:
    country_name = COUNTRY_NAMES.get(country, country)
    language = LANGUAGE_MAP.get(country,  "English")
    
    prompt = f"""Write a brief, informative summary about the healthcare system of {country_name} ({country}).
    Include the type of system (universal/private/mixed), key characteristics, 
    notable strengths or challenges, and recent context if relevant.
    Keep it to 3-4 sentences maximum. Be specific and factual.
    Write your response in {language}."""

    try:
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
                        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 300,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error("country_summary_failed", country=country, error=str(e))
        return ""