# app/db/base_class.py
from datetime import datetime
from typing import Any
from uuid import uuid4
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.mysql import CHAR

class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    # ID en CHAR(36) pour UUID MySQL
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Timestamps automatiques
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
