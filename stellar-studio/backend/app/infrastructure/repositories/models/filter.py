#app/domain/models/filter.py
from uuid import uuid4
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Filter(Base):
    __tablename__ = "filters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(50), nullable=False)
    telescope_id = Column(String(36), ForeignKey("space_telescopes.id"), nullable=False)
    wavelength = Column(Float)
    description = Column(String)

    # Relations
    telescope = relationship("SpaceTelescope", back_populates="filters")
    presets = relationship("Preset", secondary="preset_filters", back_populates="filters")
    target_files = relationship("TargetFile", back_populates="filter")
