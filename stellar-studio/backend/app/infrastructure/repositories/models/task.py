# app/infrastructure/repositories/models/task.py
from sqlalchemy import Column, String, ForeignKey, DateTime, JSON
from app.db.base_class import Base
from datetime import datetime

class Task(Base):
    __tablename__ = "tasks"  # Ajout du nom de table au pluriel pour cohérence

    id = Column(String(36), primary_key=True)  # Spécification de la longueur pour UUID
    user_id = Column(String(36), ForeignKey("users.id"))  # Changé pour correspondre au type d'ID des users
    type = Column(String(50), nullable=False)  # Ajout de la longueur et nullable=False
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    parameters = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
