# app/schemas/target_preset.py
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field
from .preset import PresetResponse

class TargetPresetBase(BaseModel):
    """Schema de base pour l'association Target-Preset"""
    target_id: UUID = Field(..., description="ID de la cible")
    preset_id: UUID = Field(..., description="ID du preset")
    is_available: bool = Field(
        default=True,
        description="Indique si le preset est disponible pour cette cible"
    )

class TargetPresetCreate(TargetPresetBase):
    """Schema pour la création d'une association Target-Preset"""
    pass

class TargetPresetInDB(TargetPresetBase):
    """Schema pour une association Target-Preset en DB"""
    class Config:
        from_attributes = True

class TargetPresetResponse(TargetPresetBase):
    """Schema pour la réponse API avec détails du preset"""
    preset: Optional[PresetResponse] = Field(
        None, 
        description="Détails du preset associé"
    )
    required_filters: List[str] = Field(
        default_factory=list,
        description="Liste des filtres requis pour ce preset"
    )
    missing_filters: List[str] = Field(
        default_factory=list,
        description="Liste des filtres manquants pour ce preset"
    )

    class Config:
        from_attributes = True
