# domain/value_objects/task_types.py
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def get_default(cls) -> "TaskStatus":
        """État par défaut d'une nouvelle tâche"""
        return cls.PENDING

    def is_terminal(self) -> bool:
        """Vérifie si l'état est terminal"""
        return self in {self.COMPLETED, self.FAILED, self.CANCELLED}

class TaskType(str, Enum):
    DOWNLOAD = "download"
    PROCESSING = "processing"
    STACKING = "stacking"
    CALIBRATION = "calibration"

    def get_queue_name(self) -> str:
        """Retourne le nom de la queue Celery associée"""
        return f"{self.value}_queue"
