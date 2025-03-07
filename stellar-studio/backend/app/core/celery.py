# app/core/celery.py
import os
from celery import Celery
from celery.signals import worker_ready
from app.core.config import settings

celery_app = Celery(
    "app",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=[
        "app.tasks.storage.tasks",
        "app.tasks.processing.tasks",
        "app.tasks.download.tasks"
    ]
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_track_started = True
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_default_queue = "default"

celery_app.conf.beat_schedule = {
    "check-multipart-uploads-1": {
        "task": "app.tasks.storage.tasks.process_multipart_uploads",
        "schedule": 5.0,  # Toutes les 5 secondes
        "options": {"queue": "download"}
    },
    "check-multipart-uploads-2": {
        "task": "app.tasks.storage.tasks.process_multipart_uploads",
        "schedule": 5.0,  # Toutes les 5 secondes
        "options": {"queue": "download", "countdown": 1}
    },
    "check-multipart-uploads-3": {
        "task": "app.tasks.storage.tasks.process_multipart_uploads",
        "schedule": 5.0,  # Toutes les 5 secondes
        "options": {"queue": "download", "countdown": 2}
    },
    "check-multipart-uploads-4": {
        "task": "app.tasks.storage.tasks.process_multipart_uploads",
        "schedule": 5.0,  # Toutes les 5 secondes
        "options": {"queue": "download", "countdown": 3}
    },
    "check-failed-transfers": {
        "task": "app.tasks.storage.tasks.check_failed_transfers",
        "schedule": 60.0,  # Toutes les minutes
        "options": {"queue": "download"}
    }
}

# Configuration des routes de tâches
celery_app.conf.task_routes = {
    # Toutes les tâches de téléchargement vont à la queue download
    "app.tasks.download.tasks.*": {"queue": "download"},
    "app.tasks.storage.tasks.*": {"queue": "download"},
    # Toutes les tâches de traitement vont à la queue processing
    "app.tasks.processing.tasks.*": {"queue": "processing"}
}

# Assigner un identifiant unique à chaque worker lors du démarrage
@worker_ready.connect
def worker_ready_handler(sender, **kwargs):
    import socket
    import redis
    import logging

    logger = logging.getLogger("app.core.celery")
    hostname = socket.gethostname()
    worker_id = os.environ.get("CELERY_WORKER_ID", str(hash(hostname) % 100))
    
    # Enregistrer ce worker dans Redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.hset("celery:workers", worker_id, hostname)
        logger.info(f"Worker {worker_id} ({hostname}) enregistré avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du worker: {str(e)}")
    
    return True
