from app.core.celery import celery_app
from app.services.telescope_service import fetch_object_data, download_fits_async

# Enregistrer explicitement les tâches
celery_app.task(name='app.services.telescope_service.fetch_object_data')(fetch_object_data)
celery_app.task(name='app.services.telescope_service.download_fits_async')(download_fits_async)
