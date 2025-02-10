# app/schemas/telescope.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.domain.value_objects.telescope_types import TelescopeStatus

class TelescopeBase(BaseModel):
    name: str
    description: Optional[str] = None
    aperture: str  # Stocké comme "2.4m"
    focal_length: str  # Stocké comme "57.6m"
    location: str
    instruments: List[str]
    api_endpoint: str
    status: TelescopeStatus = TelescopeStatus.OFFLINE

class TelescopeCreate(TelescopeBase):
    id: str  # ID unique comme "HST"

class TelescopeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    aperture: Optional[str] = None
    focal_length: Optional[str] = None
    location: Optional[str] = None
    instruments: Optional[List[str]] = None
    api_endpoint: Optional[str] = None
    status: Optional[TelescopeStatus] = None

class TelescopeResponse(TelescopeBase):
    id: str
    created_at: datetime
    last_maintenance: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
