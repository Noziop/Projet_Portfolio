# app/schemas/processing.py
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from app.domain.value_objects.processing_types import ProcessingStepType, ProcessingStatus

class ProcessingJobBase(BaseModel):
    """Attributs communs pour tous les schemas ProcessingJob"""
    steps: List[ProcessingStepType] = Field(
        ..., 
        description="Étapes de traitement à effectuer"
    )
    status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Statut global du job de traitement"
    )
    current_step: Optional[ProcessingStepType] = Field(
        None, 
        description="Étape de traitement en cours"
    )
    error_message: Optional[str] = Field(
        None, 
        description="Message d'erreur éventuel"
    )
    intermediate_results: Optional[Dict] = Field(
        None,
        description="Résultats intermédiaires du traitement"
    )

class ProcessingJobCreate(BaseModel):
    """Schema pour la création d'un job de traitement"""
    target_id: UUID = Field(..., description="ID de la cible à traiter")
    preset_id: UUID = Field(..., description="ID du preset à utiliser")
    workflow_id: UUID = Field(..., description="ID du workflow à suivre")

class ProcessingJobUpdate(BaseModel):
    """Schema pour la mise à jour d'un job de traitement"""
    status: Optional[ProcessingStatus] = None
    current_step: Optional[ProcessingStepType] = None
    error_message: Optional[str] = None
    intermediate_results: Optional[Dict] = None

class ProcessingJobInDB(ProcessingJobBase):
    """Schema pour un job de traitement en DB"""
    id: UUID
    user_id: UUID
    telescope_id: UUID
    workflow_id: UUID
    target_id: UUID
    preset_id: UUID
    task_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProcessingStepProgress(BaseModel):
    """Progression d'une étape de traitement"""
    step: ProcessingStepType
    progress: float = Field(..., ge=0, le=100)
    status: str
    details: Optional[Dict] = None

class ProcessingJobResponse(ProcessingJobInDB):
    """Schema pour la réponse API"""
    target_name: Optional[str] = Field(None, description="Nom de la cible")
    preset_name: Optional[str] = Field(None, description="Nom du preset")
    telescope_name: Optional[str] = Field(None, description="Nom du télescope")
    user_name: Optional[str] = Field(None, description="Nom de l'utilisateur")
    workflow_name: Optional[str] = Field(None, description="Nom du workflow")
    progress: List[ProcessingStepProgress] = Field(
        default_factory=list,
        description="Progression détaillée par étape"
    )
    preview_url: Optional[str] = Field(
        None,
        description="URL de la preview du traitement"
    )

    class Config:
        from_attributes = True

class ProcessingJobWebSocketUpdate(BaseModel):
    """Schema pour les mises à jour WebSocket"""
    job_id: UUID
    status: ProcessingStatus
    step: ProcessingStepType
    progress: float
    details: Optional[Dict] = None
    preview_url: Optional[str] = None
