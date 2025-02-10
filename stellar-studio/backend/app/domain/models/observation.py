# app/domain/models/observation.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from ..value_objects.coordinates import Coordinates
from ..value_objects.observation_types import InstrumentType, FilterType

@dataclass
class Observation:
    id: str
    telescope_id: str
    target_id: str
    coordinates: Coordinates
    start_time: datetime
    exposure_time: int
    instrument: InstrumentType
    filters: List[FilterType]
    fits_files: List[str]
    preview_url: Optional[str] = None
