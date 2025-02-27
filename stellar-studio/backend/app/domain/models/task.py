# app/domain/models/task.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from app.domain.value_objects.task_types import TaskType, TaskStatus

@dataclass
class Task:
    id: UUID
    type: TaskType
    status: TaskStatus
    params: Dict
    user_id: Optional[UUID] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: Optional[float] = None  # Progression 0-100
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
