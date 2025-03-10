# app/tasks/download/finalize.py
import logging
from uuid import UUID

from app.db.session import SyncSessionLocal
from app.core.celery import celery_app
from app.tasks.common.status import update_task_status_sync
from app.domain.value_objects.task_types import TaskStatus
from app.tasks.common.notifications import send_notification_sync

# Configuration du logging
finalize_logger = logging.getLogger('app.task.download.finalize')

@celery_app.task(name="app.tasks.download.finalize_download")
def finalize_download(download_results):
    """Finalise le téléchargement et notifie l'utilisateur"""
    # Premier résultat contient l'ID de tâche
    task_id = download_results[0]["task_id"] if download_results else None
    
    if not task_id:
        finalize_logger.error("Résultat de téléchargement invalide ou vide")
        return {"status": "error", "message": "Résultat de téléchargement invalide"}
    
    finalize_logger.info(f"Finalisation du téléchargement pour la tâche {task_id}")
    
    # Consolider les fichiers téléchargés
    all_files = []
    error_count = 0
    
    for result in download_results:
        if result.get("status") == "success":
            all_files.extend(result.get("downloaded_files", []))
        else:
            error_count += 1
            finalize_logger.warning(f"Erreur dans le chunk {result.get('chunk_index')}: {result.get('message')}")
    
    with SyncSessionLocal() as session:
        try:
            # Récupérer la tâche
            from app.infrastructure.repositories.task_repository import TaskRepository
            task_repo = TaskRepository(session)
            task = task_repo.get_sync(UUID(task_id))
            
            if not task:
                finalize_logger.error(f"Tâche {task_id} non trouvée")
                return {"status": "error", "message": "Tâche non trouvée"}
            
            # Message de finalisation
            if len(all_files) > 0:
                # Au moins certains fichiers ont été téléchargés avec succès
                status_message = f"{len(all_files)} fichiers téléchargés avec succès"
                if error_count > 0:
                    status_message += f" (avec {error_count} erreurs)"
                
                update_task_status_sync(task_id, TaskStatus.COMPLETED, status_message)
                
                # Notifier l'utilisateur via WebSocket
                send_notification_sync(
                    user_id=task.user_id,
                    message_data={
                        "task_id": str(task_id),
                        "progress": 100,
                        "message": status_message,
                        "type": "download_complete",
                        "files": all_files
                    }
                )
                
                finalize_logger.info(f"Téléchargement terminé: {status_message}")
                
                # Lancement du traitement des aperçus (si configuré)
                try:
                    # Import placé ici pour éviter les dépendances circulaires
                    from app.tasks.processing import generate_channel_previews
                    
                    # Lancement de la tâche de génération d'aperçus
                    generate_previews = task.params.get("generate_previews", True)
                    if generate_previews and all_files:
                        # Créer une nouvelle tâche pour la génération d'aperçus
                        from app.domain.models.task import Task
                        from datetime import datetime
                        
                        preview_task = Task(
                            user_id=task.user_id,
                            status=TaskStatus.PENDING,
                            type="GENERATE_PREVIEWS",
                            params={
                                "target_id": task.params.get("target_id"),
                                "parent_task_id": str(task_id)
                            },
                            created_at=datetime.now()
                        )
                        
                        session.add(preview_task)
                        session.commit()
                        
                        # Lancer la tâche de génération d'aperçus
                        preview_task_id = str(preview_task.id)
                        target_id = task.params.get("target_id")
                        
                        generate_channel_previews.delay(
                            preview_task_id, 
                            target_id
                        )
                        
                        finalize_logger.info(f"Tâche de génération d'aperçus lancée: {preview_task_id}")
                except Exception as e:
                    finalize_logger.warning(f"Erreur lors du lancement de la génération d'aperçus: {str(e)}")
                
                return {
                    "status": "success",
                    "message": status_message,
                    "files": all_files
                }
            else:
                # Aucun fichier téléchargé avec succès
                error_message = "Aucun fichier téléchargé avec succès"
                update_task_status_sync(task_id, TaskStatus.FAILED, error_message)
                
                # Notifier l'utilisateur via WebSocket
                send_notification_sync(
                    user_id=task.user_id,
                    message_data={
                        "task_id": str(task_id),
                        "progress": 100,
                        "message": error_message,
                        "type": "download_error"
                    }
                )
                
                finalize_logger.error(error_message)
                return {"status": "error", "message": error_message}
        
        except Exception as e:
            finalize_logger.error(f"Erreur lors de la finalisation: {str(e)}")
            update_task_status_sync(task_id, TaskStatus.FAILED, f"Erreur lors de la finalisation: {str(e)}")
            return {"status": "error", "message": str(e)}
