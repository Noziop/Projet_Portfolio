from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from ..value_objects.processing_types import ProcessingStatus, ProcessingStepType

@dataclass
class ProcessingJob:
    id: str
    user_id: str
    telescope_id: str
    workflow_id: str
    task_id: str
    status: ProcessingStatus
    steps: List[ProcessingStepType]
    created_at: datetime
    current_step: Optional[ProcessingStepType] = None
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None