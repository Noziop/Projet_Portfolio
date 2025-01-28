from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, require_role, get_db
from app.domain.models.user import User, UserRole
from app.schemas.telescope import TelescopeCreate, TelescopeUpdate, TelescopeResponse
from app.infrastructure.repositories.telescope_repository import TelescopeRepository

router = APIRouter(prefix="/api/v1/admin/telescopes", tags=["telescope-management"])

@router.post("/", response_model=TelescopeResponse)
@require_role(UserRole.ADMIN)
async def create_telescope(
    telescope: TelescopeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crée un nouveau télescope"""
    try:
        telescope_repo = TelescopeRepository(db)
        new_telescope = await telescope_repo.create(telescope)
        return TelescopeResponse.from_orm(new_telescope)
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Un télescope avec cet ID existe déjà"
        )
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Met à jour un télescope"""
    telescope_repo = TelescopeRepository(db)
    existing_telescope = await telescope_repo.get_by_id(telescope_id)
    
    if not existing_telescope:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    
    try:
        updated_telescope = await telescope_repo.update(telescope_id, telescope)
        return TelescopeResponse.from_orm(updated_telescope)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour du télescope: {str(e)}"
        )

@router.delete("/{telescope_id}")
@require_role(UserRole.ADMIN)
async def delete_telescope(
    telescope_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprime un télescope"""
    telescope_repo = TelescopeRepository(db)
    existing_telescope = await telescope_repo.get_by_id(telescope_id)
    
    if not existing_telescope:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    
    try:
        await telescope_repo.delete(telescope_id)
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} supprimé avec succès"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression du télescope: {str(e)}"
        )

@router.post("/{telescope_id}/deactivate")
@require_role(UserRole.ADMIN)
async def deactivate_telescope(
    telescope_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Désactive un télescope"""
    telescope_repo = TelescopeRepository(db)
    existing_telescope = await telescope_repo.get_by_id(telescope_id)
    
    if not existing_telescope:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    
    try:
        await telescope_repo.deactivate(telescope_id)
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} désactivé avec succès"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la désactivation du télescope: {str(e)}"
        )

@router.post("/{telescope_id}/activate")
@require_role(UserRole.ADMIN)
async def activate_telescope(
    telescope_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Active un télescope"""
    telescope_repo = TelescopeRepository(db)
    existing_telescope = await telescope_repo.get_by_id(telescope_id)
    
    if not existing_telescope:
        raise HTTPException(
            status_code=404,
            detail="Télescope non trouvé"
        )
    
    try:
        await telescope_repo.activate(telescope_id)
        return {
            "status": "success",
            "message": f"Télescope {telescope_id} activé avec succès"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'activation du télescope: {str(e)}"
        )
