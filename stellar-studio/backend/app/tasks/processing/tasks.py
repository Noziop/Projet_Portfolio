from celery import shared_task
from uuid import UUID
import logging
from contextlib import asynccontextmanager
import numpy as np
from PIL import Image
import io
from app.db.session import AsyncSessionLocal
from app.core.celery import celery_app
from app.services.storage.service import StorageService
from app.core.ws.manager import ConnectionManager

# Singleton pour le WebSocket manager
ws_manager = ConnectionManager()

def apply_stf(data: np.ndarray) -> np.ndarray:
    """Applique une STF basique à un canal"""
    median = np.median(data)
    mad = np.median(np.abs(data - median))
    shadows = median - 2.8 * mad
    highlights = median + 8 * mad
    stretched = (data - shadows) / (highlights - shadows)
    return np.clip(stretched, 0, 1)

def save_preview(rgb_data: np.ndarray, storage_service: StorageService, job_id: str) -> str:
    """Sauvegarde une preview dans MinIO"""
    # Conversion en PNG en mémoire
    preview_data = (rgb_data * 255).astype(np.uint8)
    image = Image.fromarray(preview_data)
    
    # Sauvegarde temporaire en mémoire
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # Chemin dans MinIO
    preview_path = f"previews/{job_id}_hoo_preview.png"
    
    # Stockage dans MinIO
    storage_service.store_preview(
        img_byte_arr.getvalue(),
        preview_path,
        content_type="image/png"
    )
    
    return preview_path

@asynccontextmanager
async def get_services():
    """Context manager pour créer et gérer les services"""
    from app.services.workflow.service import WorkflowService
    async with AsyncSessionLocal() as session:
        storage_service = StorageService()
        workflow_service = WorkflowService(
            session=session,
            storage_service=storage_service,
            ws_manager=ws_manager
        )
        try:
            yield storage_service, workflow_service
        finally:
            await session.close()

@shared_task(name="process_hoo_preset")
async def process_hoo_preset(job_id: str, target_id: str, files: list):
    """
    Traitement HOO :
    - Ha : Rouge
    - OIII : Vert + Bleu
    """
    async with get_services() as (storage_service, workflow_service):
        try:
            # 1. Récupération des fichiers
            ha_data = []
            oiii_data = []
            
            for file_info in files:
                fits_data = storage_service.get_fits_file(file_info["path"])
                if "H-alpha" in file_info["filter"]:
                    ha_data.append(fits_data)
                elif "OIII" in file_info["filter"]:
                    oiii_data.append(fits_data)

            # 2. Stacking des images par filtre
            ha_stack = np.mean([d["data"] for d in ha_data], axis=0)
            oiii_stack = np.mean([d["data"] for d in oiii_data], axis=0)

            # 3. Application du STF
            red_channel = apply_stf(ha_stack)
            green_channel = apply_stf(oiii_stack)
            blue_channel = apply_stf(oiii_stack)

            # 4. Création de l'image RGB
            rgb_data = np.stack((red_channel, green_channel, blue_channel), axis=-1)

            # 5. Génération et stockage preview
            preview_path = save_preview(rgb_data, storage_service, job_id)

            # 6. Mise à jour du statut
            await workflow_service.update_processing_step(
                UUID(job_id),
                "HOO_COMPLETE",
                {
                    "preview_url": preview_path,
                    "channels": {
                        "ha": "Mapped to Red",
                        "oiii": "Mapped to Green+Blue"
                    }
                }
            )

            return {
                "status": "success",
                "preview": preview_path
            }

        except Exception as e:
            logging.exception(f"Erreur lors du traitement HOO: {str(e)}")
            await workflow_service.handle_processing_error(
                UUID(job_id),
                f"Erreur de traitement HOO: {str(e)}"
            )
            raise

@shared_task(name="generate_channel_previews")
async def generate_channel_previews(download_result):
    """Génère des previews pour chaque canal (H-alpha, OIII, etc.)"""
    logging.info(f"Génération des previews pour les fichiers téléchargés: {download_result}")
    
    async with get_services() as (storage_service, workflow_service):
        try:
            task_id = download_result.get("task_id")
            files = download_result.get("files", [])
            
            previews = {}
            for file_info in files:
                file_path = file_info.get("path")
                filter_name = file_info.get("filter", "unknown")
                
                # Récupérer les données FITS
                fits_data = storage_service.get_fits_file(file_path)
                if not fits_data:
                    continue
                    
                # Traitement pour générer une preview
                data = fits_data["data"]
                stretched_data = apply_stf(data)  # Réutilise la fonction existante
                
                # Conversion en image
                preview_data = (stretched_data * 255).astype(np.uint8)
                image = Image.fromarray(preview_data)
                
                # Sauvegarde en mémoire
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                # Chemin dans MinIO
                preview_path = f"previews/{task_id}_{filter_name}_preview.png"
                
                # Stockage dans MinIO
                storage_service.store_preview(
                    img_byte_arr.getvalue(),
                    preview_path,
                    content_type="image/png"
                )
                
                previews[filter_name] = preview_path
            
            # Mise à jour du statut
            await workflow_service.update_processing_step(
                UUID(task_id),
                "PREVIEWS_GENERATED",
                {
                    "previews": previews
                }
            )
            
            return {
                "task_id": task_id,
                "previews": previews,
                "files": files
            }
        except Exception as e:
            logging.exception(f"Erreur lors de la génération des previews: {str(e)}")
            if task_id:
                await workflow_service.handle_processing_error(
                    UUID(task_id),
                    f"Erreur de génération des previews: {str(e)}"
                )
            raise

@shared_task(name="wait_user_validation")
async def wait_user_validation(preview_result):
    """Attend la validation utilisateur avant de continuer le traitement"""
    logging.info(f"En attente de validation utilisateur pour: {preview_result}")
    
    async with get_services() as (storage_service, workflow_service):
        try:
            task_id = preview_result.get("task_id")
            
            # Mise à jour du statut pour indiquer l'attente de validation
            await workflow_service.update_processing_step(
                UUID(task_id),
                "WAITING_VALIDATION",
                {
                    "message": "En attente de validation utilisateur",
                    "previews": preview_result.get("previews", {})
                }
            )
            
            # Pour le DemoDay, on va automatiquement "valider" après 5 secondes
            # En production, cette tâche serait mise en pause jusqu'à ce que l'utilisateur
            # valide via une API
            import time
            time.sleep(5)
            
            # Mise à jour du statut pour indiquer la validation
            await workflow_service.update_processing_step(
                UUID(task_id),
                "VALIDATION_COMPLETE",
                {
                    "message": "Validation utilisateur reçue"
                }
            )
            
            return {
                "task_id": task_id,
                "status": "validated",
                "previews": preview_result.get("previews", {}),
                "files": preview_result.get("files", [])
            }
        except Exception as e:
            logging.exception(f"Erreur lors de l'attente de validation: {str(e)}")
            if task_id:
                await workflow_service.handle_processing_error(
                    UUID(task_id),
                    f"Erreur pendant l'attente de validation: {str(e)}"
                )
            raise
