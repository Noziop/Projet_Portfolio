# app/domain/models/telescope.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from app.domain.value_objects.telescope_types import TelescopeStatus

@dataclass
class SpaceTelescope:
    id: UUID
    name: str
    description: str
    aperture: str
    focal_length: str
    location: str
    instruments: Dict[str, str]
    api_endpoint: str
    status: TelescopeStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
