# app/api/v1/endpoints/observations.py
from fastapi import APIRouter, Depends, HTTPException
from app.services.observation import observation_service
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/{telescope}/targets")
async def list_telescope_targets(telescope: str):
    """Liste les cibles disponibles pour un télescope donné"""
    targets = observation_service.get_available_targets(telescope)
    if not targets:
        raise HTTPException(status_code=404, detail=f"No targets found for telescope {telescope}")
    return targets

@router.get("/preview/{telescope}/{object_name}")
async def get_object_preview(telescope: str, object_name: str):
    """Récupère l'URL de preview pour un objet spécifique"""
    preview_url = observation_service.get_target_preview(object_name, telescope)
    if not preview_url:
        raise HTTPException(status_code=404, detail=f"No preview available for {object_name}")
    return {"preview_url": preview_url}
