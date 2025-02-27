from sqlalchemy import Column, ForeignKey, Integer, CheckConstraint, UniqueConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base

class PresetFilter(Base):
    """Modèle SQLAlchemy pour la table d'association entre Presets et Filters.
    
    Cette table d'association permet de définir l'ordre d'application des filtres
    dans un preset de traitement d'images. Elle maintient également l'intégrité
    référentielle entre les presets et les filtres.
    """

    __tablename__ = "preset_filters"

    __table_args__ = (
        UniqueConstraint(
            'preset_id', 'filter_id',
            name='uq_preset_filter'
        ),
        UniqueConstraint(
            'preset_id', 'filter_order',
            name='uq_preset_order'
        ),
        CheckConstraint(
            'filter_order >= 0',
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
    
    filter_id = Column(
        CHAR(36), 
        ForeignKey("filters.id", ondelete="CASCADE"), 
        primary_key=True,
        comment="ID du filtre"
    )
    
    # Colonne d'ordre
    filter_order = Column(
        Integer, 
        nullable=False, 
        default=0,
        index=True,
        comment="Ordre d'application du filtre dans le preset (0-based)"
    )

    # Relations
    preset = relationship(
        "Preset", 
        back_populates="preset_filters",
        lazy="joined"
    )
    
    filter = relationship(
        "Filter", 
        back_populates="preset_filters",
        lazy="joined"
    )

    # Validateurs
    @validates('filter_order')
    def validate_order(self, key, filter_order):
        """Valide que l'ordre est un entier positif."""
        if not isinstance(filter_order, int) or filter_order < 0:
            raise ValueError("L'ordre doit être un entier positif ou nul")
        return filter_order

    def __repr__(self):
        return (
            f"<PresetFilter("
            f"preset_id='{self.preset_id}', "
            f"filter_id='{self.filter_id}', "
            f"filter_order={self.filter_order})>"
        )

# Event Listeners
@event.listens_for(PresetFilter, 'before_insert')
def set_default_order(mapper, connection, target):
    """Définit l'ordre par défaut si non spécifié."""
    if target.filter_order is None:
        # Trouve le dernier ordre utilisé pour ce preset
        from sqlalchemy import select, func
        stmt = select(func.max(PresetFilter.filter_order)).where(
            PresetFilter.preset_id == target.preset_id
        )
        result = connection.execute(stmt).scalar()
        target.filter_order = (result or -1) + 1

@event.listens_for(PresetFilter, 'after_delete')
def reorder_after_delete(mapper, connection, target):
    """Réorganise les ordres après une suppression."""
    from sqlalchemy import select
    stmt = select(PresetFilter).where(
        PresetFilter.preset_id == target.preset_id,
        PresetFilter.filter_order > target.filter_order
    ).order_by(PresetFilter.filter_order)
    
    for idx, preset_filter in enumerate(connection.execute(stmt)):
        connection.execute(
            PresetFilter.__table__.update().where(
                PresetFilter.preset_id == preset_filter.preset_id,
                PresetFilter.filter_id == preset_filter.filter_id
            ).values(filter_order=target.filter_order + idx)
        )

class PresetFilterError(Exception):
    """Exception personnalisée pour les erreurs liées aux PresetFilters."""
    pass
