# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

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
    SECRET_KEY: str = "your-secret-key-here"  # À changer en production !
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    class Config:
        env_file = ".env"

    MINIO_URL: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"


settings = Settings()
