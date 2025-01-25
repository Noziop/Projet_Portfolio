# app/domain/models/observation.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from ..value_objects.coordinates import Coordinates

@dataclass
class Observation:
    id: str
    telescope_id: str
    target_id: str
    coordinates: Coordinates
    start_time: datetime
    exposure_time: int  # en secondes
    instrument: str
    filters: List[str]
    fits_files: List[str]
    preview_url: Optional[str] = None
