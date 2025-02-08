# tasks/processing.py
from app.core.celery import celery_app
from app.services.minio_service import get_minio_client
from astroquery.mast import Observations

@celery_app.task(name="app.tasks.process_fits")
def process_fits(observation_id: int, workflow: str):
    # Logique de traitement
    pass
