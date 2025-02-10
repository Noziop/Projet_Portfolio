# app/domain/models/telescope.py
from dataclasses import dataclass
from typing import List, Optional
from app.domain.value_objects.telescope_types import TelescopeStatus

@dataclass
class Telescope:
    id: str
    name: str
    description: str
    aperture: str
    focal_length: str
    location: str
    instruments: List[str]
    api_endpoint: str
    status: TelescopeStatus = TelescopeStatus.OFFLINE
