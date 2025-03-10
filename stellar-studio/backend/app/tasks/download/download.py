# app/tasks/download/download.py
import logging
import traceback
import os
import tempfile
from uuid import UUID

# Import de celery_app uniquement (sans shared_task inutilisé)
from astroquery.mast import Observations

from app.db.session import SyncSessionLocal
from app.core.celery import celery_app
from app.domain.value_objects.task_types import TaskStatus
from app.services.storage.service import StorageService

# Configuration du logging
download_logger = logging.getLogger('app.task.download.download')

@celery_app.task(name="app.tasks.download.download_chunk")
def download_chunk(selection_result, chunk_index):
    """Télécharge un groupe spécifique de fichiers"""
    task_id = selection_result["task_id"]
    target_id = selection_result["target_id"]
    telescope_id = selection_result["telescope_id"]
    
    # Vérifier que le chunk existe
    if "file_chunks" not in selection_result or chunk_index >= len(selection_result["file_chunks"]):
        error_msg = f"Chunk {chunk_index} non trouvé dans la sélection"
        download_logger.error(error_msg)
        return {
            "task_id": task_id,
            "chunk_index": chunk_index,
            "status": "error",
            "message": error_msg,
            "downloaded_files": []
        }
    
    # Récupérer les fichiers pour ce chunk
    files = selection_result["file_chunks"][chunk_index]
    downloaded_files = []
    
    download_logger.info(f"Téléchargement du chunk {chunk_index} avec {len(files)} fichiers")
    
    with SyncSessionLocal() as session:
        # Services nécessaires
        storage_service = StorageService()
        
        # Obtenir le service Target (version synchrone)
        from app.services.target.service import TargetService
        from app.core.ws.manager import ConnectionManager
        # Utiliser une instance du ConnectionManager qui a des méthodes synchrones
        connection_manager = ConnectionManager()
        target_service = TargetService(session, storage_service, connection_manager)
        
        # Créer un répertoire temporaire pour le téléchargement
        download_path = tempfile.mkdtemp()
        download_logger.info(f"Répertoire temporaire créé: {download_path}")
        
        try:
            for file_idx, file_info in enumerate(files):
                try:
                    filename = file_info["filename"]
                    observation_id = file_info["observation_id"]
                    
                    download_logger.info(f"Téléchargement du fichier {file_idx+1}/{len(files)}: {filename}")
                    
                    # Préparation pour le téléchargement MAST
                    products_subset = [file_info["product_data"]]
                    
                    # Téléchargement via MAST
                    try:
                        manifest = Observations.download_products(
                            products=products_subset,
                            download_dir=download_path
                        )
                        
                        if not manifest or len(manifest) == 0:
                            download_logger.warning(f"Aucun manifeste retourné pour {filename}")
                            continue
                            
                        download_logger.info(f"Manifeste obtenu avec {len(manifest)} entrées")
                    except Exception as e:
                        download_logger.error(f"Erreur lors du téléchargement MAST: {str(e)}")
                        continue
                    
                    # Recherche du fichier téléchargé
                    local_path = None
                    if 'Local Path' in manifest.columns:
                        for path in manifest['Local Path']:
                            if path and os.path.exists(path):
                                local_path = path
                                break
                    
                    if not local_path:
                        expected_path = os.path.join(download_path, filename)
                        if os.path.exists(expected_path):
                            local_path = expected_path
                    
                    if not local_path or not os.path.exists(local_path):
                        download_logger.error(f"Fichier introuvable après téléchargement: {filename}")
                        continue
                    
                    download_logger.info(f"Fichier téléchargé: {local_path}")
                    
                    # Stockage dans MinIO
                    object_name = f"{target_id}/{filename}"
                    if storage_service.store_fits_file(local_path, object_name):
                        download_logger.info(f"Fichier stocké dans MinIO: {object_name}")
                        
                        # Enregistrement en base de données
                        file_size = os.path.getsize(local_path)
                        mast_id = f"mast:/{filename}"
                        
                        # Version synchrone de add_file_from_mast
                        target_file = target_service.add_file_from_mast_sync(
                            target_id=UUID(target_id),
                            file_path=object_name,
                            mast_id=mast_id,
                            file_size=file_size,
                            telescope_id=UUID(telescope_id)
                        )
                        
                        if target_file:
                            downloaded_files.append({
                                "path": object_name,
                                "size": file_size,
                                "observation_id": observation_id,
                                "filename": filename,
                                "success": True
                            })
                        else:
                            download_logger.warning(f"Échec d'enregistrement en base: {filename}")
                    else:
                        download_logger.error(f"Échec de stockage MinIO: {filename}")
                    
                    # Nettoyage du fichier local
                    try:
                        os.remove(local_path)
                    except:
                        pass
                
                except Exception as e:
                    download_logger.error(f"Erreur de traitement du fichier {file_idx}: {str(e)}")
                    continue
            
            # Nettoyage du répertoire temporaire
            try:
                import shutil
                shutil.rmtree(download_path, ignore_errors=True)
            except:
                pass
            
            return {
                "task_id": task_id,
                "chunk_index": chunk_index,
                "status": "success",
                "downloaded_files": downloaded_files
            }
            
        except Exception as e:
            download_logger.error(f"Erreur dans le téléchargement du chunk {chunk_index}: {str(e)}")
            download_logger.error(traceback.format_exc())
            
            # Nettoyage du répertoire temporaire en cas d'erreur
            try:
                import shutil
                shutil.rmtree(download_path, ignore_errors=True)
            except:
                pass
                
            return {
                "task_id": task_id,
                "chunk_index": chunk_index,
                "status": "error",
                "message": str(e),
                "downloaded_files": downloaded_files
            }
