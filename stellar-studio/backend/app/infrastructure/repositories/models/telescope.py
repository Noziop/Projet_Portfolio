# app/infrastructure/repositories/models/telescope.py
from sqlalchemy import Column, String, Text, ARRAY
from app.db.base_class import Base
from sqlalchemy.types import JSON

class SpaceTelescope(Base):
    __tablename__ = "space_telescopes"

    id = Column(String(36), primary_key=True)  # Changé en String pour UUID
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    aperture = Column(String(50), nullable=False)  # Ajouté
    focal_length = Column(String(50), nullable=False)  # Ajouté
    location = Column(String(255), nullable=False)  # Ajouté
    instruments = Column(JSON)  # Suppression de la virgule ici
    api_endpoint = Column(String(255), nullable=False)
