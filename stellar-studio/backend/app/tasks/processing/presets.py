# app/tasks/processing/presets.py
import logging
import numpy as np
from typing import List, Dict, Any

from app.core.celery import celery_app
from app.tasks.common import update_task_status_sync
from app.domain.value_objects.task_types import TaskStatus
from .utils import auto_stf, save_preview, get_services_sync

# Configuration du logging
preset_logger = logging.getLogger('app.task.processing.presets')

@celery_app.task(name="app.tasks.processing.process_hoo_preset")
def process_hoo_preset(job_id: str, target_id: str, files: List[Dict[str, Any]]):
    """Tâche Celery pour le traitement HOO (Hydrogène-alpha + Oxygène III)
    
    HOO est un preset qui mappe le filtre H-alpha sur le canal rouge,
    et OIII sur les canaux vert et bleu.
    """
    preset_logger.info(f"Démarrage du traitement HOO: job_id={job_id}")
    
    # Obtention des services en mode synchrone
    session, storage_service, ws_manager = get_services_sync()
    
    try:
        # Mise à jour du statut
        update_task_status_sync(job_id, TaskStatus.RUNNING, "Traitement HOO en cours")
        
        # 1. Récupération et tri des fichiers par filtre
        ha_data = []
        oiii_data = []
        
        preset_logger.info(f"Traitement de {len(files)} fichiers")
        for file_info in files:
            try:
                fits_data = storage_service.get_fits_file(file_info["path"])
                if not fits_data or "data" not in fits_data:
                    preset_logger.warning(f"Fichier invalide ou vide: {file_info['path']}")
                    continue
                
                # Classifier par filtre
                if "H-alpha" in file_info.get("filter", ""):
                    ha_data.append(fits_data)
                    preset_logger.info(f"Fichier H-alpha ajouté: {file_info['path']}")
                elif "OIII" in file_info.get("filter", ""):
                    oiii_data.append(fits_data)
                    preset_logger.info(f"Fichier OIII ajouté: {file_info['path']}")
                else:
                    preset_logger.warning(f"Filtre non reconnu: {file_info.get('filter', 'inconnu')}")
            except Exception as e:
                preset_logger.error(f"Erreur lors du traitement du fichier {file_info.get('path')}: {str(e)}")
                continue
        
        # Vérifier qu'on a des données pour chaque filtre
        if not ha_data:
            error_msg = "Aucune image H-alpha trouvée"
            preset_logger.error(error_msg)
            update_task_status_sync(job_id, TaskStatus.FAILED, error_msg)
            return {"status": "error", "message": error_msg}
            
        if not oiii_data:
            error_msg = "Aucune image OIII trouvée"
            preset_logger.error(error_msg)
            update_task_status_sync(job_id, TaskStatus.FAILED, error_msg)
            return {"status": "error", "message": error_msg}
        
        # 2. Stacking des images par filtre
        ha_stack = np.mean([d["data"] for d in ha_data], axis=0)
        oiii_stack = np.mean([d["data"] for d in oiii_data], axis=0)
        
        preset_logger.info(f"Stacking terminé: {len(ha_data)} images H-alpha, {len(oiii_data)} images OIII")
        
        # 3. Application du STF (Screen Transfer Function)
        red_channel = auto_stf(ha_stack)
        green_channel = auto_stf(oiii_stack)
        blue_channel = auto_stf(oiii_stack)
        
        # 4. Création de l'image RGB
        rgb_data = np.stack((red_channel, green_channel, blue_channel), axis=-1)
        
        # 5. Génération et stockage de l'aperçu
        preview_path = save_preview(rgb_data, storage_service, job_id)
        preset_logger.info(f"Aperçu sauvegardé: {preview_path}")
        
        # 6. Mise à jour du statut et notification WebSocket
        update_task_status_sync(job_id, TaskStatus.COMPLETED, "Traitement HOO terminé")
        
        # Notification WebSocket synchrone
        ws_manager.send_message_sync(
            user_id=target_id,  # Utiliser target_id comme user_id
            message={
                "type": "processing_update",
                "data": {
                    "step": "HOO_COMPLETE",
                    "job_id": job_id,
                    "preview_url": preview_path,
                    "channels": {
                        "ha": "Mapped to Red",
                        "oiii": "Mapped to Green+Blue"
                    }
                }
            }
        )
        
        # Fermer la session
        session.close()
        
        return {
            "status": "success",
            "preview": preview_path,
            "job_id": job_id,
            "target_id": target_id
        }
        
    except Exception as e:
        preset_logger.error(f"Erreur lors du traitement HOO: {str(e)}")
        update_task_status_sync(job_id, TaskStatus.FAILED, f"Erreur: {str(e)}")
        
        # Notification d'erreur via WebSocket
        try:
            ws_manager.send_error_sync(
                user_id=target_id,
                error=f"Erreur de traitement HOO: {str(e)}"
            )
        except:
            pass
        
        # Fermer la session en cas d'erreur
        session.close()
        
        return {"status": "error", "message": str(e)}

