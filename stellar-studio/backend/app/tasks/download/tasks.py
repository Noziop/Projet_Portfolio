from celery import shared_task
from uuid import UUID
import logging
from contextlib import asynccontextmanager
from app.db.session import AsyncSessionLocal
from app.core.celery import celery_app
from app.services.storage.service import StorageService
from app.core.ws.manager import ConnectionManager
from astroquery.mast import Observations


# Singleton pour le WebSocket manager
ws_manager = ConnectionManager()

@asynccontextmanager
async def get_services():
    """Context manager pour créer et gérer les services"""
    
    from app.services.target.service import TargetService
    async with AsyncSessionLocal() as session:
        storage_service = StorageService()
        target_service = TargetService(
            session=session,
            storage_service=storage_service,
            ws_manager=ws_manager
        )
        try:
            yield storage_service, target_service
        finally:
            await session.close()

@shared_task(
    name="download_mast_files",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
async def download_mast_files(self, task_id: str, target_id: str, preset_id: str):
    """Télécharge les fichiers FITS depuis MAST"""
    async with get_services() as (storage_service, target_service):
        try:
            # Initialisation
            await target_service.update_download_progress(
                UUID(task_id),
                "Initialisation du téléchargement",
                0.0
            )

            # Récupération des fichiers à télécharger
            target_files = await target_service.get_target_files(UUID(target_id))
            total_files = len(target_files)
            
            downloaded_files = []
            for idx, target_file in enumerate(target_files, 1):
                try:
                    # Téléchargement depuis MAST
                    obs = Observations.get_product_list(target_file.mast_id)
                    download_path = Observations.download_file(
                        obs[0]['dataURI'],
                        cache=True
                    )

                    # Stockage dans MinIO
                    if storage_service.store_fits_file(download_path, target_file.file_path):
                        # Mise à jour du statut du fichier
                        target_file.is_downloaded = True
                        target_file.in_minio = True
                        await target_service.update_target_file(target_file)
                        
                        downloaded_files.append({
                            "id": str(target_file.id),
                            "path": target_file.file_path
                        })

                    # Mise à jour de la progression
                    progress = (idx / total_files) * 100
                    await target_service.update_download_progress(
                        UUID(task_id),
                        target_file.file_path,
                        progress
                    )

                except Exception as e:
                    logging.error(f"Erreur lors du téléchargement de {target_file.mast_id}: {str(e)}")
                    continue

            # Finalisation
            if downloaded_files:
                await target_service.complete_download(
                    UUID(task_id),
                    downloaded_files
                )
                return {
                    "status": "success",
                    "files": downloaded_files
                }
            else:
                raise Exception("Aucun fichier n'a pu être téléchargé")

        except Exception as e:
            logging.exception(f"Erreur lors du téléchargement: {str(e)}")
            raise
