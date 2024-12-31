# app/models/telescope.py
from sqlalchemy import Column, Integer, String, Text
from app.db.base_class import Base

class SpaceTelescope(Base):
    __tablename__ = "space_telescopes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)  # Ajout de la longueur
    description = Column(Text)
    api_endpoint = Column(String(255), nullable=False)  # Ajout de la longueur
