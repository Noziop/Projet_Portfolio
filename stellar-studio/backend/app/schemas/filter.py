# app/schemas/filter.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.domain.value_objects.filter_types import FilterType

class FilterBase(BaseModel):
    """Attributs communs pour tous les schemas Filter"""
    name: str = Field(..., description="Nom du filtre", example="H-alpha")
    wavelength: int = Field(..., description="Longueur d'onde en nanomètres", example=656)
    filter_type: FilterType = Field(..., description="Type de filtre")
    description: Optional[str] = Field(None, description="Description du filtre")

class FilterCreate(FilterBase):
    """Schema pour la création d'un filtre"""
    telescope_id: UUID = Field(..., description="ID du télescope associé")

class FilterUpdate(BaseModel):
    """Schema pour la mise à jour d'un filtre"""
    name: Optional[str] = None
    wavelength: Optional[int] = None
    description: Optional[str] = None
    filter_type: Optional[FilterType] = None

class FilterInDB(FilterBase):
    """Schema pour un filtre en DB"""
    id: UUID
    telescope_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FilterResponse(FilterInDB):
    """Schema pour la réponse API"""
    telescope_name: Optional[str] = Field(None, description="Nom du télescope associé")
