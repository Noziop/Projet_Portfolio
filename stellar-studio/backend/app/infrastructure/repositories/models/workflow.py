from sqlalchemy import (
    Column, String, JSON, Boolean, Integer, CheckConstraint, 
    event, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from app.db.base_class import Base
import json

class Workflow(Base):
    """Modèle SQLAlchemy pour les workflows de traitement d'images.
    
    Ce modèle définit les séquences de traitement d'images astronomiques,
    incluant les étapes, les filtres requis et les statistiques d'utilisation.
    """

    __tablename__ = "workflows"

    __table_args__ = (
        UniqueConstraint('name', name='uq_workflow_name'),
        CheckConstraint(
            'length(name) >= 3',
            name='check_name_length'
        ),
        CheckConstraint(
            "JSON_VALID(steps)", 
            name='check_valid_steps_json'
        ),
        CheckConstraint(
            "JSON_VALID(required_filters)", 
            name='check_valid_filters_json'
        ),
        CheckConstraint(
            'estimated_duration >= 0',
            name='check_positive_duration'
        ),
        CheckConstraint(
            'execution_count >= 0',
            name='check_positive_count'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Identification
    name = Column(
        String(255), 
        nullable=False, 
        unique=True, 
        index=True,
        comment="Nom unique du workflow"
    )
    
    description = Column(
        String(1000),
        comment="Description détaillée du workflow"
    )

    # Colonnes - Configuration
    steps = Column(
        JSON, 
        nullable=False, 
        default=[],
        comment="Étapes de traitement au format JSON"
    )
    
    required_filters = Column(
        JSON, 
        nullable=False, 
        default=[],
        comment="Liste des filtres requis"
    )
    
    target_type = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Type de cible compatible"
    )

    # Colonnes - État et Statistiques
    is_default = Column(
        Boolean, 
        nullable=False, 
        default=False, 
        index=True,
        comment="Indique si c'est le workflow par défaut"
    )
    
    estimated_duration = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Durée estimée en secondes"
    )
    
    execution_count = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Nombre d'exécutions du workflow"
    )

    # Relations
    processing_jobs = relationship(
        "ProcessingJob", 
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Validateurs
    @validates('name')
    def validate_name(self, key, name):
        """Valide le nom du workflow."""
        if not name or len(name.strip()) < 3:
            raise ValueError("Le nom doit contenir au moins 3 caractères")
        return name.strip()

    @validates('description')
    def validate_description(self, key, description):
        """Valide la description du workflow."""
        if description and len(description) > 1000:
            raise ValueError("La description ne peut pas dépasser 1000 caractères")
        return description

    @validates('steps')
    def validate_steps(self, key, steps):
        """Valide les étapes du workflow."""
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except json.JSONDecodeError:
                raise ValueError("Les étapes doivent être un JSON valide")
        
        if not isinstance(steps, list):
            raise ValueError("Les étapes doivent être une liste")
            
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError("Chaque étape doit être un objet")
            required_fields = {'name', 'type', 'params'}
            if not all(field in step for field in required_fields):
                raise ValueError(f"Chaque étape doit avoir: {required_fields}")
                
        return steps

    @validates('required_filters')
    def validate_required_filters(self, key, filters):
        """Valide la liste des filtres requis."""
        if isinstance(filters, str):
            try:
                filters = json.loads(filters)
            except json.JSONDecodeError:
                raise ValueError("La liste des filtres doit être un JSON valide")
        
        if not isinstance(filters, list):
            raise ValueError("Les filtres doivent être une liste")
            
        return filters

    @validates('target_type')
    def validate_target_type(self, key, target_type):
        """Valide le type de cible."""
        valid_types = {'GALAXY', 'NEBULA', 'STAR', 'CLUSTER', 'PLANET'}
        if target_type not in valid_types:
            raise ValueError(f"Type de cible invalide. Valeurs possibles: {valid_types}")
        return target_type

    @validates('estimated_duration')
    def validate_duration(self, key, duration):
        """Valide la durée estimée."""
        if not isinstance(duration, int) or duration < 0:
            raise ValueError("La durée estimée doit être un entier positif")
        return duration

    def __repr__(self):
        return (
            f"<Workflow("
            f"name='{self.name}', "
            f"target_type='{self.target_type}', "
            f"steps_count={len(self.steps)})>"
        )

    # Méthodes utilitaires
    def increment_execution_count(self):
        """Incrémente le compteur d'exécutions."""
        self.execution_count += 1

    def update_estimated_duration(self, new_duration: int):
        """Met à jour la durée estimée."""
        if new_duration < 0:
            raise ValueError("La durée ne peut pas être négative")
        self.estimated_duration = new_duration

    def add_step(self, name: str, step_type: str, params: dict = None):
        """Ajoute une nouvelle étape au workflow."""
        step = {
            'name': name,
            'type': step_type,
            'params': params or {}
        }
        self.steps = [*self.steps, step]

    def add_required_filter(self, filter_id: str):
        """Ajoute un filtre requis."""
        if filter_id not in self.required_filters:
            self.required_filters = [*self.required_filters, filter_id]

    @property
    def steps_count(self):
        """Retourne le nombre d'étapes."""
        return len(self.steps)

# Event Listeners
@event.listens_for(Workflow, 'before_insert')
def validate_default_workflow(mapper, connection, target):
    """Vérifie qu'il n'y a qu'un seul workflow par défaut par type de cible."""
    if target.is_default:
        stmt = f"SELECT COUNT(*) FROM workflows WHERE is_default = 1 AND target_type = '{target.target_type}'"
        result = connection.execute(stmt).scalar()
        if result > 0:
            raise ValueError(
                f"Il existe déjà un workflow par défaut pour le type {target.target_type}"
            )

class WorkflowError(Exception):
    """Exception personnalisée pour les erreurs liées aux workflows."""
    pass
