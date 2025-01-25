# app/infrastructure/repositories/models/workflow.py
from sqlalchemy import Column, String, Text, Boolean, JSON, ARRAY
from app.db.base_class import Base
from sqlalchemy.types import JSON

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True)  # Changé en String pour UUID
    name = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(JSON)  # Stockage des étapes du workflow en JSON
    is_default = Column(Boolean, default=False)
    target_type = Column(String(100), nullable=False)  # Ajouté
    required_filters = Column(JSON)

