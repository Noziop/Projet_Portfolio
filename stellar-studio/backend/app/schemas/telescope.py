# app/schemas/telescope.py
from pydantic import BaseModel
from typing import Optional

class TelescopeCreate(BaseModel):
    name: str
    description: Optional[str]
    aperture: float
    focal_length: float
    location: str
    instruments: dict

class TelescopeUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    aperture: Optional[float]
    focal_length: Optional[float]
    location: Optional[str]
    instruments: Optional[dict]
