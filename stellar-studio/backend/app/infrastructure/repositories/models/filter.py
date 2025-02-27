from sqlalchemy import Column, String, Integer, ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
from app.domain.value_objects.filter_types import FilterType

class Filter(Base):
    """Modèle SQLAlchemy pour les filtres des télescopes.
    
    Ce modèle représente les filtres optiques utilisés par les télescopes spatiaux
    pour l'acquisition d'images dans différentes longueurs d'onde.
    """
    
    __tablename__ = "filters"
    
    __table_args__ = (
        CheckConstraint('wavelength > 0', name='check_positive_wavelength'),
        CheckConstraint('length(name) >= 2', name='check_name_length'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes
    name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Nom unique du filtre"
    )
    
    telescope_id = Column(
        CHAR(36), 
        ForeignKey(
            "spacetelescopes.id", 
            ondelete="CASCADE"
        ), 
        nullable=False,
        index=True
    )
    
    wavelength = Column(
        Integer, 
        nullable=False,
        comment="Longueur d'onde en nanomètres"
    )
    
    description = Column(
        String(500),
        comment="Description détaillée du filtre et de son utilisation"
    )
    
    filter_type = Column(
        Enum(FilterType), 
        nullable=False,
        index=True,
        comment="Type de filtre (BROADBAND, NARROWBAND, etc.)"
    )

    # Relations
    telescope = relationship(
        "SpaceTelescope", 
        back_populates="filters",
        lazy="joined"
    )
    
    target_files = relationship(
        "TargetFile", 
        back_populates="filter",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    preset_filters = relationship(
        "PresetFilter", 
        back_populates="filter",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Validateurs
    @validates('name')
    def validate_name(self, key, name):
        if not name or len(name.strip()) < 2:
            raise ValueError("Le nom du filtre doit contenir au moins 2 caractères")
        return name.strip()

    @validates('wavelength')
    def validate_wavelength(self, key, wavelength):
        if not isinstance(wavelength, int) or wavelength <= 0:
            raise ValueError("La longueur d'onde doit être un entier positif")
        return wavelength

    @validates('description')
    def validate_description(self, key, description):
        if description and len(description) > 500:
            raise ValueError("La description ne peut pas dépasser 500 caractères")
        return description

    def __repr__(self):
        return f"<Filter(name='{self.name}', wavelength={self.wavelength}nm, type={self.filter_type})>"
