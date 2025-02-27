# app/domain/models/preset.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from app.domain.value_objects.target_types import ObjectType

@dataclass
class Preset:
    id: UUID
    name: str
    description: str
    telescope_id: UUID
    processing_params: Dict
    target_type: ObjectType
    is_default: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
