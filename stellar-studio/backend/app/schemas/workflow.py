# app/schemas/workflow.py
from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from app.domain.value_objects.processing_types import ProcessingStepType

class WorkflowStep(BaseModel):
    """Structure d'une étape de workflow"""
    name: str = Field(..., description="Nom de l'étape")
    order: int = Field(..., description="Ordre d'exécution")
    type: ProcessingStepType = Field(..., description="Type de traitement")
    params: Dict = Field(default_factory=dict, description="Paramètres de l'étape")
    estimated_duration: Optional[int] = Field(
        None,
        description="Durée estimée de l'étape en secondes"
    )

class FilterRequirement(BaseModel):
    """Exigences pour les filtres"""
    filter_type: str = Field(..., description="Type de filtre requis")
    min_count: int = Field(1, description="Nombre minimum d'images")
    wavelength_range: Optional[List[int]] = Field(
        None,
        description="Plage de longueur d'onde acceptée"
    )

class WorkflowBase(BaseModel):
    """Attributs communs pour tous les schemas Workflow"""
    name: str = Field(
        ..., 
        description="Nom du workflow",
        min_length=3,
        max_length=255
    )
    description: Optional[str] = Field(None, description="Description du workflow")
    steps: List[WorkflowStep] = Field(..., description="Étapes du workflow")
    is_default: bool = Field(
        default=False,
        description="Workflow par défaut pour ce type de cible"
    )
    target_type: str = Field(
        ..., 
        description="Type de cible compatible",
        max_length=100
    )
    required_filters: Dict[str, FilterRequirement] = Field(
        default_factory=dict,
        description="Filtres requis pour ce workflow"
    )
    estimated_duration: Optional[int] = Field(
        None,
        description="Durée estimée totale en secondes",
        ge=0
    )
    execution_count: int = Field(
        default=0,
        description="Nombre total d'exécutions",
        ge=0
    )

class WorkflowCreate(WorkflowBase):
    """Schema pour la création d'un workflow"""
    @validator('steps')
    def validate_steps(cls, v):
        if not v:
            raise ValueError("Le workflow doit contenir au moins une étape")
        orders = [step.order for step in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Les ordres des étapes doivent être uniques")
        return v

    @validator('estimated_duration', always=True)
    def calculate_estimated_duration(cls, v, values):
        if v is None and 'steps' in values:
            return sum(step.estimated_duration or 0 for step in values['steps'])
        return v

class WorkflowUpdate(BaseModel):
    """Schema pour la mise à jour d'un workflow"""
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    is_default: Optional[bool] = None
    required_filters: Optional[Dict[str, FilterRequirement]] = None
    estimated_duration: Optional[int] = None

    @validator('steps')
    def validate_steps(cls, v):
        if v is not None:
            if not v:
                raise ValueError("Le workflow doit contenir au moins une étape")
            orders = [step.order for step in v]
            if len(orders) != len(set(orders)):
                raise ValueError("Les ordres des étapes doivent être uniques")
        return v

class WorkflowInDB(WorkflowBase):
    """Schema pour un workflow en DB"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WorkflowStats(BaseModel):
    """Statistiques du workflow"""
    total_executions: int = Field(..., description="Nombre total d'exécutions")
    success_rate: float = Field(..., description="Taux de réussite")
    average_duration: float = Field(..., description="Durée moyenne d'exécution (s)")
    last_execution: Optional[datetime] = Field(None, description="Dernière exécution")
    actual_vs_estimated: float = Field(
        ..., 
        description="Ratio durée réelle/estimée"
    )

class WorkflowResponse(WorkflowInDB):
    """Schema pour la réponse API"""
    stats: Optional[WorkflowStats] = Field(
        None,
        description="Statistiques d'exécution"
    )
    is_compatible: Optional[bool] = Field(
        None,
        description="Compatible avec la cible courante"
    )

    class Config:
        from_attributes = True

class WorkflowListResponse(BaseModel):
    """Schema pour la liste paginée des workflows"""
    items: List[WorkflowResponse]
    total: int
    page: int
    size: int
