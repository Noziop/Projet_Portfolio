# app/domain/models/target.py
from dataclasses import dataclass
from ..value_objects.coordinates import Coordinates

@dataclass
class Target:
    id: str
    name: str
    description: str
    telescope_id: str
    coordinates: Coordinates
    object_type: str  # 'nebula', 'galaxy', etc.
