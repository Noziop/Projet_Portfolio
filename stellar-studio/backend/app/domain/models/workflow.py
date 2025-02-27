# app/domain/models/workflow.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID

@dataclass
class Workflow:
    id: UUID
    name: str
    description: str
    steps: List[str]
    is_default: bool = False
    target_type: str
    required_filters: Optional[Dict] = None
    estimated_duration: Optional[int] = None  # Durée estimée en secondes
    execution_count: int = 0  # Compteur d'exécutions
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
