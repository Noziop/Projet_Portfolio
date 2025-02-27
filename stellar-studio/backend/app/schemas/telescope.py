# app/schemas/telescope.py
from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, validator
from app.domain.value_objects.telescope_types import TelescopeStatus

class Instrument(BaseModel):
    """Schema pour un instrument du télescope"""
    name: str = Field(..., description="Nom de l'instrument")
    description: str = Field(..., description="Description de l'instrument")
    wavelength_range: Optional[str] = Field(None, description="Gamme de longueurs d'onde")
    resolution: Optional[str] = Field(None, description="Résolution de l'instrument")

class TelescopeBase(BaseModel):
    """Attributs communs pour tous les schemas SpaceTelescope"""
    name: str = Field(
        ..., 
        description="Nom du télescope",
        min_length=2,
        max_length=255
    )
    description: Optional[str] = Field(None, description="Description du télescope")
    aperture: str = Field(
        ..., 
        description="Diamètre du miroir principal",
        example="2.4m"
    )
    focal_length: str = Field(
        ..., 
        description="Longueur focale",
        example="57.6m"
    )
    location: str = Field(
        ..., 
        description="Position du télescope",
        example="Low Earth Orbit"
    )
    instruments: Dict[str, Instrument] = Field(
        ...,
        description="Instruments disponibles"
    )
    api_endpoint: HttpUrl = Field(
        ...,
        description="Point d'accès API MAST"
    )
    status: TelescopeStatus = Field(
        ...,
        description="Statut opérationnel du télescope"
    )

class TelescopeCreate(TelescopeBase):
    """Schema pour la création d'un télescope"""
    pass

class TelescopeUpdate(BaseModel):
    """Schema pour la mise à jour d'un télescope"""
    name: Optional[str] = None
    description: Optional[str] = None
    aperture: Optional[str] = None
    focal_length: Optional[str] = None
    location: Optional[str] = None
    instruments: Optional[Dict[str, Instrument]] = None
    api_endpoint: Optional[HttpUrl] = None
    status: Optional[TelescopeStatus] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and (len(v) < 2 or len(v) > 255):
            raise ValueError("Le nom doit faire entre 2 et 255 caractères")
        return v

class TelescopeInDB(TelescopeBase):
    """Schema pour un télescope en DB"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TelescopeStats(BaseModel):
    """Statistiques du télescope"""
    total_targets: int = Field(..., description="Nombre total de cibles")
    total_observations: int = Field(..., description="Nombre total d'observations")
    total_processing_jobs: int = Field(..., description="Nombre total de traitements")
    available_filters: List[str] = Field(..., description="Filtres disponibles")
    storage_usage: float = Field(..., description="Espace de stockage utilisé (Go)")

class TelescopeResponse(TelescopeInDB):
    """Schema pour la réponse API"""
    stats: Optional[TelescopeStats] = Field(
        None,
        description="Statistiques du télescope"
    )
    available_presets: List[str] = Field(
        default_factory=list,
        description="Presets disponibles"
    )
    health_status: Dict[str, bool] = Field(
        default_factory=dict,
        description="État des services (API, Storage, etc.)"
    )

    class Config:
        from_attributes = True

class TelescopeListResponse(BaseModel):
    """Schema pour la liste paginée des télescopes"""
    items: List[TelescopeResponse]
    total: int
    page: int
    size: int
