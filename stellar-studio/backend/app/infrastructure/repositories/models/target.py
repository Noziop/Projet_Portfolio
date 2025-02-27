from sqlalchemy import (
    Column, String, ForeignKey, Enum, CheckConstraint, 
    event, UniqueConstraint, func
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
from app.domain.value_objects.target_types import ObjectType, TargetStatus
import re

class Target(Base):
    """Modèle SQLAlchemy pour les cibles astronomiques.
    
    Ce modèle représente une cible astronomique (galaxie, nébuleuse, etc.)
    avec ses coordonnées, métadonnées et relations avec les observations
    et traitements associés.
    """

    __tablename__ = "targets"

    __table_args__ = (
        UniqueConstraint(
            'catalog_name', 'telescope_id',
            name='uq_catalog_telescope'
        ),
        CheckConstraint(
            "coordinates_ra REGEXP '^[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?$'",
            name='check_ra_format'
        ),
        CheckConstraint(
            "coordinates_dec REGEXP '^[+-][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?$'",
            name='check_dec_format'
        ),
        CheckConstraint(
            'length(name) >= 2',
            name='check_name_length'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Identification
    name = Column(
        String(255), 
        nullable=False, 
        index=True,
        comment="Nom descriptif de la cible"
    )
    
    catalog_name = Column(
        String(100), 
        index=True,
        comment="Identifiant de catalogue (ex: NGC6302)"
    )
    
    common_name = Column(
        String(255), 
        index=True,
        comment="Nom commun (ex: Butterfly Nebula)"
    )
    
    description = Column(
        String(1000),
        comment="Description détaillée de la cible"
    )

    # Colonnes - Relations
    telescope_id = Column(
        CHAR(36), 
        ForeignKey("spacetelescopes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID du télescope associé"
    )

    # Colonnes - Coordonnées
    coordinates_ra = Column(
        String(50), 
        nullable=False,
        comment="Ascension droite (format: HH:MM:SS.sss)"
    )
    
    coordinates_dec = Column(
        String(50), 
        nullable=False,
        comment="Déclinaison (format: ±DD:MM:SS.sss)"
    )

    # Colonnes - Classification et État
    object_type = Column(
        Enum(ObjectType), 
        nullable=False,
        index=True,
        comment="Type d'objet astronomique"
    )
    
    status = Column(
        Enum(TargetStatus), 
        nullable=False, 
        default=TargetStatus.NEEDS_DOWNLOAD,
        index=True,
        comment="État actuel de la cible"
    )

    # Relations
    telescope = relationship(
        "SpaceTelescope", 
        back_populates="targets",
        lazy="joined"
    )
    
    files = relationship(
        "TargetFile", 
        back_populates="target",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    observations = relationship(
        "Observation", 
        back_populates="target",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Observation.observation_date)"
    )
    
    processing_jobs = relationship(
        "ProcessingJob", 
        back_populates="target",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    target_presets = relationship(
        "TargetPreset", 
        back_populates="target",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Validateurs
    @validates('name')
    def validate_name(self, key, name):
        """Valide le nom de la cible."""
        if not name or len(name.strip()) < 2:
            raise ValueError("Le nom doit contenir au moins 2 caractères")
        return name.strip()

    @validates('catalog_name')
    def validate_catalog_name(self, key, catalog_name):
        """Valide le nom de catalogue."""
        if catalog_name:
            # Format typique: NGC1234, M31, IC342, etc.
            pattern = r'^[A-Za-z]+[0-9]+[A-Za-z0-9-]*$'
            if not re.match(pattern, catalog_name):
                raise ValueError("Format de nom de catalogue invalide")
        return catalog_name

    @validates('coordinates_ra')
    def validate_ra(self, key, ra):
        """Valide l'ascension droite."""
        pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?$'
        if not re.match(pattern, ra):
            raise ValueError("Format d'ascension droite invalide (HH:MM:SS.sss)")
        return ra

    @validates('coordinates_dec')
    def validate_dec(self, key, dec):
        """Valide la déclinaison."""
        pattern = r'^[+-]([0-8][0-9]|90):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?$'
        if not re.match(pattern, dec):
            raise ValueError("Format de déclinaison invalide (±DD:MM:SS.sss)")
        return dec

    @validates('description')
    def validate_description(self, key, description):
        """Valide la description."""
        if description and len(description) > 1000:
            raise ValueError("La description ne peut pas dépasser 1000 caractères")
        return description

    def __repr__(self):
        return (
            f"<Target("
            f"name='{self.name}', "
            f"catalog='{self.catalog_name}', "
            f"type={self.object_type.name}, "
            f"status={self.status.name})>"
        )

    # Méthodes utilitaires
    @property
    def coordinates(self):
        """Retourne les coordonnées formatées."""
        return {
            'ra': self.coordinates_ra,
            'dec': self.coordinates_dec
        }

    @property
    def latest_observation(self):
        """Retourne la dernière observation."""
        return self.observations[0] if self.observations else None

    @property
    def available_presets(self):
        """Retourne les presets disponibles."""
        return [tp.preset for tp in self.target_presets if tp.is_available]

    def update_status(self, new_status: TargetStatus):
        """Met à jour le statut de la cible."""
        self.status = new_status

    def add_preset(self, preset, is_available=True):
        """Ajoute un preset à la cible."""
        from app.infrastructure.repositories.models.target_preset import TargetPreset
        target_preset = TargetPreset(
            target=self,
            preset=preset,
            is_available=is_available
        )
        self.target_presets.append(target_preset)
        return target_preset

    def get_files_by_filter(self, filter_id):
        """Retourne les fichiers pour un filtre donné."""
        return [f for f in self.files if f.filter_id == filter_id]

# Event Listeners
@event.listens_for(Target, 'before_insert')
def validate_coordinates(mapper, connection, target):
    """Vérifie la validité des coordonnées avant insertion."""
    # Conversion RA en valeur décimale pour validation
    ra_parts = [float(x) for x in target.coordinates_ra.split(':')]
    ra_decimal = ra_parts[0] + ra_parts[1]/60 + ra_parts[2]/3600
    if not 0 <= ra_decimal < 24:
        raise ValueError("L'ascension droite doit être entre 0h et 24h")

    # Conversion DEC en valeur décimale pour validation
    dec_parts = [float(x) for x in target.coordinates_dec[1:].split(':')]
    dec_decimal = dec_parts[0] + dec_parts[1]/60 + dec_parts[2]/3600
    if target.coordinates_dec[0] == '-':
        dec_decimal = -dec_decimal
    if not -90 <= dec_decimal <= 90:
        raise ValueError("La déclinaison doit être entre -90° et +90°")

@event.listens_for(Target, 'before_update')
def check_status_transition(mapper, connection, target):
    """Vérifie les transitions de statut valides."""
    if hasattr(target, '_sa_instance_state'):
        if 'status' in target._sa_instance_state.committed_state:
            old_status = target._sa_instance_state.committed_state['status']
            new_status = target.status
            
            # Définir les transitions valides
            valid_transitions = {
                TargetStatus.NEEDS_DOWNLOAD: {
                    TargetStatus.DOWNLOADING,
                    TargetStatus.FAILED
                },
                TargetStatus.DOWNLOADING: {
                    TargetStatus.READY,
                    TargetStatus.FAILED
                },
                TargetStatus.READY: {
                    TargetStatus.PROCESSING,
                    TargetStatus.FAILED
                },
                TargetStatus.PROCESSING: {
                    TargetStatus.READY,
                    TargetStatus.COMPLETED,
                    TargetStatus.FAILED
                },
                TargetStatus.COMPLETED: {
                    TargetStatus.READY,
                    TargetStatus.NEEDS_DOWNLOAD
                },
                TargetStatus.FAILED: {
                    TargetStatus.NEEDS_DOWNLOAD
                }
            }
            
            if new_status not in valid_transitions[old_status]:
                raise ValueError(
                    f"Transition de statut invalide: {old_status.name} -> {new_status.name}"
                )

class TargetError(Exception):
    """Exception personnalisée pour les erreurs liées aux cibles."""
    pass
