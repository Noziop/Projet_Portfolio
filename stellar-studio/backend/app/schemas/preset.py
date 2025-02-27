# app/schemas/preset.py
from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from .filter import FilterResponse
from .preset_filter import PresetFilterResponse

class ProcessingParams(BaseModel):
    """Structure des paramètres de traitement"""
    stretch_factor: float = Field(
        default=1.0,
        description="Facteur d'étirement pour le traitement"
    )
    combine_method: str = Field(
        default="mean",
        description="Méthode de combinaison des images (mean, median, etc.)"
    )
    color_balance: Dict[str, float] = Field(
        default={},
        description="Balance des couleurs par canal"
    )

class PresetBase(BaseModel):
    """Attributs communs pour tous les schemas Preset"""
    name: str = Field(
        ..., 
        description="Nom du preset",
        example="HOO",
        min_length=2,
        max_length=100
    )
    description: Optional[str] = Field(
        None,
        description="Description détaillée du preset",
        example="Traitement Ha-OIII-OIII"
    )
    processing_params: ProcessingParams = Field(
        default_factory=ProcessingParams,
        description="Paramètres de traitement"
    )

class PresetCreate(PresetBase):
    """Schema pour la création d'un preset"""
    telescope_id: UUID = Field(..., description="ID du télescope associé")
    filter_ids: List[UUID] = Field(
        ..., 
        description="Liste des IDs des filtres nécessaires"
    )

class PresetUpdate(BaseModel):
    """Schema pour la mise à jour d'un preset"""
    name: Optional[str] = None
    description: Optional[str] = None
    processing_params: Optional[ProcessingParams] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and (len(v) < 2 or len(v) > 100):
            raise ValueError("Le nom doit faire entre 2 et 100 caractères")
        return v

class PresetInDB(PresetBase):
    """Schema pour un preset en DB"""
    id: UUID
    telescope_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PresetResponse(PresetInDB):
    """Schema pour la réponse API"""
    telescope_name: Optional[str] = Field(
        None, 
        description="Nom du télescope associé"
    )
    filters: List[FilterResponse] = Field(
        default_factory=list,
        description="Liste des filtres associés"
    )
    preset_filters: List[PresetFilterResponse] = Field(
        default_factory=list,
        description="Configuration détaillée des filtres"
    )

    class Config:
        from_attributes = True
