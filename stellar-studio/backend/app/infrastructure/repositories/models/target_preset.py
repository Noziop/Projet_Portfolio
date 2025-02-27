from sqlalchemy import Column, ForeignKey, Boolean, CheckConstraint, event, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
from datetime import datetime, timezone

class TargetPreset(Base):
    """Modèle SQLAlchemy pour la table d'association entre Targets et Presets.
    
    Cette table d'association gère les relations entre les cibles astronomiques
    et leurs presets de traitement associés, en incluant un statut de disponibilité
    pour chaque association.
    """

    __tablename__ = "target_presets"

    __table_args__ = (
        UniqueConstraint(
            'target_id', 'preset_id',
            name='uq_target_preset'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Clés composées
    target_id = Column(
        CHAR(36), 
        ForeignKey("targets.id", ondelete="CASCADE"), 
        primary_key=True,
        index=True,
        comment="ID de la cible"
    )
    
    preset_id = Column(
        CHAR(36), 
        ForeignKey("presets.id", ondelete="CASCADE"), 
        primary_key=True,
        index=True,
        comment="ID du preset"
    )
    
    # Colonnes - État
    is_available = Column(
        Boolean, 
        nullable=False, 
        default=True, 
        index=True,
        comment="Indique si le preset est disponible pour cette cible"
    )

    # Relations
    target = relationship(
        "Target", 
        back_populates="target_presets",
        lazy="joined"
    )
    
    preset = relationship(
        "Preset", 
        back_populates="target_presets",
        lazy="joined"
    )

    # Validateurs
    @validates('is_available')
    def validate_availability(self, key, value):
        """Valide le statut de disponibilité."""
        if not isinstance(value, bool):
            raise ValueError("is_available doit être un booléen")
        return value

    def __repr__(self):
        return (
            f"<TargetPreset("
            f"target_id='{self.target_id}', "
            f"preset_id='{self.preset_id}', "
            f"available={self.is_available})>"
        )

    # Méthodes utilitaires
    def toggle_availability(self):
        """Inverse le statut de disponibilité."""
        self.is_available = not self.is_available
        self.updated_at = datetime.now(timezone.utc)
        return self.is_available

    @property
    def is_compatible(self):
        """Vérifie si le preset est compatible avec la cible."""
        # Vérifie que tous les filtres requis sont disponibles
        required_filters = {pf.filter_id for pf in self.preset.preset_filters}
        available_filters = {tf.filter_id for tf in self.target.files}
        return required_filters.issubset(available_filters)
    
    # Méthodes de classe
    @classmethod
    def get_available_presets(cls, session, target_id):
        """Retourne tous les presets disponibles pour une cible donnée."""
        return (
            session.query(cls)
            .filter(
                cls.target_id == target_id,
                cls.is_available == True
            )
            .all()
        )

    @classmethod
    def get_targets_for_preset(cls, session, preset_id):
        """Retourne toutes les cibles pour lesquelles un preset est disponible."""
        return (
            session.query(cls)
            .filter(
                cls.preset_id == preset_id,
                cls.is_available == True
            )
            .all()
        )

@event.listens_for(TargetPreset, 'before_insert')
def check_compatibility(mapper, connection, target):
    """Vérifie la compatibilité avant l'insertion."""
    # Vérifie que les relations sont chargées
    if hasattr(target, 'target') and target.target is not None and \
       hasattr(target, 'preset') and target.preset is not None:
        # Vérifie que le preset et la cible utilisent le même télescope
        if target.target.telescope_id != target.preset.telescope_id:
            raise ValueError(
                "Le preset et la cible doivent être associés au même télescope"
            )

@event.listens_for(TargetPreset, 'before_update')
def log_availability_change(mapper, connection, target):
    """Enregistre les changements de disponibilité."""
    if hasattr(target, '_sa_instance_state'):
        if 'is_available' in target._sa_instance_state.committed_state:
            old_value = target._sa_instance_state.committed_state['is_available']
            if old_value != target.is_available:
                # Ici, vous pourriez ajouter une logique de logging
                target.updated_at = datetime.now(timezone.utc)

class TargetPresetError(Exception):
    """Exception personnalisée pour les erreurs liées aux associations Target-Preset."""
    pass


