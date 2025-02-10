# app/infrastructure/repositories/models/telescope.py
from sqlalchemy import Column, String, Text, Enum
from app.db.base_class import Base
from sqlalchemy.types import JSON
from app.domain.value_objects.telescope_types import TelescopeStatus

class SpaceTelescope(Base):
    __tablename__ = "space_telescopes"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    aperture = Column(String(50), nullable=False)
    focal_length = Column(String(50), nullable=False)
    location = Column(String(255), nullable=False)
    instruments = Column(JSON)
    api_endpoint = Column(String(255), nullable=False)
    status = Column(Enum(TelescopeStatus), default=TelescopeStatus.OFFLINE)
