# app/core/task.py
from app.core.celery import celery_app
from app.services.task.service import download_fits

# Enregistrer explicitement la tâche avec son nom complet
celery_app.task(name='app.services.task.service.download_fits')(download_fits)


