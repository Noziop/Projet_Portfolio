# app/domain/models/filter.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.domain.value_objects.filter_types import FilterType

@dataclass
class Filter:
    id: UUID
    name: str
    telescope_id: UUID
    wavelength: int
    description: str
    filter_type: FilterType
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
