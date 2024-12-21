# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Stellar Studio"
    API_V1_STR: str = "/api/v1"
    REDIS_URL: str = "redis://redis:6379/0"
    
settings = Settings()