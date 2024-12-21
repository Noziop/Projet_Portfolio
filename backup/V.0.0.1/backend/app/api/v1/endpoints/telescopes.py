# app/api/v1/endpoints/telescopes.py
from fastapi import APIRouter, HTTPException
from app.services.telescope_service import TelescopeService
from typing import Dict, Optional

router = APIRouter()

@router.get("/telescopes/{telescope_id}/target/{target}")
async def get_telescope_target(
    telescope_id: str,
    target: str
) -> Dict:
    """Récupère les métadonnées d'une cible"""
    result = await TelescopeService.get_target_image(telescope_id, target)
    if not result:
        raise HTTPException(status_code=404, detail="Target not found")
    return result

@router.get("/telescopes/{telescope_id}/target/{target}/fits")
async def download_target_fits(
    telescope_id: str,
    target: str
) -> Dict:
    """Télécharge les fichiers FITS d'une cible"""
    result = await TelescopeService.download_target_fits(telescope_id, target)
    if not result:
        raise HTTPException(
            status_code=404, 
            detail=f"No FITS files found for {target} with telescope {telescope_id}"
        )
    return result

@router.get("/telescopes/{telescope_id}/targets")
async def list_available_targets(telescope_id: str) -> Dict:
    """Liste les cibles disponibles pour un télescope"""
    targets = TelescopeService.ICONIC_TARGETS.get(telescope_id.lower(), {})
    if not targets:
        raise HTTPException(status_code=404, detail="Telescope not found")
    return {"targets": list(targets.keys())}
