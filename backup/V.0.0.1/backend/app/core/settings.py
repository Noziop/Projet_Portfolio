# app/core/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Stellar Studio"
    
    # Configuration pour les télescopes
    MAST_TOKEN: str | None = None  # Pour l'API MAST (HST/JWST)
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
