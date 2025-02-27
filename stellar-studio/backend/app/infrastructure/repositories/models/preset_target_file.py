from sqlalchemy import (
    Column, Integer, ForeignKey, CheckConstraint, event, 
    UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
from datetime import datetime, timezone

class PresetTargetFile(Base):
    """Modèle SQLAlchemy pour la table d'association entre Presets et TargetFiles.
    
    Cette table d'association gère l'ordre de traitement des fichiers cibles
    dans un preset donné, permettant une séquence de traitement ordonnée
    et personnalisée.
    """

    __tablename__ = "preset_target_files"

    __table_args__ = (
        UniqueConstraint(
            'preset_id', 'target_file_id',
            name='uq_preset_target_file'
        ),
        UniqueConstraint(
            'preset_id', 'file_order',
            name='uq_preset_order'
        ),
        CheckConstraint(
            'file_order >= 0',
            name='check_order_positive'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Clés composées
    preset_id = Column(
        CHAR(36), 
        ForeignKey("presets.id", ondelete="CASCADE"), 
        primary_key=True,
        comment="ID du preset"
    )
    
    target_file_id = Column(
        CHAR(36), 
        ForeignKey("target_files.id", ondelete="CASCADE"), 
        primary_key=True,
        comment="ID du fichier cible"
    )
    
    # Colonne d'ordre
    file_order = Column(
        Integer, 
        nullable=False, 
        default=0,
        index=True,
        comment="Ordre de traitement du fichier dans le preset"
    )

    # Relations
    preset = relationship(
        "Preset", 
        back_populates="preset_files",
        lazy="joined"
    )
    
    target_file = relationship(
        "TargetFile", 
        back_populates="preset_files",
        lazy="joined"
    )

    # Validateurs
    @validates('file_order')
    def validate_order(self, key, file_order):
        """Valide l'ordre de traitement."""
        if not isinstance(file_order, int):
            raise ValueError("L'ordre doit être un entier")
        if file_order < 0:
            raise ValueError("L'ordre doit être positif ou nul")
        return file_order

    def __repr__(self):
        return (
            f"<PresetTargetFile("
            f"preset_id='{self.preset_id}', "
            f"target_file_id='{self.target_file_id}', "
            f"file_order={self.file_order})>"
        )

    # Méthodes utilitaires
    def move_up(self):
        """Déplace le fichier d'une position vers le haut dans l'ordre."""
        if self.file_order > 0:
            self.file_order -= 1
            self.updated_at = datetime.now(timezone.utc)

    def move_down(self):
        """Déplace le fichier d'une position vers le bas dans l'ordre."""
        self.file_order += 1
        self.updated_at = datetime.now(timezone.utc)

    def set_order(self, new_order: int):
        """Définit directement l'ordre du fichier."""
        if new_order < 0:
            raise ValueError("L'ordre ne peut pas être négatif")
        self.file_order = new_order
        self.updated_at = datetime.now(timezone.utc)

# Event Listeners
@event.listens_for(PresetTargetFile, 'before_insert')
def set_default_order(mapper, connection, target):
    """Définit l'ordre par défaut si non spécifié."""
    if target.file_order is None:
        # Trouve le dernier ordre utilisé pour ce preset
        stmt = (
            f"SELECT COALESCE(MAX(`file_order`), -1) FROM {target.__tablename__} "
            f"WHERE preset_id = '{target.preset_id}'"
        )
        result = connection.execute(stmt).scalar()
        target.file_order = (result or -1) + 1

@event.listens_for(PresetTargetFile, 'after_delete')
def reorder_after_delete(mapper, connection, target):
    """Réorganise les ordres après une suppression."""
    stmt = (
        f"UPDATE {target.__tablename__} "
        f"SET `file_order` = `file_order` - 1 "
        f"WHERE preset_id = '{target.preset_id}' "
        f"AND `file_order` > {target.file_order}"
    )
    connection.execute(stmt)

@event.listens_for(PresetTargetFile, 'before_update')
def validate_order_change(mapper, connection, target):
    """Vérifie que le changement d'ordre est valide."""
    if hasattr(target, '_sa_instance_state'):
        if 'file_order' in target._sa_instance_state.committed_state:
            old_order = target._sa_instance_state.committed_state['file_order']
            new_order = target.file_order
            
            # Vérifie que le nouvel ordre n'est pas déjà utilisé
            if old_order != new_order:
                stmt = (
                    f"SELECT COUNT(*) FROM {target.__tablename__} "
                    f"WHERE preset_id = '{target.preset_id}' "
                    f"AND `file_order` = {new_order}"
                )
                result = connection.execute(stmt).scalar()
                if result > 0:
                    raise ValueError(f"L'ordre {new_order} est déjà utilisé dans ce preset")

class PresetTargetFileError(Exception):
    """Exception personnalisée pour les erreurs liées aux associations Preset-TargetFile."""
    pass

# Méthodes de classe
@classmethod
def get_ordered_files(cls, session, preset_id):
    """Retourne tous les fichiers d'un preset dans l'ordre."""
    return (
        session.query(cls)
        .filter(cls.preset_id == preset_id)
        .order_by(cls.file_order)
        .all()
    )
