from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app.api.deps import get_current_user, require_role
from app.domain.models.user import UserRole
from app.schemas.telescope import TelescopeCreate, TelescopeUpdate, TelescopeResponse

router = APIRouter(prefix="/api/v1/admin/telescopes", tags=["telescope-management"])

@router.get("/", response_model=List[TelescopeResponse])
@require_role(UserRole.ADMIN, UserRole.OPERATOR)
async def list_telescopes():
    """Liste tous les télescopes disponibles"""
    pass

@router.get("/{telescope_id}", response_model=TelescopeResponse)
@require_role(UserRole.ADMIN, UserRole.OPERATOR)
async def get_telescope(telescope_id: UUID):
    """Récupère les détails d'un télescope"""
    pass

@router.post("/", response_model=TelescopeResponse)
@require_role(UserRole.ADMIN)
async def create_telescope(telescope: TelescopeCreate):
    """Crée un nouveau télescope"""
    pass

@router.put("/{telescope_id}", response_model=TelescopeResponse)
@require_role(UserRole.ADMIN, UserRole.OPERATOR)
async def update_telescope(telescope_id: UUID, telescope: TelescopeUpdate):
    """Met à jour un télescope"""
    pass

@router.delete("/{telescope_id}")
@require_role(UserRole.ADMIN)
async def delete_telescope(telescope_id: UUID):
    """Supprime un télescope"""
    pass
