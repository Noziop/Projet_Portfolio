# app/schemas/preset_filter.py
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field
from .filter import FilterResponse

class PresetFilterBase(BaseModel):
    """Schema de base pour l'association Preset-Filter"""
    preset_id: UUID = Field(..., description="ID du preset")
    filter_id: UUID = Field(..., description="ID du filtre")
    order: Optional[int] = Field(
        None, 
        description="Ordre de traitement du filtre dans le preset"
    )

class PresetFilterCreate(PresetFilterBase):
    """Schema pour la création d'une association Preset-Filter"""
    pass

class PresetFilterInDB(PresetFilterBase):
    """Schema pour une association Preset-Filter en DB"""
    class Config:
        from_attributes = True

class PresetFilterResponse(PresetFilterBase):
    """Schema pour la réponse API avec détails du filtre"""
    filter: Optional[FilterResponse] = Field(
        None, 
        description="Détails du filtre associé"
    )

    class Config:
        from_attributes = True
