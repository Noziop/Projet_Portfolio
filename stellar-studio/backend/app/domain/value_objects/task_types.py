#app/domain/value_objects/task_types.py
from enum import Enum

class TaskType(str, Enum):
    DOWNLOAD = "DOWNLOAD"
    PROCESSING = "PROCESSING"
    STACKING = "STACKING"
    CALIBRATION = "CALIBRATION"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
