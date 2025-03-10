# app/core/celery.py
import os
from celery import Celery
from celery.signals import worker_ready, task_prerun
from app.core.config import settings

celery_app = Celery(
    "app",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=[
        "app.tasks.storage.tasks",
        "app.tasks.processing.presets",
        "app.tasks.processing.previews",
        "app.tasks.processing.validation",
        "app.tasks.download.search",
        "app.tasks.download.select",
        "app.tasks.download.download",
        "app.tasks.download.finalize",
        "app.tasks.download.workflow"
    ]
)

# Configuration de base
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_track_started = True
celery_app.conf.broker_connection_retry_on_startup = True

# Optimisation pour la parallélisation
celery_app.conf.task_acks_late = True  # Seulement ACK si la tâche réussit
celery_app.conf.worker_prefetch_multiplier = 1  # Un worker prend une tâche à la fois
celery_app.conf.task_default_queue = "default"

# Timeouts et limites pour éviter les tâches bloquées
celery_app.conf.task_time_limit = 3600  # 1 heure max par tâche
celery_app.conf.task_soft_time_limit = 3000  # Avertissement après 50 minutes
celery_app.conf.worker_max_tasks_per_child = 10  # Redémarrer après 10 tâches

# Configuration des tâches périodiques
celery_app.conf.beat_schedule = {
    "check-multipart-uploads": {
        "task": "app.tasks.storage.tasks.process_multipart_uploads",
        "schedule": 5.0,  # Toutes les 5 secondes
        "options": {"queue": "download"}
    },
    "check-failed-transfers": {
        "task": "app.tasks.storage.tasks.check_failed_transfers",
        "schedule": 60.0,  # Toutes les minutes
        "options": {"queue": "download"}
    }
}

# Configuration des routes pour les tâches refactorisées
celery_app.conf.task_routes = {
    # Queue download
    "app.tasks.download.search.*": {"queue": "download"},
    "app.tasks.download.select.*": {"queue": "download"},
    "app.tasks.download.workflow.*": {"queue": "download"},
    "app.tasks.storage.tasks.*": {"queue": "download"},
    
    # Queue parallèle pour les téléchargements de fichiers
    "app.tasks.download.download.*": {"queue": "download_files"},
    
    # Queue finalisation
    "app.tasks.download.finalize.*": {"queue": "download"},
    
    # Queue processing
    "app.tasks.processing.presets.*": {"queue": "processing"},
    "app.tasks.processing.previews.*": {"queue": "processing"},
    "app.tasks.processing.validation.*": {"queue": "processing"}
}

# Assigner un identifiant unique à chaque worker
@worker_ready.connect
def worker_ready_handler(sender, **kwargs):
    import socket
    import redis
    import logging

    logger = logging.getLogger("app.core.celery")
    hostname = socket.gethostname()
    worker_id = os.environ.get("CELERY_WORKER_ID", str(hash(hostname) % 100))
    
    # Récupération des queues écoutées
    queues = "default"
    try:
        # Essayer d'obtenir les queues à partir des consommateurs
        if hasattr(sender, 'consumer') and hasattr(sender.consumer, 'task_consumer'):
            if hasattr(sender.consumer.task_consumer, 'queues'):
                queue_names = list(sender.consumer.task_consumer.queues.keys())
                if queue_names:
                    queues = ",".join(queue_names)
    except:
        pass
    
    # Enregistrer ce worker dans Redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.hset("celery:workers", worker_id, f"{hostname}:{queues}")
        logger.info(f"Worker {worker_id} ({hostname}) sur queues '{queues}' enregistré")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du worker: {str(e)}")
    
    return True


# S'assurer que chaque tâche utilise bien sa propre session
@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    import logging
    logger = logging.getLogger("app.core.celery")
    logger.info(f"Démarrage de la tâche {task.name} ({task_id})")
