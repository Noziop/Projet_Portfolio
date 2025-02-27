from sqlalchemy import Column, String, JSON, ForeignKey, Enum, event, CheckConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
from app.domain.value_objects.processing_types import ProcessingStepType, ProcessingStatus
import json
from datetime import datetime, timezone

class ProcessingJob(Base):
    """Modèle SQLAlchemy pour les jobs de traitement d'images.
    
    Ce modèle représente une tâche de traitement d'image astronomique,
    incluant toutes les étapes du processus et leur état d'avancement.
    """

    __tablename__ = "processing_jobs"

    __table_args__ = (
        CheckConstraint(
            "JSON_VALID(steps)", 
            name='check_valid_steps_json'
        ),
        CheckConstraint(
            "JSON_VALID(intermediate_results)", 
            name='check_valid_results_json'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Relations principales
    user_id = Column(
        CHAR(36), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID de l'utilisateur ayant initié le traitement"
    )
    
    telescope_id = Column(
        CHAR(36), 
        ForeignKey("spacetelescopes.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID du télescope source"
    )
    
    workflow_id = Column(
        CHAR(36), 
        ForeignKey("workflows.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID du workflow de traitement"
    )
    
    target_id = Column(
        CHAR(36), 
        ForeignKey("targets.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID de la cible traitée"
    )
    
    preset_id = Column(
        CHAR(36), 
        ForeignKey("presets.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID du preset de traitement"
    )
    
    task_id = Column(
        CHAR(36), 
        ForeignKey("tasks.id", ondelete="CASCADE"), 
        nullable=False,
        unique=True,
        comment="ID de la tâche associée"
    )

    # Colonnes - État du traitement
    steps = Column(
        JSON, 
        nullable=False, 
        default=[],
        comment="Liste des étapes de traitement au format JSON"
    )
    
    status = Column(
        Enum(ProcessingStatus), 
        nullable=False, 
        default=ProcessingStatus.PENDING,
        index=True,
        comment="État actuel du traitement"
    )
    
    current_step = Column(
        Enum(ProcessingStepType),
        nullable=True,
        index=True,
        comment="Étape en cours de traitement"
    )
    
    error_message = Column(
        String(500),
        comment="Message d'erreur en cas d'échec"
    )
    
    intermediate_results = Column(
        JSON, 
        nullable=False, 
        default={},
        comment="Résultats intermédiaires au format JSON"
    )

    # Relations
    user = relationship(
        "User", 
        back_populates="processing_jobs",
        lazy="joined"
    )
    
    telescope = relationship(
        "SpaceTelescope", 
        back_populates="processing_jobs",
        lazy="joined"
    )
    
    workflow = relationship(
        "Workflow", 
        back_populates="processing_jobs",
        lazy="joined"
    )
    
    target = relationship(
        "Target", 
        back_populates="processing_jobs",
        lazy="joined"
    )
    
    preset = relationship(
        "Preset", 
        back_populates="processing_jobs",
        lazy="joined"
    )
    
    task = relationship(
        "Task", 
        back_populates="processing_job",
        lazy="joined",
        uselist=False
    )

    # Validateurs
    @validates('steps')
    def validate_steps(self, key, steps):
        """Valide la structure des étapes de traitement."""
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except json.JSONDecodeError:
                raise ValueError("Les étapes doivent être un JSON valide")
        
        if not isinstance(steps, list):
            raise ValueError("Les étapes doivent être une liste")
        
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError("Chaque étape doit être un dictionnaire")
            if 'type' not in step or 'params' not in step:
                raise ValueError("Chaque étape doit avoir un type et des paramètres")
            
        return steps

    @validates('intermediate_results')
    def validate_intermediate_results(self, key, results):
        """Valide la structure des résultats intermédiaires."""
        if isinstance(results, str):
            try:
                results = json.loads(results)
            except json.JSONDecodeError:
                raise ValueError("Les résultats doivent être un JSON valide")
        
        if not isinstance(results, dict):
            raise ValueError("Les résultats doivent être un dictionnaire")
            
        return results

    @validates('error_message')
    def validate_error_message(self, key, message):
        """Valide le message d'erreur."""
        if message and len(message) > 500:
            message = message[:497] + "..."
        return message

    def __repr__(self):
        return (
            f"<ProcessingJob("
            f"id='{self.id}', "
            f"status={self.status.name}, "
            f"current_step={self.current_step.name if self.current_step else 'None'})>"
        )

    # Méthodes utilitaires
    def update_status(self, new_status: ProcessingStatus, error_message: str = None):
        """Met à jour le statut du job et enregistre l'erreur si présente."""
        self.status = new_status
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.now(timezone.utc)

    def advance_step(self, next_step: ProcessingStepType):
        """Avance à l'étape suivante du traitement."""
        self.current_step = next_step
        self.updated_at = datetime.now(timezone.utc)

    def add_intermediate_result(self, step: ProcessingStepType, result: dict):
        """Ajoute un résultat intermédiaire pour une étape."""
        if not isinstance(result, dict):
            raise ValueError("Le résultat doit être un dictionnaire")
        
        self.intermediate_results = {
            **self.intermediate_results,
            step.name: result
        }
        self.updated_at = datetime.now(timezone.utc)

# Event Listeners
@event.listens_for(ProcessingJob, 'before_insert')
def set_initial_status(mapper, connection, target):
    """Initialise le statut et vérifie la cohérence des données."""
    if target.status is None:
        target.status = ProcessingStatus.PENDING
    
    if not target.steps:
        raise ValueError("Un job de traitement doit avoir au moins une étape")

@event.listens_for(ProcessingJob, 'before_update')
def validate_status_transition(mapper, connection, target):
    """Vérifie que la transition de statut est valide."""
    if hasattr(target, '_sa_instance_state'):
        # Vérifie si le statut a été modifié
        if 'status' in target._sa_instance_state.committed_state:
            old_status = target._sa_instance_state.committed_state['status']
            new_status = target.status
            
            # Définir les transitions valides
            valid_transitions = {
                ProcessingStatus.PENDING: {ProcessingStatus.RUNNING, ProcessingStatus.FAILED},
                ProcessingStatus.RUNNING: {ProcessingStatus.COMPLETED, ProcessingStatus.FAILED},
                ProcessingStatus.FAILED: {ProcessingStatus.PENDING},
                ProcessingStatus.COMPLETED: set()  # Aucune transition depuis COMPLETED
            }
            
            if new_status not in valid_transitions[old_status]:
                raise ValueError(
                    f"Transition de statut invalide: {old_status.name} -> {new_status.name}"
                )

class ProcessingJobError(Exception):
    """Exception personnalisée pour les erreurs liées aux jobs de traitement."""
    pass
