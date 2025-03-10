# app/core/tasks.py
from celery import shared_task
from app.core.celery import celery_app

# Import des fonctions de tâches depuis les modules appropriés
from app.tasks.processing import process_hoo_preset, generate_channel_previews, wait_user_validation

# Configuration commune pour toutes les tâches
common_options = {
    "bind": True,
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "max_retries": 3
}

# Enregistrement explicite des tâches avec leurs noms complets et options standardisées
celery_app.task(
    name='app.tasks.processing.process_hoo_preset',
    **common_options
)(process_hoo_preset)

celery_app.task(
    name='app.tasks.processing.generate_channel_previews',
    **common_options
)(generate_channel_previews)

celery_app.task(
    name='app.tasks.processing.wait_user_validation',
    **common_options
)(wait_user_validation)

# Autres tâches à ajouter selon les besoins
