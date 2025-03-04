from celery import shared_task
from uuid import UUID
import logging
import asyncio
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

def auto_stf(data: np.ndarray, target_background: float = 0.25, shadow_protection: float = 0.0, tolerance: float = 0.0015) -> np.ndarray:
    """
    Implémente une version de l'AutoSTF inspirée de PixInsight.
    
    Args:
        data: L'image d'entrée en numpy array
        target_background: Niveau cible pour le fond de ciel (0.25 = 25%)
        shadow_protection: Protection des ombres (0-1)
        tolerance: Tolérance pour la convergence
        
    Returns:
        Image étirée
    """
    # 1. Calcul des statistiques robustes
    median = np.median(data)
    mad = np.median(np.abs(data - median))
    
    # 2. Estimation du bruit
    noise = 1.4826 * mad  # Estimation robuste de l'écart-type
    
    # 3. Détection du fond de ciel (background)
    # Utilise une approche itérative pour trouver le mode
    hist, bins = np.histogram(data, bins=1000)
    peak_idx = np.argmax(hist)
    background = (bins[peak_idx] + bins[peak_idx + 1]) / 2
    
    # 4. Détection des pixels significatifs
    # Pixels au-dessus du niveau de bruit
    significant_pixels = data[data > (background + 3 * noise)]
    
    if len(significant_pixels) > 0:
        # 5. Calcul du point de référence pour les hautes lumières
        # Utilise le 99.5 percentile des pixels significatifs
        highlights = np.percentile(significant_pixels, 99.5)
    else:
        highlights = background + 3 * noise
    
    # 6. Protection des ombres
    shadows = background + shadow_protection * (highlights - background)
    
    # 7. Application de la transformation
    # Ajuste le background au niveau cible
    m = target_background / (background - shadows)
    b = -m * shadows
    
    # Application de la transformation
    stretched = m * data + b
    
    return np.clip(stretched, 0, 1)

# Alias pour la compatibilité avec le code existant
apply_stf = auto_stf

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

async def _process_hoo_preset_async(job_id: str, target_id: str, files: list):
    """Version asynchrone du traitement HOO"""
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

@shared_task(name="app.tasks.processing.tasks.process_hoo_preset")
def process_hoo_preset(job_id: str, target_id: str, files: list):
    """Tâche Celery pour le traitement HOO"""
    return asyncio.run(_process_hoo_preset_async(job_id, target_id, files))

async def _generate_channel_previews_async(download_result):
    """Version asynchrone de la génération des previews"""
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

@shared_task(name="app.tasks.processing.tasks.generate_channel_previews")
def generate_channel_previews(download_result):
    """Tâche Celery pour la génération des previews"""
    return asyncio.run(_generate_channel_previews_async(download_result))

async def _wait_user_validation_async(preview_result):
    """Version asynchrone de l'attente de validation"""
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

@shared_task(name="app.tasks.processing.tasks.wait_user_validation")
def wait_user_validation(preview_result):
    """Tâche Celery pour l'attente de validation utilisateur"""
    return asyncio.run(_wait_user_validation_async(preview_result))
