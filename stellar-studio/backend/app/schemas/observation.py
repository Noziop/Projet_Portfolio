# app/schemas/observation.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.domain.value_objects.observation_types import InstrumentType, FilterType
from app.domain.value_objects.coordinates import Coordinates

class CoordinatesSchema(BaseModel):
    ra: str = Field(..., description="Ascension droite")
    dec: str = Field(..., description="Déclinaison")
    
    model_config = {
        "from_attributes": True
    }

class ObservationBase(BaseModel):
    telescope_id: str = Field(..., description="Identifiant du télescope")
    target_id: str = Field(..., description="Identifiant de la cible")
    coordinates: CoordinatesSchema
    start_time: datetime = Field(..., description="Date et heure de début de l'observation")
    exposure_time: int = Field(..., description="Temps d'exposition en secondes")
    instrument: InstrumentType
    filters: List[FilterType]

    model_config = {
        "from_attributes": True
    }

class ObservationCreate(ObservationBase):
    fits_files: List[str] = Field(default_factory=list, description="Liste des fichiers FITS")

class ObservationUpdate(BaseModel):
    telescope_id: Optional[str] = None
    target_id: Optional[str] = None
    coordinates: Optional[CoordinatesSchema] = None
    start_time: Optional[datetime] = None
    exposure_time: Optional[int] = None
    instrument: Optional[InstrumentType] = None
    filters: Optional[List[FilterType]] = None
    preview_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class ObservationInDB(ObservationBase):
    id: str
    fits_files: List[str]
    preview_url: Optional[str] = None
