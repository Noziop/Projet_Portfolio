# app/tasks/processing/validation.py
import logging
import time
from typing import Dict, Any

from app.core.celery import celery_app
from app.tasks.common import update_task_status_sync, send_notification_sync
from app.domain.value_objects.task_types import TaskStatus
from .utils import get_services_sync

# Configuration du logging
validation_logger = logging.getLogger('app.task.processing.validation')

@celery_app.task(name="app.tasks.processing.wait_user_validation")
def wait_user_validation(previews_result: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """Tâche Celery qui attend la validation utilisateur avant de continuer
    
    Cette tâche met le travail en pause et notifie l'utilisateur qu'une
    action est nécessaire pour continuer le traitement.
    """
    validation_logger.info(f"Attente de validation utilisateur pour le job {job_id}")
    
    # Obtention des services en mode synchrone
    session, storage_service, ws_manager = get_services_sync()
    
    try:
        # Mise à jour du statut
        update_task_status_sync(job_id, TaskStatus.WAITING, "En attente de validation utilisateur")
        
        # Notification à l'utilisateur
        from sqlalchemy import select
        from app.domain.models.processing import ProcessingJob
        
        stmt = select(ProcessingJob).where(ProcessingJob.id == job_id)
        job = session.execute(stmt).scalar_one_or_none()
        
        if job:
            # Envoi de la notification
            send_notification_sync(
                user_id=job.user_id,
                message_data={
                    "type": "validation_required",
                    "data": {
                        "job_id": job_id,
                        "message": "Veuillez valider les aperçus pour continuer le traitement",
                        "previews": previews_result.get("previews", [])
                    }
                }
            )
            
            validation_logger.info(f"Notification de validation envoyée pour {job_id}")
            
            # Retourne les informations pour la tâche suivante
            return {
                "status": "waiting",
                "job_id": job_id,
                "message": "En attente de validation utilisateur",
                "previews": previews_result.get("previews", [])
            }
        else:
            error_msg = f"Job de traitement {job_id} non trouvé"
            validation_logger.error(error_msg)
            return {"status": "error", "message": error_msg}
            
    except Exception as e:
        validation_logger.error(f"Erreur lors de l'attente de validation: {str(e)}")
        update_task_status_sync(job_id, TaskStatus.FAILED, f"Erreur: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        session.close()
