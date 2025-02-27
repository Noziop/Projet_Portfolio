# app/infratsructure/repositories/models/task.py
from sqlalchemy import (
    Column, String, DateTime, JSON, ForeignKey, Enum, Float, 
    CheckConstraint, event
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
from app.domain.value_objects.task_types import TaskType, TaskStatus
from datetime import datetime, timezone
import json

class Task(Base):
    """Modèle SQLAlchemy pour les tâches de traitement.
    
    Ce modèle représente une tâche unitaire de traitement, pouvant être
    associée à un job de traitement plus large. Il gère le cycle de vie
    complet d'une tâche, son état et ses résultats.
    """

    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint(
            'progress >= 0 AND progress <= 100',
            name='check_progress_range'
        ),
        CheckConstraint(
            "JSON_VALID(params)", 
            name='check_valid_params_json'
        ),
        CheckConstraint(
            "JSON_VALID(result) OR result IS NULL", 
            name='check_valid_result_json'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Type et État
    type = Column(
        Enum(TaskType), 
        nullable=False,
        index=True,
        comment="Type de tâche"
    )
    
    status = Column(
        Enum(TaskStatus), 
        nullable=False,
        index=True,
        default=TaskStatus.PENDING,
        comment="État actuel de la tâche"
    )

    # Colonnes - Paramètres et Résultats
    params = Column(
        JSON, 
        nullable=False, 
        default={},
        comment="Paramètres de la tâche au format JSON"
    )
    
    result = Column(
        JSON, 
        nullable=True,
        comment="Résultats de la tâche au format JSON"
    )
    
    error = Column(
        String(500),
        comment="Message d'erreur en cas d'échec"
    )
    
    progress = Column(
        Float, 
        nullable=False,
        default=0.0,
        index=True,
        comment="Progression de 0 à 100"
    )

    # Colonnes - Relations et Timing
    user_id = Column(
        CHAR(36), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID de l'utilisateur associé"
    )
    
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Date de fin d'exécution"
    )

    # Relations
    user = relationship(
        "User", 
        back_populates="tasks",
        lazy="joined"
    )
    
    processing_job = relationship(
        "ProcessingJob", 
        back_populates="task", 
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Validateurs
    @validates('progress')
    def validate_progress(self, key, progress):
        """Valide la progression."""
        if not isinstance(progress, (int, float)):
            raise ValueError("La progression doit être un nombre")
        if not 0 <= progress <= 100:
            raise ValueError("La progression doit être entre 0 et 100")
        return float(progress)

    @validates('params')
    def validate_params(self, key, params):
        """Valide les paramètres de la tâche."""
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                raise ValueError("Les paramètres doivent être un JSON valide")
        
        if not isinstance(params, dict):
            raise ValueError("Les paramètres doivent être un dictionnaire")
            
        return params

    @validates('result')
    def validate_result(self, key, result):
        """Valide le résultat de la tâche."""
        if result is not None:
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    raise ValueError("Le résultat doit être un JSON valide")
            
            if not isinstance(result, dict):
                raise ValueError("Le résultat doit être un dictionnaire")
                
        return result

    @validates('error')
    def validate_error(self, key, error):
        """Valide le message d'erreur."""
        if error and len(error) > 500:
            error = error[:497] + "..."
        return error

    def __repr__(self):
        return (
            f"<Task("
            f"type={self.type.name}, "
            f"status={self.status.name}, "
            f"progress={self.progress}%)>"
        )

    # Méthodes utilitaires
    def update_progress(self, progress: float):
        """Met à jour la progression de la tâche."""
        self.progress = progress
        self.updated_at = datetime.now(timezone.utc)

    def complete(self, result: dict = None):
        """Marque la tâche comme terminée."""
        self.status = TaskStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.now(timezone.utc)
        if result:
            self.result = result

    def fail(self, error_message: str):
        """Marque la tâche comme échouée."""
        self.status = TaskStatus.FAILED
        self.error = error_message
        self.completed_at = datetime.now(timezone.utc)

    @property
    def duration(self):
        """Retourne la durée d'exécution de la tâche."""
        if not self.completed_at:
            return None
        return (self.completed_at - self.created_at).total_seconds()

# Event Listeners
@event.listens_for(Task, 'before_insert')
def set_initial_state(mapper, connection, target):
    """Initialise l'état de la tâche."""
    if target.status is None:
        target.status = TaskStatus.PENDING
    if target.progress is None:
        target.progress = 0.0

@event.listens_for(Task, 'before_update')
def validate_status_transition(mapper, connection, target):
    """Vérifie les transitions d'état valides."""
    if hasattr(target, '_sa_instance_state'):
        if 'status' in target._sa_instance_state.committed_state:
            old_status = target._sa_instance_state.committed_state['status']
            new_status = target.status
            
            # Définir les transitions valides
            valid_transitions = {
                TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.FAILED},
                TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED},
                TaskStatus.COMPLETED: set(),  # Pas de transition depuis COMPLETED
                TaskStatus.FAILED: {TaskStatus.PENDING}  # Permet de réessayer
            }
            
            if new_status not in valid_transitions[old_status]:
                raise ValueError(
                    f"Transition de statut invalide: {old_status.name} -> {new_status.name}"
                )

class TaskError(Exception):
    """Exception personnalisée pour les erreurs liées aux tâches."""
    pass
