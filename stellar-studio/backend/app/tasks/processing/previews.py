# app/tasks/processing/previews.py
import logging
import numpy as np
from typing import Dict, Any

from app.core.celery import celery_app
from app.tasks.common import update_task_status_sync, send_notification_sync
from app.domain.value_objects.task_types import TaskStatus
from .utils import auto_stf, get_services_sync

# Configuration du logging
preview_logger = logging.getLogger('app.task.processing.previews')

@celery_app.task(name="app.tasks.processing.generate_channel_previews")
def generate_channel_previews(task_id: str, target_id: str) -> Dict[str, Any]:
    """Génère des aperçus par canal pour les images d'une cible"""
    preview_logger.info(f"Démarrage de la génération d'aperçus: task_id={task_id}")
    
    # Obtention des services en mode synchrone
    session, storage_service, ws_manager = get_services_sync()
    
    try:
        # Mise à jour du statut
        update_task_status_sync(task_id, TaskStatus.RUNNING, "Génération d'aperçus en cours")
        
        # 1. Récupération des fichiers de la cible
        from sqlalchemy import select
        from app.domain.models.target_file import TargetFile
        from app.domain.models.filter import Filter
        
        stmt = select(TargetFile).join(Filter, TargetFile.filter_id == Filter.id).where(
            TargetFile.target_id == target_id,
            TargetFile.is_downloaded == True,
            TargetFile.in_minio == True
        )
        
        target_files = session.execute(stmt).scalars().all()
        
        if not target_files:
            error_msg = f"Aucun fichier trouvé pour la cible {target_id}"
            preview_logger.error(error_msg)
            update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
            return {"status": "error", "message": error_msg}
        
        preview_logger.info(f"Traitement de {len(target_files)} fichiers pour les aperçus")
        
        # 2. Traitement par filtre
        previews = []
        
        for target_file in target_files:
            try:
                # Récupérer le filtre
                filter_stmt = select(Filter).where(Filter.id == target_file.filter_id)
                filter = session.execute(filter_stmt).scalar_one_or_none()
                
                if not filter:
                    preview_logger.warning(f"Filtre introuvable pour le fichier {target_file.id}")
                    continue
                
                # Récupérer les données FITS
                fits_data = storage_service.get_fits_file(target_file.file_path)
                
                if not fits_data or "data" not in fits_data:
                    preview_logger.warning(f"Fichier invalide ou vide: {target_file.file_path}")
                    continue
                
                # Appliquer STF pour améliorer la visualisation
                image_data = auto_stf(fits_data["data"])
                
                # Convertir en PNG
                from PIL import Image
                import io
                
                # Normalisation et conversion en uint8
                image_array = (image_data * 255).astype(np.uint8)
                
                # Création d'une image grayscale
                pil_image = Image.fromarray(image_array, mode='L')
                
                # Sauvegarde en mémoire
                img_buffer = io.BytesIO()
                pil_image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Chemin de l'aperçu
                preview_path = f"previews/channels/{target_id}_{filter.name}_{target_file.id}.png"
                
                # Stockage dans MinIO
                storage_service.store_preview(
                    img_buffer.getvalue(),
                    preview_path,
                    content_type="image/png"
                )
                
                # Ajouter aux résultats
                previews.append({
                    "filter": filter.name,
                    "filter_id": str(filter.id),
                    "preview_url": preview_path,
                    "file_id": str(target_file.id)
                })
                
                preview_logger.info(f"Aperçu généré pour {filter.name}: {preview_path}")
                
            except Exception as e:
                preview_logger.error(f"Erreur lors du traitement du fichier {target_file.id}: {str(e)}")
                continue
        
        # 3. Mise à jour du statut et notification
        if previews:
            update_task_status_sync(task_id, TaskStatus.COMPLETED, f"{len(previews)} aperçus générés")
            
            # Envoi de notification WebSocket
            send_notification_sync(
                user_id=target_id,
                message_data={
                    "type": "processing_update",
                    "data": {
                        "step": "PREVIEWS_COMPLETE",
                        "task_id": task_id,
                        "previews": previews
                    }
                }
            )
            
            preview_logger.info(f"Génération d'aperçus terminée: {len(previews)} images")
            return {
                "status": "success",
                "previews": previews
            }
        else:
            error_msg = "Aucun aperçu n'a pu être généré"
            update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
            return {"status": "error", "message": error_msg}
    
    except Exception as e:
        preview_logger.error(f"Erreur lors de la génération d'aperçus: {str(e)}")
        update_task_status_sync(task_id, TaskStatus.FAILED, str(e))
        return {"status": "error", "message": str(e)}
    
    finally:
        # Fermeture de la session
        session.close()
