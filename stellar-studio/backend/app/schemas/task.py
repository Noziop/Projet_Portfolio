# app/schemas/task.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, validator, UUID4
from app.domain.value_objects.task_types import TaskType, TaskStatus

class TaskParams(BaseModel):
    """Structure des paramètres de tâche"""
    workflow_id: Optional[UUID] = None
    target_id: Optional[UUID] = None
    preset_id: Optional[UUID] = None
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class TaskResult(BaseModel):
    """Structure des résultats de tâche"""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    messages: List[str] = Field(default_factory=list)
    preview_url: Optional[str] = None

class TaskBase(BaseModel):
    """Attributs communs pour tous les schemas Task"""
    type: TaskType = Field(..., description="Type de tâche")
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Statut de la tâche"
    )
    params: TaskParams = Field(
        ...,
        description="Paramètres de la tâche"
    )
    progress: Optional[float] = Field(
        None,
        description="Progression de la tâche (0-100)",
        ge=0,
        le=100
    )

class TaskCreate(TaskBase):
    """Schema pour la création d'une tâche"""
    user_id: Optional[UUID] = Field(None, description="ID de l'utilisateur")

class TaskUpdate(BaseModel):
    """Schema pour la mise à jour d'une tâche"""
    status: Optional[TaskStatus] = None
    result: Optional[TaskResult] = None
    error: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    completed_at: Optional[datetime] = None

    @validator('error')
    def validate_error(cls, v, values):
        if v and values.get('status') != TaskStatus.FAILED:
            raise ValueError("Un message d'erreur ne peut être défini que pour une tâche en échec")
        return v

class TaskInDB(TaskBase):
    """Schema pour une tâche en DB"""
    id: UUID
    user_id: Optional[UUID]
    result: Optional[TaskResult] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskResponse(TaskInDB):
    """Schema pour la réponse API"""
    user_name: Optional[str] = Field(None, description="Nom de l'utilisateur")
    duration: Optional[float] = Field(
        None,
        description="Durée d'exécution en secondes"
    )

    class Config:
        from_attributes = True

class TaskProgress(BaseModel):
    """Schema pour les mises à jour de progression"""
    task_id: UUID
    status: TaskStatus
    progress: float = Field(..., ge=0, le=100)
    message: Optional[str] = None
    preview_url: Optional[str] = None

class TaskListResponse(BaseModel):
    """Schema pour la liste paginée des tâches"""
    items: List[TaskResponse]
    total: int
    page: int
    size: int

class DownloadTaskCreate(BaseModel):
    """Schéma pour la création d'une tâche de téléchargement"""
    target_id: UUID4
    preset_id: UUID4

class DownloadTaskResponse(BaseModel):
    """Schéma pour la réponse d'une tâche de téléchargement"""
    task_id: UUID4
    status: str
    message: str = "Téléchargement initié"
