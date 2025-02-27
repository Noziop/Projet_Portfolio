# app/api/v1/endpoints/presets.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.infrastructure.repositories.preset_repository import PresetRepository
from app.infrastructure.repositories.target_preset_repository import TargetPresetRepository
from app.schemas.preset import PresetResponse, PresetCreate, PresetUpdate
from app.domain.value_objects.target_types import ObjectType

router = APIRouter()

@router.get("/", response_model=List[PresetResponse])
async def list_presets(
    target_id: Optional[UUID] = Query(None, description="Filtrer par cible"),
    telescope_id: Optional[UUID] = Query(None, description="Filtrer par télescope"),
    db: AsyncSession = Depends(get_db)
):
    """Liste tous les presets disponibles, filtrable par cible ou télescope"""
    preset_repo = PresetRepository(db)
    target_preset_repo = TargetPresetRepository(db)
    
    if target_id:
        # Récupérer les presets pour une cible spécifique
        target_presets = await target_preset_repo.get_by_target(target_id)
        preset_ids = [UUID(tp.preset_id) for tp in target_presets]
        presets = []
        for preset_id in preset_ids:
            preset = await preset_repo.get(preset_id)
            if preset:
                presets.append(preset)
        return presets
    elif telescope_id:
        # Récupérer les presets pour un télescope spécifique
        return await preset_repo.get_by_telescope(telescope_id)
    else:
        # Récupérer tous les presets
        return await preset_repo.get_all()

@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'un preset par son ID"""
    preset_repo = PresetRepository(db)
    preset = await preset_repo.get(preset_id)
    
    if not preset:
        raise HTTPException(status_code=404, detail="Preset non trouvé")
    
    return preset

@router.get("/type/{object_type}", response_model=List[PresetResponse])
async def get_presets_by_type(
    object_type: ObjectType,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les presets disponibles pour un type d'objet"""
    preset_repo = PresetRepository(db)
    presets = await preset_repo.get_by_object_type(object_type)
    
    if not presets:
        raise HTTPException(status_code=404, detail=f"Aucun preset trouvé pour le type {object_type}")
    
    return presets
