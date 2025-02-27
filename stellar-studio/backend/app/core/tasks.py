# app/core/tasks.py
from app.core.celery import celery_app

# Import des fonctions de tâches depuis les modules appropriés
from app.tasks.download.tasks import download_mast_files
from app.tasks.processing.tasks import process_hoo_preset, generate_channel_previews, wait_user_validation

# Enregistrement explicite des tâches avec leurs noms complets
celery_app.task(name='app.tasks.download.tasks.download_mast_files')(download_mast_files)
celery_app.task(name='app.tasks.processing.tasks.process_hoo_preset')(process_hoo_preset)
celery_app.task(name='generate_channel_previews')(generate_channel_previews)
celery_app.task(name='wait_user_validation')(wait_user_validation)

# Autres tâches à ajouter selon les besoins
