# app/models/processing.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, CHAR
from sqlalchemy.sql import func
import enum
from app.db.base_class import Base

class JobStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True)  # Changé en String(36)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    telescope_id = Column(String(36), ForeignKey("space_telescopes.id"), nullable=False)  # Changé en String(36)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)  # Changé en String(36)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    result_url = Column(String(255))
