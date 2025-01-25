# tasks/download.py
from app.core.celery import celery_app
from app.services.minio_service import get_minio_client
from astroquery.mast import Observations

@celery_app.task(name="app.tasks.download_fits")
def download_fits(telescope: str, object_name: str):
    # Logique de téléchargement
    pass

