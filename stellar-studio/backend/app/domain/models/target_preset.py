# app/domain/models/target_preset.py
from dataclasses import dataclass
from uuid import UUID

@dataclass
class TargetPreset:
    target_id: UUID
    preset_id: UUID
    is_available: bool = True  # Indique si le preset est disponible pour cette cible
    