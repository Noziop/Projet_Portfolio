# app/api/v1/endpoints/health.py
from fastapi import APIRouter
from typing import Dict
from sqlalchemy import text 
from app.db.session import AsyncSessionLocal
from app.core.celery import celery_app
from app.services.storage.service import StorageService

router = APIRouter()

@router.get("/", response_model=Dict)
@router.get("", response_model=Dict)
async def health_check():
    """Vérifie l'état de santé de l'application et ses dépendances"""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "minio": "healthy"
        }
    }

    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    try:
        # Vérification de Redis/Celery
        celery_app.control.ping()
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    try:
        # Vérification de MinIO
        storage_service = StorageService()
        storage_service.client.bucket_exists("fits-files")
    except Exception as e:
        health_status["services"]["minio"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status
