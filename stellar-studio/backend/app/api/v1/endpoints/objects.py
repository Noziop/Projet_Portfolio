# app/api/v1/endpoints/objects.py  # Nouveau fichier pour la gestion des objets
from fastapi import APIRouter, HTTPException
from app.services.telescope_service import fetch_object_data

router = APIRouter()

@router.get("/{object_name}")
async def get_object_info(object_name: str):
    """Récupère les informations Simbad pour un objet"""
    task = fetch_object_data.delay(object_name)
    result = task.get(timeout=10)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result
