# app/core/celery.py
from celery import Celery

celery_app = Celery(
    "stellar_studio",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=['app.services.task.service']
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True
)