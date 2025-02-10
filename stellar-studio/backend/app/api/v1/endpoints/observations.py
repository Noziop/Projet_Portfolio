# app/api/v1/endpoints/observations.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.observation import observation_service
from app.api.deps import get_current_user, require_role
from app.domain.value_objects.user_types import UserRole
from app.schemas.observation import (
    ObservationCreate,
    ObservationUpdate,
    ObservationInDB
)

router = APIRouter()

@router.get("/{telescope}/targets")
async def list_telescope_targets(
    telescope: str,
    current_user = Depends(get_current_user)
):
    """Liste les cibles disponibles pour un télescope donné"""
    targets = await observation_service.get_available_targets(telescope)
    if not targets:
        raise HTTPException(status_code=404, detail=f"Aucune cible trouvée pour le télescope {telescope}")
    return targets

@router.get("/preview/{telescope}/{object_name}")
async def get_object_preview(
    telescope: str,
    object_name: str,
    current_user = Depends(get_current_user)
):
    """Récupère l'URL de preview pour un objet spécifique"""
    preview_url = await observation_service.get_target_preview(object_name, telescope)
    if not preview_url:
        raise HTTPException(status_code=404, detail=f"Pas de preview disponible pour {object_name}")
    return {"preview_url": preview_url}

@router.post("/", response_model=ObservationInDB)
@require_role(UserRole.ADMIN)
async def create_observation(
    observation: ObservationCreate,
    current_user = Depends(get_current_user)
):
    """Crée une nouvelle observation"""
    return await observation_service.create_observation(**observation.model_dump())

@router.get("/{observation_id}", response_model=ObservationInDB)
async def get_observation(
    observation_id: str,
    current_user = Depends(get_current_user)
):
    """Récupère une observation par son ID"""
    return await observation_service.get_observation(observation_id)

@router.patch("/{observation_id}", response_model=ObservationInDB)
@require_role(UserRole.ADMIN)
async def update_observation(
    observation_id: str,
    observation: ObservationUpdate,
    current_user = Depends(get_current_user)
):
    """Met à jour une observation existante"""
    return await observation_service.update_observation(
        observation_id,
        **observation.model_dump(exclude_unset=True)
    )

@router.delete("/{observation_id}")
@require_role(UserRole.ADMIN)
async def delete_observation(
    observation_id: str,
    current_user = Depends(get_current_user)
):
    """Supprime une observation"""
    await observation_service.delete_observation(observation_id)
    return {"message": "Observation supprimée avec succès"}
