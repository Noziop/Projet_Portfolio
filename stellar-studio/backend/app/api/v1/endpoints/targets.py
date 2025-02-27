# app/api/v1/endpoints/targets.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.target.service import TargetService
from app.services.storage.service import StorageService
from app.core.ws.manager import ConnectionManager
from app.schemas.target import TargetResponse, TargetListResponse, TargetCreate
from app.domain.value_objects.target_types import ObjectType

router = APIRouter()

@router.get("/", response_model=List[TargetResponse])
async def list_targets(
    telescope_id: Optional[UUID] = Query(None, description="Filtrer par télescope"),
    object_type: Optional[ObjectType] = Query(None, description="Filtrer par type d'objet"),
    db: AsyncSession = Depends(get_db)
):
    """Liste les cibles disponibles, filtrable par télescope et type d'objet"""
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    if telescope_id:
        targets = await target_service.target_repository.get_by_telescope(telescope_id)
    elif object_type:
        targets = await target_service.target_repository.get_by_type(object_type)
    else:
        targets = await target_service.target_repository.get_all()
        
    return targets

@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'une cible par son ID"""
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    target = await target_service.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    
    return target

@router.get("/{target_id}/files")
async def get_target_files(
    target_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les fichiers associés à une cible"""
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    target_with_files = await target_service.get_target_with_files(target_id)
    if not target_with_files:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    
    return target_with_files["files"]

@router.get("/{target_id}/presets")
async def get_target_presets(
    target_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les presets disponibles pour une cible"""
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    presets = await target_service.get_available_presets(target_id)
    if not presets:
        raise HTTPException(status_code=404, detail="Aucun preset disponible pour cette cible")
    
    return presets

@router.get("/{target_id}/preview")
async def get_target_preview(
    target_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Récupère l'URL de preview pour une cible"""
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    preview_path = await target_service.generate_target_preview(target_id)
    if not preview_path:
        raise HTTPException(status_code=404, detail="Pas de preview disponible pour cette cible")
    
    return {"preview_url": preview_path}
