# app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends
from app.services.task_manager import TaskManager
from app.api.deps import get_current_user
from app.services.telescope_service import fetch_object_data, download_fits_async

router = APIRouter()

@router.get("/")
async def get_user_tasks(current_user = Depends(get_current_user)):
    """Liste toutes les tâches de l'utilisateur"""
    return await TaskManager.get_user_tasks(current_user.id)

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Vérifie le statut d'une tâche"""
    task = download_fits_async.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
