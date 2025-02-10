# app/api/v1/endpoints/telescope_management.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, require_role
from app.domain.models.user import User, UserRole
from app.schemas.telescope import TelescopeCreate, TelescopeUpdate, TelescopeResponse
from app.services.telescopes import get_telescope_service
from app.services.telescopes.service import TelescopeService

router = APIRouter(prefix="/api/v1/admin/telescopes", tags=["telescope-management"])

@router.post("/", response_model=TelescopeResponse)
@require_role(UserRole.ADMIN)
async def create_telescope(
    telescope: TelescopeCreate,
    telescope_service: TelescopeService = Depends(get_telescope_service),
    current_user: User = Depends(get_current_user)
):
    """Crée un nouveau télescope"""
    try:
        return await telescope_service.create_telescope(telescope)
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
    telescope_service: TelescopeService = Depends(get_telescope_service),
    current_user: User = Depends(get_current_user)
):
    """Met à jour un télescope"""
    try:
        return await telescope_service.update_telescope(telescope_id, telescope)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )

@router.delete("/{telescope_id}")
@require_role(UserRole.ADMIN)
async def delete_telescope(
    telescope_id: str,
    telescope_service: TelescopeService = Depends(get_telescope_service),
    current_user: User = Depends(get_current_user)
):
    """Supprime un télescope"""
    try:
        await telescope_service.delete_telescope(telescope_id)
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} supprimé avec succès"
        }
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    
@router.post("/{telescope_id}/activate")
@require_role(UserRole.ADMIN)
async def activate_telescope(
    telescope_id: str,
    telescope_service: TelescopeService = Depends(get_telescope_service),
    current_user: User = Depends(get_current_user)
):
    """Active un télescope"""
    try:
        telescope = await telescope_service.activate_telescope(telescope_id)
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} activé avec succès",
            "telescope": telescope
        }
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )

@router.post("/{telescope_id}/deactivate")
@require_role(UserRole.ADMIN)
async def deactivate_telescope(
    telescope_id: str,
    telescope_service: TelescopeService = Depends(get_telescope_service),
    current_user: User = Depends(get_current_user)
):
    """Désactive un télescope"""
    try:
        telescope = await telescope_service.deactivate_telescope(telescope_id)
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} désactivé avec succès",
            "telescope": telescope
        }
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )

@router.post("/{telescope_id}/maintenance")
@require_role(UserRole.ADMIN, UserRole.OPERATOR)
async def set_maintenance_mode(
    telescope_id: str,
    telescope_service: TelescopeService = Depends(get_telescope_service),
    current_user: User = Depends(get_current_user)
):
    """Met un télescope en maintenance"""
    try:
        telescope = await telescope_service.set_maintenance_mode(telescope_id)
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} mis en maintenance avec succès",
            "telescope": telescope
        }
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )