"""
Tâches Celery liées au stockage de fichiers.
Gère les uploads multipart et la récupération des transferts échoués.
"""

# Importation des tâches
from .tasks import process_multipart_uploads, check_failed_transfers

__all__ = [
    'process_multipart_uploads',
    'check_failed_transfers'
]
