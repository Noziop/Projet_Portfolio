# app/api/v1/endpoints/telescopes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.telescopes import telescope_service
from app.schemas.telescope import TelescopeResponse

router = APIRouter(prefix="/telescopes", tags=["telescopes"])

@router.get("/", response_model=List[TelescopeResponse])
async def list_telescopes():
    """Liste tous les télescopes disponibles"""
    return telescope_service.get_telescopes()

@router.get("/{telescope_id}", response_model=TelescopeResponse)
async def get_telescope(telescope_id: str):
    """Récupère les détails d'un télescope"""
    telescope = telescope_service.get_telescope(telescope_id)
    if not telescope:
        raise HTTPException(status_code=404, detail="Telescope not found")
    return telescope
