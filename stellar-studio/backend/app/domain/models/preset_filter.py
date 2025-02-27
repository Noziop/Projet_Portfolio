# app/domain/models/preset_filter.py
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass
class PresetFilter:
    preset_id: UUID
    filter_id: UUID
    filter_order: Optional[int] = None  # Pour définir l'ordre des filtres dans le preset
