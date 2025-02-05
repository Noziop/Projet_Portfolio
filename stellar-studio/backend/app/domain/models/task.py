# domain/models/task.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from ..value_objects.task_types import TaskStatus, TaskType

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
