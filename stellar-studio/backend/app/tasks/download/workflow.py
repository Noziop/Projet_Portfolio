# app/tasks/download/workflow.py
import logging
from uuid import UUID

from celery import chain, chord

from app.db.session import SyncSessionLocal
from app.core.celery import celery_app
from app.infrastructure.repositories.task_repository import TaskRepository
from app.domain.value_objects.task_types import TaskStatus

from .search import search_observations
from .select import select_files
from .download import download_chunk
from .finalize import finalize_download

# Configuration du logging
workflow_logger = logging.getLogger('app.task.download.workflow')

@celery_app.task(name="app.tasks.download.workflow.create_download_tasks")
def create_download_tasks(selection_result):
    """Crée des tâches parallèles pour chaque chunk de fichiers"""
    task_id = selection_result.get("task_id")
    
    if selection_result.get("status") != "success":
        error_msg = selection_result.get("message", "Erreur lors de la sélection des fichiers")
        workflow_logger.error(f"Sélection échouée pour {task_id}: {error_msg}")
        return selection_result
    
    file_chunks = selection_result.get("file_chunks", [])
    
    if not file_chunks:
        workflow_logger.warning(f"Aucun chunk de fichiers à télécharger pour {task_id}")
        return {
            "task_id": task_id,
            "status": "error",
            "message": "Aucun fichier à télécharger"
        }
    
    workflow_logger.info(f"Création de {len(file_chunks)} tâches de téléchargement pour {task_id}")
    
    # Créer des tâches parallèles pour chaque chunk
    parallel_tasks = []
    for i in range(len(file_chunks)):
        parallel_tasks.append(download_chunk.s(selection_result, i))
    
    # Utiliser chord pour exécuter les téléchargements en parallèle
    # puis finaliser une fois tous terminés
    chord_workflow = chord(parallel_tasks)(finalize_download.s())
    chord_workflow.apply_async()

    
    return {"status": "success", "message": f"Téléchargement lancé avec {len(parallel_tasks)} tâches parallèles"}

@celery_app.task(name="app.tasks.download.workflow.start_mast_download")
def start_mast_download(task_id, target_id, telescope_id):
    """Point d'entrée principal pour le téléchargement MAST"""
    workflow_logger.info(f"Démarrage du workflow de téléchargement: task_id={task_id}")
    
    # Mise à jour initiale du statut
    with SyncSessionLocal() as session:
        task_repo = TaskRepository(session)
        task = task_repo.get_sync(UUID(task_id))
        
        if not task:
            workflow_logger.error(f"Tâche {task_id} non trouvée")
            return {"status": "error", "message": f"Tâche {task_id} non trouvée"}
        
        task.status = TaskStatus.RUNNING
        task.error = "Démarrage du téléchargement"
        task_repo.update_sync(task)
        session.commit()
    
    # Construction et lancement du workflow
    workflow = chain(
        search_observations.s(task_id, target_id, telescope_id),
        select_files.s(),
        create_download_tasks.s()
    )
    
    workflow_logger.info(f"Lancement du workflow pour task_id={task_id}")
    workflow.apply_async()
    
    return {"status": "success", "message": "Workflow de téléchargement démarré"}

# Point d'entrée compatible avec l'existant
@celery_app.task(name="app.tasks.download.workflow.download_mast_files")
def download_mast_files(**kwargs):
    """Version ultra-simplifiée pour la démo"""
    task_id = kwargs.get("task_id")
    target_id = kwargs.get("target_id")
    telescope_id = kwargs.get("telescope_id")
    preset_id = kwargs.get("preset_id")
    
    workflow_logger.info(f"📥 Vérification/téléchargement pour: task_id={task_id}, target={target_id}")
    
    # Vérification directe avec MinIO au lieu d'utiliser check_files_exist
    from app.services.storage.service import StorageService
    storage = StorageService()
    
    try:
        # Utiliser directement le client MinIO pour vérifier les fichiers
        objects = list(storage.client.list_objects(
            storage.fits_bucket,
            prefix=f"{target_id}/",
            recursive=True
        ))
        
        # Compter les fichiers FITS
        fits_files = [obj.object_name for obj in objects 
                     if obj.object_name.endswith('.fits') or obj.object_name.endswith('.fit')]
        
        # S'il y a des fichiers, on considère que c'est bon
        if fits_files:
            nb_files = len(fits_files)
            message = f"{nb_files} fichiers disponibles"
            workflow_logger.info(f"✅ {message}")
            
            # Mettre à jour le statut
            from ..common import update_task_status_sync
            update_task_status_sync(task_id, TaskStatus.COMPLETED, message)
            
            return {"status": "success", "message": message}
        
        # Sinon lancer le workflow normal
        workflow_logger.info("⚠️ Aucun fichier existant, lancement du téléchargement complet")
        workflow = chain(
            search_observations.s(task_id, target_id, telescope_id),
            select_files.s(),
            create_download_tasks.s()
        )
        workflow.apply_async()
        return {"status": "success", "message": "Workflow de téléchargement démarré"}
    
    except Exception as e:
        workflow_logger.error(f"Erreur: {str(e)}")
        return {"status": "error", "message": str(e)}
