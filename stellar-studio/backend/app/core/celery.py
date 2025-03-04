# app/core/celery.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "stellar_studio",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.download.tasks",
        "app.tasks.processing.tasks"
    ]
)

celery_app.conf.task_routes = {
    "app.tasks.download.tasks.*": {"queue": "download"},
    "app.tasks.processing.tasks.*": {"queue": "processing"}
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
