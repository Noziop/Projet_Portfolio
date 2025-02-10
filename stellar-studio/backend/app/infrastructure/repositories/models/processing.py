from app.domain.value_objects.processing_types import ProcessingStatus, ProcessingStepType
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    telescope_id = Column(String(36), ForeignKey("space_telescopes.id"), nullable=False)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)  # Ajout
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.get_default())
    steps = Column(JSON, default=ProcessingStepType.get_default_sequence)
    current_step = Column(Enum(ProcessingStepType), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    result_url = Column(String(255), nullable=True)
    error_message = Column(String(255), nullable=True)

