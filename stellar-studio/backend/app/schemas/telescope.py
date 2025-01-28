from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID

class TelescopeBase(BaseModel):
    name: str = Field(..., description="Nom du télescope")
    description: Optional[str] = Field(None, description="Description du télescope")
    aperture: float = Field(..., description="Ouverture en millimètres", gt=0)
    focal_length: float = Field(..., description="Longueur focale en millimètres", gt=0)
    location: str = Field(..., description="Localisation du télescope")
    instruments: Dict[str, dict] = Field(
        default_factory=dict,
        description="Instruments attachés au télescope"
    )

class TelescopeCreate(TelescopeBase):
    pass

class TelescopeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    aperture: Optional[float] = Field(None, gt=0)
    focal_length: Optional[float] = Field(None, gt=0)
    location: Optional[str] = None
    instruments: Optional[Dict[str, dict]] = None

class TelescopeResponse(TelescopeBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Hubble Space Telescope",
                "description": "NASA's flagship space telescope",
                "aperture": 2400.0,
                "focal_length": 57600.0,
                "location": "Low Earth Orbit",
                "instruments": {
                    "WFC3": {"type": "camera", "wavelength": "visible/IR"},
                    "COS": {"type": "spectrograph", "wavelength": "UV"}
                },
                "created_at": "2024-01-28T00:00:00",
                "updated_at": None,
                "is_active": True
            }
        }
    }
