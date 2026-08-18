from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://datapulse:datapulse@localhost:5433/datapulse"
    
settings = Settings()