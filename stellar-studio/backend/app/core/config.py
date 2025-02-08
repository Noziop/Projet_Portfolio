# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# Obtenir le chemin absolu du fichier .env
env_path = Path(__file__).parents[2] / '.env'

class Settings(BaseSettings):
    # Base
    PROJECT_NAME: str = "Stellar Studio"  # On peut garder celle-ci par défaut
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_NAME: str
    
    # Redis
    REDIS_URL: str
    REDIS_SESSION_DB: int = 1
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # MinIO
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+mysqlconnector://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding='utf-8',
        case_sensitive=True
    )

settings = Settings()
