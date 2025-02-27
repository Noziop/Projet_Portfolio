# app/core/celery.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "stellar_studio",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.download",
        "app.tasks.processing"
    ]
)

celery_app.conf.task_routes = {
    "app.tasks.download.*": {"queue": "download_queue"},
    "app.tasks.processing.*": {"queue": "processing_queue"},
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
