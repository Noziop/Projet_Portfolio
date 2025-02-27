# app/domain/models/observation.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class Observation:
    id: UUID
    target_id: UUID
    telescope_id: UUID
    observation_date: datetime
    exposure_time: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
