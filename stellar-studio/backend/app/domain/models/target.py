# app/domain/models/target.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.domain.value_objects.target_types import ObjectType, TargetStatus

@dataclass
class Target:
    id: UUID
    name: str
    description: Optional[str]
    catalog_name: Optional[str]    # Pour "NGC6302"
    common_name: Optional[str]     # Pour "Butterfly Nebula"
    telescope_id: UUID
    coordinates_ra: str
    coordinates_dec: str
    object_type: ObjectType
    status: TargetStatus = TargetStatus.NEEDS_DOWNLOAD
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
