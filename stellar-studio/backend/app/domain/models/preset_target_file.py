# app/domain/models/preset_target_file.py
from dataclasses import dataclass
from uuid import UUID

@dataclass
class PresetTargetFile:
    preset_id: UUID
    target_file_id: UUID
    file_order: int  # Pour l'ordre de traitement
