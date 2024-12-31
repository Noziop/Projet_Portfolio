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

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    telescope_id = Column(Integer, ForeignKey("space_telescopes.id"), nullable=False)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    result_url = Column(String(255))
