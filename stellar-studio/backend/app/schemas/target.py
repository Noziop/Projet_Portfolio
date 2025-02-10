# app/schemas/target.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.domain.value_objects.target_types import ObjectType

class CoordinatesSchema(BaseModel):
    ra: str = Field(..., description="Right Ascension")
    dec: str = Field(..., description="Declination")

class TargetBase(BaseModel):
    name: str
    description: Optional[str] = None
    telescope_id: str
    coordinates: CoordinatesSchema
    object_type: ObjectType

class TargetCreate(TargetBase):
    pass

class TargetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    telescope_id: Optional[str] = None
    coordinates: Optional[CoordinatesSchema] = None
    object_type: Optional[ObjectType] = None

class TargetInDB(TargetBase):
    id: str
    
    class Config:
        from_attributes = True
