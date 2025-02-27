from sqlalchemy import Column, Float, DateTime, ForeignKey, CheckConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime, timezone
from app.db.base_class import Base

class Observation(Base):
    """Modèle SQLAlchemy pour les observations astronomiques.
    
    Ce modèle représente une observation unique d'une cible astronomique
    par un télescope spatial, incluant les métadonnées d'acquisition.
    """

    __tablename__ = "observations"

    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Relations
    target_id = Column(
        CHAR(36), 
        ForeignKey("targets.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID de la cible observée"
    )

    telescope_id = Column(
        CHAR(36), 
        ForeignKey("spacetelescopes.id", ondelete="SET NULL"),
        index=True,
        comment="ID du télescope ayant effectué l'observation"
    )

    # Colonnes - Métadonnées
    observation_date = Column(
        DateTime(timezone=True), 
        nullable=False,
        index=True,
        comment="Date et heure de l'observation (UTC)"
    )

    exposure_time = Column(
        Float, 
        nullable=False,
        comment="Temps d'exposition en secondes"
    )

    # Relations
    target = relationship(
        "Target", 
        back_populates="observations",
        lazy="joined"
    )

    telescope = relationship(
        "SpaceTelescope",
        back_populates="observations",
        lazy="joined"
    )

    # Validateurs
    @validates('exposure_time')
    def validate_exposure_time(self, key, exposure_time):
        if not isinstance(exposure_time, (int, float)) or exposure_time <= 0:
            raise ValueError("Le temps d'exposition doit être un nombre positif")
        return float(exposure_time)

    @validates('observation_date')
    def validate_observation_date(self, key, observation_date):
        if not isinstance(observation_date, datetime):
            raise ValueError("La date d'observation doit être un objet datetime")
        
        # Assurer que la date est en UTC
        if observation_date.tzinfo is None:
            observation_date = observation_date.replace(tzinfo=timezone.utc)
        
        # Vérifier que la date n'est pas dans le futur
        if observation_date > datetime.now(timezone.utc):
            raise ValueError("La date d'observation ne peut pas être dans le futur")
            
        return observation_date

    def __repr__(self):
        return (
            f"<Observation("
            f"target_id='{self.target_id}', "
            f"date='{self.observation_date}', "
            f"exposure={self.exposure_time}s)>"
        )

# Event Listeners
@event.listens_for(Observation, 'before_insert')
def set_defaults(mapper, connection, target):
    """Définit les valeurs par défaut avant l'insertion."""
    if target.observation_date is None:
        target.observation_date = datetime.now(timezone.utc)

@event.listens_for(Observation, 'before_update')
def validate_update(mapper, connection, target):
    """Valide les modifications avant la mise à jour."""
    if hasattr(target, '_sa_instance_state'):
        # Vérifie si observation_date a été modifiée
        if 'observation_date' in target._sa_instance_state.committed_state:
            new_date = target.observation_date
            if new_date > datetime.now(timezone.utc):
                raise ValueError("La date d'observation ne peut pas être dans le futur")
