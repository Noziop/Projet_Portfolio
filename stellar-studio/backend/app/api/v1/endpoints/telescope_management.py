# app/api/v1/endpoints/telescope_management.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, require_role
from app.domain.models.user import User, UserRole
from app.schemas.telescope import TelescopeCreate, TelescopeUpdate, TelescopeResponse
from app.services.telescopes import telescope_service

router = APIRouter(prefix="/api/v1/admin/telescopes", tags=["telescope-management"])

@router.post("/", response_model=TelescopeResponse)
@require_role(UserRole.ADMIN)
async def create_telescope(
    telescope: TelescopeCreate,
    current_user: User = Depends(get_current_user)
):
    """Crée un nouveau télescope"""
    try:
        return telescope_service.create_telescope(telescope)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création du télescope: {str(e)}"
        )

@router.put("/{telescope_id}", response_model=TelescopeResponse)
@require_role(UserRole.ADMIN, UserRole.OPERATOR)
async def update_telescope(
    telescope_id: str,
    telescope: TelescopeUpdate,
    current_user: User = Depends(get_current_user)
):
    """Met à jour un télescope"""
    updated_telescope = telescope_service.update_telescope(telescope_id, telescope)
    if not updated_telescope:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    return updated_telescope

@router.delete("/{telescope_id}")
@require_role(UserRole.ADMIN)
async def delete_telescope(
    telescope_id: str,
    current_user: User = Depends(get_current_user)
):
    """Supprime un télescope"""
    if not telescope_service.get_telescope(telescope_id):
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    
    if telescope_service.delete_telescope(telescope_id):
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} supprimé avec succès"
        }
    raise HTTPException(
        status_code=500,
        detail="Erreur lors de la suppression du télescope"
    )

@router.post("/{telescope_id}/deactivate")
@require_role(UserRole.ADMIN)
async def deactivate_telescope(
    telescope_id: str,
    current_user: User = Depends(get_current_user)
):
    """Désactive un télescope"""
    if not telescope_service.get_telescope(telescope_id):
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    
    if telescope_service.deactivate_telescope(telescope_id):
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} désactivé avec succès"
        }
    raise HTTPException(
        status_code=500,
        detail="Erreur lors de la désactivation du télescope"
    )

@router.post("/{telescope_id}/activate")
@require_role(UserRole.ADMIN)
async def activate_telescope(
    telescope_id: str,
    current_user: User = Depends(get_current_user)
):
    """Active un télescope"""
    if not telescope_service.get_telescope(telescope_id):
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    
    if telescope_service.activate_telescope(telescope_id):
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} activé avec succès"
        }
    raise HTTPException(
        status_code=500,
        detail="Erreur lors de l'activation du télescope"
    )
