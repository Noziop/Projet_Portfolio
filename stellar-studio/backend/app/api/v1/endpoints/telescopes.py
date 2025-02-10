# app/api/v1/endpoints/telescopes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.telescopes import get_telescope_service
from app.services.telescopes.service import TelescopeService
from app.schemas.telescope import TelescopeResponse

router = APIRouter(prefix="/telescopes", tags=["telescopes"])

@router.get("/", response_model=List[TelescopeResponse])
async def list_telescopes(
    telescope_service: TelescopeService = Depends(get_telescope_service)
):
    """Liste tous les télescopes disponibles"""
    return await telescope_service.list_telescopes()

@router.get("/{telescope_id}", response_model=TelescopeResponse)
async def get_telescope(
    telescope_id: str,
    telescope_service: TelescopeService = Depends(get_telescope_service)
):
    """Récupère les détails d'un télescope"""
    try:
        return await telescope_service.get_telescope(telescope_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Telescope not found")