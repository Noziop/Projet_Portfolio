# app/schemas/target.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from app.domain.value_objects.target_types import ObjectType, TargetStatus
from .target_preset import TargetPresetResponse
from .target_file import TargetFileStats

class Coordinates(BaseModel):
    """Schema pour les coordonnées célestes"""
    ra: str = Field(..., description="Ascension droite")
    dec: str = Field(..., description="Déclinaison")

    @validator('ra')
    def validate_ra(cls, v):
        # Format: HH:MM:SS.ss
        if not v.count(':') == 2:
            raise ValueError("Format RA invalide, utilisez HH:MM:SS.ss")
        return v

    @validator('dec')
    def validate_dec(cls, v):
        # Format: DD:MM:SS.ss
        if not v.count(':') == 2:
            raise ValueError("Format DEC invalide, utilisez DD:MM:SS.ss")
        return v

class TargetBase(BaseModel):
    """Attributs communs pour tous les schemas Target"""
    name: str = Field(
        ..., 
        description="Nom principal de la cible",
        min_length=2,
        max_length=255
    )
    description: Optional[str] = Field(None, description="Description de la cible")
    catalog_name: Optional[str] = Field(
        None, 
        description="Nom dans le catalogue (ex: NGC6302)",
        max_length=100
    )
    common_name: Optional[str] = Field(
        None, 
        description="Nom commun (ex: Butterfly Nebula)",
        max_length=255
    )
    coordinates_ra: str = Field(..., description="Ascension droite")
    coordinates_dec: str = Field(..., description="Déclinaison")
    object_type: ObjectType = Field(..., description="Type d'objet céleste")

class TargetCreate(TargetBase):
    """Schema pour la création d'une cible"""
    telescope_id: UUID = Field(..., description="ID du télescope associé")

class TargetUpdate(BaseModel):
    """Schema pour la mise à jour d'une cible"""
    name: Optional[str] = None
    description: Optional[str] = None
    catalog_name: Optional[str] = None
    common_name: Optional[str] = None
    coordinates_ra: Optional[str] = None
    coordinates_dec: Optional[str] = None
    status: Optional[TargetStatus] = None

class TargetInDB(TargetBase):
    """Schema pour une cible en DB"""
    id: UUID
    telescope_id: UUID
    status: TargetStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TargetResponse(TargetInDB):
    """Schema pour la réponse API"""
    telescope_name: Optional[str] = Field(None, description="Nom du télescope")
    coordinates: Coordinates = Field(
        ...,
        description="Coordonnées formatées"
    )
    available_presets: List[TargetPresetResponse] = Field(
        default_factory=list,
        description="Presets disponibles pour cette cible"
    )
    file_stats: Optional[TargetFileStats] = Field(
        None,
        description="Statistiques des fichiers associés"
    )
    preview_url: Optional[str] = Field(
        None,
        description="URL de la preview de la cible"
    )

    class Config:
        from_attributes = True

class TargetListResponse(BaseModel):
    """Schema pour la liste paginée des cibles"""
    items: List[TargetResponse]
    total: int
    page: int
    size: int
