# app/models/workflow.py
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON
from app.db.base_class import Base

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(JSON)  # Stockage des étapes du workflow en JSON
    is_default = Column(Boolean, default=False)
