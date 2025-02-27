# app/domain/models/processing.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from app.domain.value_objects.processing_types import ProcessingStepType, ProcessingStatus

@dataclass
class ProcessingJob:
    id: UUID
    user_id: UUID
    telescope_id: UUID
    workflow_id: UUID
    target_id: UUID
    preset_id: UUID
    task_id: UUID
    steps: List[ProcessingStepType]
    status: ProcessingStatus
    current_step: Optional[ProcessingStepType] = None
    error_message: Optional[str] = None
    intermediate_results: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
