# domain/models/preset.py
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class Preset:
    id: str
    name: str
    description: Optional[str]
    processing_params: Dict[str, Any]
    telescope_id: str
    filters: List[str]  # Liste des IDs des filtres