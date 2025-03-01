from sqlalchemy import Column, String, JSON, ForeignKey, CheckConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
from app.domain.value_objects.target_types import ObjectType
import json

class Preset(Base):
    """Modèle SQLAlchemy pour les préréglages de traitement d'images.
    
    Ce modèle définit les configurations prédéfinies pour le traitement
    d'images astronomiques, incluant les paramètres de traitement et
    les associations avec les filtres.
    """

    __tablename__ = "presets"

    __table_args__ = (
        CheckConstraint('length(name) >= 3', name='check_name_length'),
        CheckConstraint(
            "JSON_VALID(processing_params)", 
            name='check_valid_json'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Identification
    name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Nom unique du preset"
    )
    
    description = Column(
        String(500),
        comment="Description détaillée du preset"
    )

    # Colonnes - Relations
    telescope_id = Column(
        CHAR(36), 
        ForeignKey("spacetelescopes.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID du télescope associé"
    )

    target_type = Column(
        String(100), 
        nullable=True,  # ou False selon tes besoins
        index=True,
        comment="Type d'objet cible (nebula, galaxy, etc.)"
    )

    # Colonnes - Configuration
    processing_params = Column(
        JSON, 
        nullable=False, 
        default={},
        comment="Paramètres de traitement au format JSON"
    )

    # Relations
    telescope = relationship(
        "SpaceTelescope", 
        back_populates="presets",
        lazy="joined"
    )
    
    processing_jobs = relationship(
        "ProcessingJob", 
        back_populates="preset",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    preset_filters = relationship(
        "PresetFilter", 
        back_populates="preset",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PresetFilter.filter_order"
    )
    
    target_presets = relationship(
        "TargetPreset", 
        back_populates="preset",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    preset_files = relationship(
        "PresetTargetFile", 
        back_populates="preset",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PresetTargetFile.file_order"
    )

    # Validateurs
    @validates('name')
    def validate_name(self, key, name):
        """Valide le nom du preset."""
        if not name or len(name.strip()) < 3:
            raise ValueError("Le nom du preset doit contenir au moins 3 caractères")
        return name.strip()

    @validates('description')
    def validate_description(self, key, description):
        """Valide la description du preset."""
        if description and len(description) > 500:
            raise ValueError("La description ne peut pas dépasser 500 caractères")
        return description
    
    @validates('target_type')
    def validate_target_type(self, key, value):
        """Valide le type de cible."""
        if value and not value in [t.value for t in ObjectType]:
            raise ValueError(f"Type de cible invalide: {value}")
        return value

    @validates('processing_params')
    def validate_processing_params(self, key, params):
        """Valide les paramètres de traitement."""
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                raise ValueError("Les paramètres doivent être un JSON valide")
        
        if not isinstance(params, dict):
            raise ValueError("Les paramètres doivent être un dictionnaire")
        
        # Validation des paramètres requis
        required_params = {'version', 'steps'}
        if not all(param in params for param in required_params):
            raise ValueError(f"Paramètres requis manquants: {required_params - params.keys()}")
        
        return params

    def __repr__(self):
        return (
            f"<Preset("
            f"name='{self.name}', "
            f"telescope_id='{self.telescope_id}', "
            f"filters_count={len(self.preset_filters)})>"
        )

    # Méthodes utilitaires
    def get_ordered_filters(self):
        """Retourne les filtres dans l'ordre d'application."""
        return [pf.filter for pf in sorted(self.preset_filters, key=lambda x: x.order)]

    def get_required_filters(self):
        """
        Retourne une liste des IDs de filtres requis par ce preset.
        
        Format: ["filter_id1", "filter_id2"]
        """
        return [str(pf.filter_id) for pf in self.preset_filters]

    def add_filter(self, filter_obj, order=None):
        """Ajoute un filtre au preset."""
        from app.infrastructure.repositories.models.preset_filter import PresetFilter
        
        if order is None:
            # Trouve le dernier ordre
            max_order = max([pf.order for pf in self.preset_filters], default=-1)
            order = max_order + 1

        preset_filter = PresetFilter(
            preset=self,
            filter=filter_obj,
            filter_order=order
        )
        self.preset_filters.append(preset_filter)
        return preset_filter

# Event Listeners
@event.listens_for(Preset, 'before_insert')
def validate_processing_params_json(mapper, connection, target):
    """Valide le format JSON des paramètres avant l'insertion."""
    if not isinstance(target.processing_params, dict):
        raise ValueError("processing_params doit être un dictionnaire")

@event.listens_for(Preset, 'before_update')
def check_filters_compatibility(mapper, connection, target):
    """Vérifie la compatibilité des filtres avec le télescope."""
    if hasattr(target, '_sa_instance_state'):
        # Vérifie si telescope_id a été modifié
        if 'telescope_id' in target._sa_instance_state.committed_state:
            for pf in target.preset_filters:
                if pf.filter.telescope_id != target.telescope_id:
                    raise ValueError(
                        f"Le filtre {pf.filter.name} n'est pas compatible "
                        f"avec le télescope sélectionné"
                    )
