# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# Obtenir le chemin absolu du fichier .env
env_path = Path(__file__).parents[2] / '.env'

class Settings(BaseSettings):
    # Base
    PROJECT_NAME: str = "Stellar Studio"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_USER: str = "stellaruser"
    DATABASE_PASSWORD: str = "stellarpassword"
    DATABASE_HOST: str = "database"
    DATABASE_PORT: str = "3306"
    DATABASE_NAME: str = "stellarstudio"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_SESSION_DB: int = 1
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # MinIO
    MINIO_URL: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding='utf-8',
        case_sensitive=True
    )

settings = Settings()
