# app/tasks/common/status.py
import logging
import traceback
from uuid import UUID

from app.db.session import SyncSessionLocal  # Import direct de la session synchrone
from app.domain.value_objects.task_types import TaskStatus
from app.infrastructure.repositories.task_repository import TaskRepository
from app.infrastructure.repositories.models import Task 

# Configuration du logging
task_logger = logging.getLogger('app.task.common.status')

def update_task_status_sync(task_id: str, status: TaskStatus, message: str = ""):
    """Version synchrone respectant les transitions d'états"""
    task_logger.info(f"Statut de la tâche {task_id} mis à jour: {status}")
    
    with SyncSessionLocal() as session:
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                task_logger.error(f"Tâche {task_id} non trouvée")
                return None
            
            # Suivre le flux des états en respectant les transitions valides
            current_status = task.status
            
            # Si on veut passer à COMPLETED mais qu'on est en PENDING,
            # il faut d'abord passer par RUNNING
            if status == TaskStatus.COMPLETED and current_status == TaskStatus.PENDING:
                task_logger.info(f"Transition intermédiaire: {current_status.name} → RUNNING")
                
                # Mise à jour en deux étapes
                task.status = TaskStatus.RUNNING
                session.commit()  # Commit intermédiaire
                
                # Puis mise à jour vers l'état final
                task.status = TaskStatus.COMPLETED
                if message:
                    task.error = message
                
                session.commit()
                return task
            
            # Sinon, mise à jour directe si la transition est valide
            task.status = status
            if message:
                task.error = message
            
            session.commit()
            return task
            
        except Exception as e:
            task_logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            session.rollback()
            return None

def check_task_status_sync(task_id: str):
    """Vérifie et log le statut d'une tâche (version synchrone)"""
    try:
        with SyncSessionLocal() as session:
            task_repository = TaskRepository(session)
            task = task_repository.get_sync(UUID(task_id))
            if task:
                return {
                    "task_id": str(task.id),
                    "status": task.status.value if hasattr(task.status, "value") else str(task.status),
                    "type": task.type if hasattr(task, "type") else "UNKNOWN",
                    "progress": task.progress if hasattr(task, "progress") else 0,
                    "error": task.error if hasattr(task, "error") else None,
                    "result": "available" if hasattr(task, "result") and task.result else "none"
                }
            return {"task_id": task_id, "status": "NOT_FOUND"}
    except Exception as e:
        task_logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
        task_logger.error(f"Traceback: {traceback.format_exc()}")
        return {"task_id": task_id, "status": "ERROR", "error": str(e)}