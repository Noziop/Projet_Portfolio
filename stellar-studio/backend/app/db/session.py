# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Engine
from typing import AsyncGenerator, Generator
from app.core.config import settings

# Création du moteur async pour FastAPI
async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    future=True
)

# Session async pour FastAPI
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# CORRECTION MAJEURE: Forcer explicitement PyMySQL pour Celery
# Quelle que soit l'URL d'origine
import re
sync_db_url = re.sub(r'mysql(\+[a-z]+)?://', 'mysql+pymysql://', settings.SQLALCHEMY_DATABASE_URI)

# Création du moteur sync pour Celery
sync_engine = create_engine(
    sync_db_url,  # URL modifiée avec PyMySQL
    echo=False,
    future=True
)

# Session synchrone pour Celery
SyncSessionLocal = sessionmaker(
    bind=sync_engine, expire_on_commit=False
)

# Dependency pour FastAPI (async)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Fonction pour Celery (sync)
def get_sync_db() -> Generator:
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
