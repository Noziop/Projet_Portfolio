from sqlalchemy import (
    Column, String, JSON, Enum, CheckConstraint, event, 
    UniqueConstraint, Float
)
from sqlalchemy.orm import relationship, validates
from app.db.base_class import Base
from app.domain.value_objects.telescope_types import TelescopeStatus
import json
import re

class SpaceTelescope(Base):
    """Modèle SQLAlchemy pour les télescopes spatiaux.
    
    Ce modèle représente un télescope spatial avec ses caractéristiques
    techniques, son état opérationnel et ses relations avec les observations
    et autres entités du système.
    """

    __tablename__ = "spacetelescopes"

    __table_args__ = (
        UniqueConstraint('name', name='uq_telescope_name'),
        CheckConstraint(
            "JSON_VALID(instruments)", 
            name='check_valid_instruments_json'
        ),
        CheckConstraint(
            'length(name) >= 2',
            name='check_name_length'
        ),
        CheckConstraint(
            "aperture REGEXP '^[0-9]+(\\.[0-9]+)?[m]$'",
            name='check_aperture_format'
        ),
        CheckConstraint(
            "focal_length REGEXP '^[0-9]+(\\.[0-9]+)?[m]$'",
            name='check_focal_length_format'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Identification
    name = Column(
        String(255), 
        nullable=False, 
        unique=True, 
        index=True,
        comment="Nom unique du télescope"
    )
    
    description = Column(
        String(1000),
        comment="Description détaillée du télescope"
    )

    # Colonnes - Caractéristiques techniques
    aperture = Column(
        String(50), 
        nullable=False,
        comment="Diamètre de l'ouverture du télescope (en mètres)"
    )
    
    focal_length = Column(
        String(50), 
        nullable=False,
        comment="Distance focale du télescope (en mètres)"
    )
    
    location = Column(
        String(255), 
        nullable=False,
        comment="Position orbitale ou coordonnées du télescope"
    )

    # Colonnes - Configuration
    instruments = Column(
        JSON, 
        nullable=False, 
        default=[],
        comment="Liste des instruments disponibles au format JSON"
    )
    
    api_endpoint = Column(
        String(255), 
        nullable=False,
        comment="URL de l'API du télescope"
    )
    
    # Colonnes - État
    status = Column(
        Enum(TelescopeStatus), 
        nullable=False, 
        default=TelescopeStatus.OFFLINE,
        index=True,
        comment="État opérationnel actuel du télescope"
    )

    # Relations
    filters = relationship(
        "Filter", 
        back_populates="telescope",
        cascade="all, delete-orphan",
        lazy="noload"
    )
    
    targets = relationship(
        "Target", 
        back_populates="telescope",
        cascade="all, delete-orphan",
        lazy="noload"
    )
    
    presets = relationship(
        "Preset", 
        back_populates="telescope",
        cascade="all, delete-orphan",
        lazy="noload"
    )
    
    observations = relationship(
        "Observation", 
        back_populates="telescope",
        cascade="all, delete-orphan",
        lazy="noload",
        order_by="desc(Observation.observation_date)"
    )
    
    processing_jobs = relationship(
        "ProcessingJob", 
        back_populates="telescope",
        cascade="all, delete-orphan",
        lazy="noload"
    )

    # Validateurs
    @validates('name')
    def validate_name(self, key, name):
        """Valide le nom du télescope."""
        if not name or len(name.strip()) < 2:
            raise ValueError("Le nom doit contenir au moins 2 caractères")
        return name.strip()

    @validates('description')
    def validate_description(self, key, description):
        """Valide la description du télescope."""
        if description and len(description) > 1000:
            raise ValueError("La description ne peut pas dépasser 1000 caractères")
        return description

    @validates('aperture', 'focal_length')
    def validate_measurements(self, key, value):
        """Valide les mesures techniques."""
        pattern = r'^[0-9]+(\.[0-9]+)?m$'
        if not re.match(pattern, value):
            raise ValueError(f"{key} doit être au format 'Xm' ou 'X.Ym'")
        return value

    @validates('location')
    def validate_location(self, key, location):
        """Valide la localisation du télescope."""
        if not location or len(location.strip()) < 2:
            raise ValueError("La localisation doit être spécifiée")
        return location.strip()

    @validates('instruments')
    def validate_instruments(self, key, instruments):
        """Valide la liste des instruments."""
        if isinstance(instruments, str):
            try:
                instruments = json.loads(instruments)
            except json.JSONDecodeError:
                raise ValueError("La liste des instruments doit être un JSON valide")
        
        # Convertir une liste en dictionnaire si nécessaire
        if isinstance(instruments, list):
            instruments_dict = {}
            for instrument in instruments:
                if not isinstance(instrument, dict):
                    raise ValueError("Chaque instrument doit être un objet")
                if 'name' not in instrument or 'type' not in instrument:
                    raise ValueError("Chaque instrument doit avoir un nom et un type")
                # Utiliser le nom de l'instrument comme clé
                instruments_dict[instrument['name']] = {
                    'name': instrument['name'],
                    'description': instrument.get('type', ''),  # Utiliser type comme description par défaut
                    'wavelength_range': instrument.get('wavelength_range', None),
                    'resolution': instrument.get('resolution', None)
                }
            return instruments_dict
                
        # Si c'est déjà un dictionnaire, vérifier sa structure
        elif isinstance(instruments, dict):
            for key, instrument in instruments.items():
                if not isinstance(instrument, dict):
                    raise ValueError("Chaque instrument doit être un objet")
                if 'name' not in instrument:
                    instrument['name'] = key
                if 'description' not in instrument:
                    instrument['description'] = instrument.get('type', '')
            return instruments
            
        raise ValueError("Les instruments doivent être une liste ou un dictionnaire")

    @validates('api_endpoint')
    def validate_api_endpoint(self, key, url):
        """Valide l'URL de l'API."""
        pattern = r'^https?:\/\/.+$'
        if not re.match(pattern, url):
            raise ValueError("L'URL de l'API doit commencer par http:// ou https://")
        return url

    def __repr__(self):
        return (
            f"<SpaceTelescope("
            f"name='{self.name}', "
            f"aperture='{self.aperture}', "
            f"status={self.status.name})>"
        )

    # Propriétés calculées
    @property
    def aperture_meters(self) -> float:
        """Retourne l'ouverture en mètres."""
        return float(self.aperture.rstrip('m'))

    @property
    def focal_length_meters(self) -> float:
        """Retourne la distance focale en mètres."""
        return float(self.focal_length.rstrip('m'))

    @property
    def focal_ratio(self) -> float:
        """Calcule le rapport focal (f/D)."""
        return self.focal_length_meters / self.aperture_meters

    # Méthodes utilitaires
    def update_status(self, new_status: TelescopeStatus):
        """Met à jour le statut du télescope."""
        self.status = new_status
        
    def add_instrument(self, name: str, type: str, properties: dict = None):
        """Ajoute un nouvel instrument."""
        instrument = {
            'name': name,
            'type': type,
            **(properties or {})
        }
        self.instruments = [*self.instruments, instrument]

    def get_instrument(self, name: str) -> dict:
        """Récupère un instrument par son nom."""
        return next(
            (i for i in self.instruments if i['name'] == name),
            None
        )

# Event Listeners
@event.listens_for(SpaceTelescope, 'before_update')
def validate_status_transition(mapper, connection, target):
    """Vérifie les transitions de statut valides."""
    if hasattr(target, '_sa_instance_state'):
        if 'status' in target._sa_instance_state.committed_state:
            old_status = target._sa_instance_state.committed_state['status']
            new_status = target.status
            
            # Définir les transitions valides
            valid_transitions = {
                TelescopeStatus.OFFLINE: {TelescopeStatus.ONLINE, TelescopeStatus.MAINTENANCE},
                TelescopeStatus.ONLINE: {TelescopeStatus.OFFLINE, TelescopeStatus.MAINTENANCE},
                TelescopeStatus.MAINTENANCE: {TelescopeStatus.OFFLINE, TelescopeStatus.ONLINE}
            }
            
            if new_status not in valid_transitions[old_status]:
                raise ValueError(
                    f"Transition de statut invalide: {old_status.name} -> {new_status.name}"
                )

class TelescopeError(Exception):
    """Exception personnalisée pour les erreurs liées aux télescopes."""
    pass
