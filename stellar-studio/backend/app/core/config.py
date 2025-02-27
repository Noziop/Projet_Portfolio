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
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_NAME: str
    EXPORTER_PASSWORD: str

    # Redis & Celery
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: str
    REDIS_SESSION_DB: int
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_WORKER_NAME: str
    HOSTNAME: str
    
    # Session
    SESSION_DURATION_MINUTES: int
    SESSION_COOKIE_NAME: str
    SESSION_COOKIE_SECURE: bool
    SESSION_COOKIE_HTTPONLY: bool
    SESSION_COOKIE_SAMESITE: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # MinIO
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str
    MINIO_PREVIEW_BUCKET: str = "previews"

    # Grafana
    GRAFANA_ADMIN_PASSWORD: str

    # Admin
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_USERNAME: str

    # Beginner user
    BEGINNER_EMAIL: str
    BEGINNER_PASSWORD: str
    BEGINNER_USERNAME: str

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+aiomysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding='utf-8',
        case_sensitive=True
    )

settings = Settings()
