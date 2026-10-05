from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    DB_URL: str = "postgresql+asyncpg://datapulse:datapulse@localhost:5433/datapulse"
    GROQ_API_KEY: str = ""
    SLACK_WEBHOOK_URL: str = ""
    TAVILY_API_KEY: str = ""
    NOTION_TOKEN: str = ""
    NOTION_PAGE_ID: str = ""
    GITHUB_TOKEN: str = ""
    GITHUB_REPO: str = ""
    PIPELINE_INTERVAL_HOURS: int = 6
    AI_RATE_LIMIT_PER_MINUTE: int = 5
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

settings = Settings()