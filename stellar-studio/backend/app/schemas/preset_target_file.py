# app/schemas/preset_target_file.py
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field
from .target_file import TargetFileResponse

class PresetTargetFileBase(BaseModel):
    """Schema de base pour l'association Preset-TargetFile"""
    preset_id: UUID = Field(..., description="ID du preset")
    target_file_id: UUID = Field(..., description="ID du fichier cible")
    order: int = Field(..., description="Ordre de traitement du fichier")

class PresetTargetFileCreate(PresetTargetFileBase):
    """Schema pour la création d'une association Preset-TargetFile"""
    pass

class PresetTargetFileInDB(PresetTargetFileBase):
    """Schema pour une association Preset-TargetFile en DB"""
    class Config:
        from_attributes = True

class PresetTargetFileResponse(PresetTargetFileBase):
    """Schema pour la réponse API avec détails du fichier"""
    target_file: Optional[TargetFileResponse] = Field(
        None, 
        description="Détails du fichier cible associé"
    )

    class Config:
        from_attributes = True
