# app/schemas/observation.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator

class ObservationBase(BaseModel):
    """Attributs communs pour tous les schemas Observation"""
    observation_date: datetime = Field(..., description="Date de l'observation")
    exposure_time: float = Field(
        ..., 
        description="Temps d'exposition en secondes",
        gt=0  # Doit être positif
    )

class ObservationCreate(ObservationBase):
    """Schema pour la création d'une observation"""
    target_id: UUID = Field(..., description="ID de la cible observée")
    telescope_id: UUID = Field(..., description="ID du télescope utilisé")

    @validator('exposure_time')
    def validate_exposure_time(cls, v):
        if v <= 0:
            raise ValueError("Le temps d'exposition doit être positif")
        return v

class ObservationUpdate(BaseModel):
    """Schema pour la mise à jour d'une observation"""
    observation_date: Optional[datetime] = None
    exposure_time: Optional[float] = None

    @validator('exposure_time')
    def validate_exposure_time(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Le temps d'exposition doit être positif")
        return v

class ObservationInDB(ObservationBase):
    """Schema pour une observation en DB"""
    id: UUID
    target_id: UUID
    telescope_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ObservationResponse(ObservationInDB):
    """Schema pour la réponse API"""
    target_name: Optional[str] = Field(None, description="Nom de la cible observée")
    telescope_name: Optional[str] = Field(None, description="Nom du télescope utilisé")