@celery_app.task(name="app.tasks.processing.process_rgb_preset")
def process_rgb_preset(job_id: str, target_id: str, files: List[Dict[str, Any]]):
    """Tâche Celery pour le traitement RGB classique
    
    Le preset RGB mappe les filtres standards RGB sur leurs canaux respectifs.
    """
    preset_logger.info(f"Démarrage du traitement RGB: job_id={job_id}")
    
    # Obtention des services en mode synchrone
    session, storage_service, ws_manager = get_services_sync()
    
    try:
        # Mise à jour du statut
        update_task_status_sync(job_id, TaskStatus.RUNNING, "Traitement RGB en cours")
        
        # 1. Récupération et tri des fichiers par filtre
        r_data = []
        g_data = []
        b_data = []
        
        preset_logger.info(f"Traitement de {len(files)} fichiers")
        for file_info in files:
            try:
                fits_data = storage_service.get_fits_file(file_info["path"])
                if not fits_data or "data" not in fits_data:
                    preset_logger.warning(f"Fichier invalide ou vide: {file_info['path']}")
                    continue
                
                # Classifier par filtre
                filter_name = file_info.get("filter", "").upper()
                if "RED" in filter_name or "R" == filter_name:
                    r_data.append(fits_data)
                    preset_logger.info(f"Fichier Rouge ajouté: {file_info['path']}")
                elif "GREEN" in filter_name or "G" == filter_name:
                    g_data.append(fits_data)
                    preset_logger.info(f"Fichier Vert ajouté: {file_info['path']}")
                elif "BLUE" in filter_name or "B" == filter_name:
                    b_data.append(fits_data)
                    preset_logger.info(f"Fichier Bleu ajouté: {file_info['path']}")
                else:
                    preset_logger.warning(f"Filtre non reconnu pour RGB: {filter_name}")
            except Exception as e:
                preset_logger.error(f"Erreur lors du traitement du fichier {file_info.get('path')}: {str(e)}")
                continue
        
        # Vérifier qu'on a des données pour chaque filtre
        missing_filters = []
        if not r_data:
            missing_filters.append("Rouge")
        if not g_data:
            missing_filters.append("Vert")
        if not b_data:
            missing_filters.append("Bleu")
        
        if missing_filters:
            error_msg = f"Filtres manquants: {', '.join(missing_filters)}"
            preset_logger.error(error_msg)
            update_task_status_sync(job_id, TaskStatus.FAILED, error_msg)
            return {"status": "error", "message": error_msg}
        
        # 2. Stacking des images par filtre
        r_stack = np.mean([d["data"] for d in r_data], axis=0)
        g_stack = np.mean([d["data"] for d in g_data], axis=0)
        b_stack = np.mean([d["data"] for d in b_data], axis=0)
        
        preset_logger.info(f"Stacking terminé: {len(r_data)} R, {len(g_data)} G, {len(b_data)} B")
        
        # 3. Application du STF (Screen Transfer Function)
        red_channel = auto_stf(r_stack)
        green_channel = auto_stf(g_stack)
        blue_channel = auto_stf(b_stack)
        
        # 4. Création de l'image RGB
        rgb_data = np.stack((red_channel, green_channel, blue_channel), axis=-1)
        
        # 5. Génération et stockage de l'aperçu
        preview_path = save_preview(rgb_data, storage_service, f"{job_id}_rgb")
        preset_logger.info(f"Aperçu RGB sauvegardé: {preview_path}")
        
        # 6. Mise à jour du statut et notification WebSocket
        update_task_status_sync(job_id, TaskStatus.COMPLETED, "Traitement RGB terminé")
        
        # Notification WebSocket synchrone
        ws_manager.send_message_sync(
            user_id=target_id,
            message={
                "type": "processing_update",
                "data": {
                    "step": "RGB_COMPLETE",
                    "job_id": job_id,
                    "preview_url": preview_path,
                    "channels": {
                        "red": "Mapped to Red",
                        "green": "Mapped to Green",
                        "blue": "Mapped to Blue"
                    }
                }
            }
        )
        
        # Fermer la session
        session.close()
        
        return {
            "status": "success",
            "preview": preview_path,
            "job_id": job_id,
            "target_id": target_id
        }
        
    except Exception as e:
        preset_logger.error(f"Erreur lors du traitement RGB: {str(e)}")
        update_task_status_sync(job_id, TaskStatus.FAILED, f"Erreur: {str(e)}")
        
        # Notification d'erreur via WebSocket
        try:
            ws_manager.send_error_sync(
                user_id=target_id,
                error=f"Erreur de traitement RGB: {str(e)}"
            )
        except:
            pass
        
        # Fermer la session en cas d'erreur
        session.close()
        
        return {"status": "error", "message": str(e)}
