# app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends
from app.services.task import task_service
from app.api.deps import get_current_user
from app.schemas.task import DownloadRequest

router = APIRouter()

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Vérifie le statut d'une tâche"""
    return task_service.get_task_status(task_id)

@router.post("/download")
async def start_download(
    request: DownloadRequest,
    current_user = Depends(get_current_user)
):
    """Initie un téléchargement d'observation"""
    task = task_service.download_fits.delay(
    object_name=request.object_name, 
    telescope=request.telescope
    )

    return {"task_id": task.id}
