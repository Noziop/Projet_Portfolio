# app/domain/models/processing.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

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
