# app/schemas/telescope.py
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class TelescopeBase(BaseModel):
    name: str
    description: Optional[str] = None
    aperture: str  # Changé de float à str car stocké comme "2.4m"
    focal_length: str  # Changé de float à str car stocké comme "57.6m"
    location: str
    instruments: Dict[str, str]  # Changé pour accepter string->string
    api_endpoint: str

class TelescopeCreate(TelescopeBase):
    id: str  # On utilise str au lieu de UUID car on a des IDs comme "HST"

class TelescopeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    aperture: Optional[str] = None
    focal_length: Optional[str] = None
    location: Optional[str] = None
    instruments: Optional[Dict[str, str]] = None
    api_endpoint: Optional[str] = None

class TelescopeResponse(TelescopeBase):
    id: str
    
    model_config = {
        "from_attributes": True
    }
