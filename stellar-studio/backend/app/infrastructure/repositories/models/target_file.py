#app/domain/models/target_file.py
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class TargetFile(Base):
    __tablename__ = "target_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    target_id = Column(String(36), ForeignKey("targets.id"), nullable=False)
    filter_id = Column(String(36), ForeignKey("filters.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size = Column(BigInteger)
    in_minio = Column(Boolean, default=False)
    fits_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    target = relationship("Target", back_populates="files")
    filter = relationship("Filter", back_populates="target_files")
