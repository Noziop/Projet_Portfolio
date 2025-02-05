#app/domain/models/preset.py
from uuid import uuid4
from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Preset(Base):
    __tablename__ = "presets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String)
    processing_params = Column(JSON)
    telescope_id = Column(String(36), ForeignKey("space_telescopes.id"), nullable=False)

    # Relations
    telescope = relationship("SpaceTelescope", back_populates="presets")
    filters = relationship("Filter", secondary="preset_filters", back_populates="presets")
    processing_jobs = relationship("ProcessingJob", back_populates="preset")
