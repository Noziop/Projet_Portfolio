# app/infrastructure/repositories/models/target.py
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from app.db.base_class import Base
from sqlalchemy.types import JSON


class Target(Base):
    __tablename__ = "targets"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    telescope_id = Column(String(36), ForeignKey("space_telescopes.id"))
    coordinates_ra = Column(String(50), nullable=False)
    coordinates_dec = Column(String(50), nullable=False)
    object_type = Column(String(100), nullable=False)  # 'nebula', 'galaxy', etc.
    extra_data = Column(JSON, nullable=True)  # Renommé de metadata à extra_data
