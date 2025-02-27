# app/api/v1/endpoints/telescopes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.telescope.service import TelescopeService
from app.schemas.telescope import TelescopeResponse, TelescopeListResponse

router = APIRouter()

@router.get("/", response_model=List[TelescopeResponse])
async def list_telescopes(
    status: Optional[str] = Query(None, description="Filtrer par statut (ONLINE, OFFLINE, MAINTENANCE)"),
    db: AsyncSession = Depends(get_db)
):
    """Liste tous les télescopes disponibles"""
    telescope_service = TelescopeService(db)
    
    if status:
        from app.domain.value_objects.telescope_types import TelescopeStatus
        try:
            status_enum = TelescopeStatus[status.upper()]
            return await telescope_service.get_by_status(status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Statut invalide: {status}")
    
    return await telescope_service.get_active_telescopes()

@router.get("/{telescope_id}", response_model=TelescopeResponse)
async def get_telescope(
    telescope_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'un télescope"""
    telescope_service = TelescopeService(db)
    telescope = await telescope_service.get_telescope(telescope_id)
    
    if not telescope:
        raise HTTPException(status_code=404, detail="Télescope non trouvé")
    
    return telescope

@router.get("/{telescope_id}/filters")
async def get_telescope_filters(
    telescope_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les filtres disponibles pour un télescope"""
    telescope_service = TelescopeService(db)
    filters = await telescope_service.get_telescope_filters(telescope_id)
    
    if not filters:
        raise HTTPException(status_code=404, detail="Filtres non trouvés ou télescope inexistant")
    
    return filters

@router.get("/{telescope_id}/presets")
async def get_telescope_presets(
    telescope_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les presets disponibles pour un télescope"""
    telescope_service = TelescopeService(db)
    presets = await telescope_service.get_telescope_presets(telescope_id)
    
    if not presets:
        raise HTTPException(status_code=404, detail="Presets non trouvés ou télescope inexistant")
    
    return presets
