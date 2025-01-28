# app/api/v1/endpoints/telescopes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.telescope import TelescopeResponse
from app.infrastructure.repositories.models.telescope import SpaceTelescope

router = APIRouter(prefix="/telescopes", tags=["telescopes"])

@router.get("/", response_model=List[TelescopeResponse])
async def list_telescopes(db: Session = Depends(get_db)):
    """Liste tous les télescopes disponibles"""
    telescopes = db.query(SpaceTelescope).all()
    return [TelescopeResponse.from_orm(telescope) for telescope in telescopes]

@router.get("/{telescope_id}", response_model=TelescopeResponse)
async def get_telescope(telescope_id: str, db: Session = Depends(get_db)):
    """Récupère les détails d'un télescope"""
    telescope = db.query(SpaceTelescope).filter(SpaceTelescope.id == telescope_id).first()
    if not telescope:
        raise HTTPException(status_code=404, detail="Telescope not found")
    return TelescopeResponse.from_orm(telescope)
