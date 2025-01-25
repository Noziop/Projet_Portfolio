# app/domain/models/task.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    DOWNLOAD = "download"
    PROCESSING = "processing"
    STACKING = "stacking"
    CALIBRATION = "calibration"

@dataclass
class Task:
    id: str
    user_id: str
    type: TaskType
    status: TaskStatus
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
