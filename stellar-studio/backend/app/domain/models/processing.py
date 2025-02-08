from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..value_objects.processing_types import ProcessingStatus

@dataclass
class ProcessingJob:
    id: str
    user_id: str
    telescope_id: str
    workflow_id: str
    status: ProcessingStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None