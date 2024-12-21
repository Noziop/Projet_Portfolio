# app/api/v1/endpoints/telescopes.py
from fastapi import APIRouter, HTTPException
from app.services.telescope_service import (
    fetch_object_data, 
    download_fits_async, 
    get_available_targets,
    get_target_preview
)

router = APIRouter()

@router.get("/telescopes/{telescope}/targets")
async def list_telescope_targets(telescope: str):
    """Liste les cibles disponibles pour un télescope donné"""
    targets = get_available_targets(telescope)
    if not targets:
        raise HTTPException(
            status_code=404, 
            detail=f"No targets found for telescope {telescope}"
        )
    return targets

@router.get("/objects/{object_name}")
async def get_object_info(object_name: str):
    """Récupère les informations Simbad pour un objet"""
    task = fetch_object_data.delay(object_name)
    result = task.get(timeout=10)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.get("/objects/{object_name}/fits")
async def request_fits_download(object_name: str, telescope: str):
    """Initie le téléchargement des fichiers FITS"""
    task = download_fits_async.delay(object_name, telescope)
    task_id = task.id
    return {
        "task_id": task_id,
        "status": "pending",
        "message": f"Download initiated for {object_name} with {telescope}"
    }

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Vérifie le statut d'une tâche de téléchargement"""
    task = download_fits_async.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }

@router.get("/preview/{telescope}/{object_name}")
async def get_object_preview(telescope: str, object_name: str):
    """Récupère l'URL de preview pour un objet spécifique"""
    preview_url = get_target_preview(object_name, telescope)
    if not preview_url:
        raise HTTPException(
            status_code=404, 
            detail=f"No preview available for {object_name} with {telescope}"
        )
    return {"preview_url": preview_url}
