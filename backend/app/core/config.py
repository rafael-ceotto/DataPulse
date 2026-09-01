from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://datapulse:datapulse@localhost:5433/datapulse"
    GROQ_API_KEY: str = ""
    SLACK_WEBHOOK_URL: str = ""
    TAVILY_API_KEY: str = ""
    NOTION_TOKEN: str = ""
    NOTION_PAGE_ID: str = ""    
    
    class Config:
        env_file = ".env"
    
settings = Settings()