# app/infrastructure/repositories/models/observation.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.types import JSON
from app.db.base_class import Base
from datetime import datetime
from app.domain.value_objects.observation_types import InstrumentType, FilterType

class Observation(Base):
    __tablename__ = "observations"

    id = Column(String(36), primary_key=True)
    telescope_id = Column(String(36), ForeignKey("space_telescopes.id", ondelete="SET NULL"), nullable=True)
    target_id = Column(String(255))
    coordinates_ra = Column(String(50), nullable=False)
    coordinates_dec = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    exposure_time = Column(Integer, nullable=False)
    instrument = Column(Enum(InstrumentType), nullable=False)
    filters = Column(JSON)  # On garde JSON pour la liste d'enums
    fits_files = Column(JSON)
    preview_url = Column(String(255), nullable=True)
