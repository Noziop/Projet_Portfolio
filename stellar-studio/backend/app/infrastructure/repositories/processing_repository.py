# app/infrastructure/repositories/processing_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from .base_repository import BaseRepository
from ..repositories.models.processing import ProcessingJob as ProcessingJobModel, JobStatus
from app.domain.models.task import TaskStatus
from app.domain.models.processing import ProcessingJob

class ProcessingJobRepository(BaseRepository[ProcessingJob]):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    async def get_by_id(self, id: str) -> Optional[ProcessingJob]:
        query = select(ProcessingJobModel).where(ProcessingJobModel.id == id)
        result = await self.db_session.execute(query)
        db_job = result.scalar_one_or_none()
        
        if db_job is None:
            return None
            
        return ProcessingJob(
            id=str(db_job.id),
            user_id=db_job.user_id,
            telescope_id=db_job.telescope_id,
            workflow_id=db_job.workflow_id,
            status=TaskStatus[db_job.status.upper()],
            created_at=db_job.created_at,
            completed_at=db_job.completed_at,
            result_url=db_job.result_url
        )

    async def list_by_user(self, user_id: str) -> List[ProcessingJob]:
        query = select(ProcessingJobModel).where(ProcessingJobModel.user_id == user_id)
        result = await self.db_session.execute(query)
        db_jobs = result.scalars().all()
        
        return [
            ProcessingJob(
                id=str(db_job.id),
                user_id=db_job.user_id,
                telescope_id=db_job.telescope_id,
                workflow_id=db_job.workflow_id,
                status=TaskStatus[db_job.status.upper()],
                created_at=db_job.created_at,
                completed_at=db_job.completed_at,
                result_url=db_job.result_url
            )
            for db_job in db_jobs
        ]

    async def create(self, job: ProcessingJob) -> ProcessingJob:
        db_job = ProcessingJobModel(
            user_id=job.user_id,
            telescope_id=job.telescope_id,
            workflow_id=job.workflow_id,
            status=job.status.value,
            created_at=job.created_at,
            completed_at=job.completed_at,
            result_url=job.result_url
        )
        
        self.db_session.add(db_job)
        await self.db_session.commit()
        await self.db_session.refresh(db_job)
        
        return job

    async def update_status(self, job_id: str, status: TaskStatus, result_url: Optional[str] = None) -> ProcessingJob:
        query = select(ProcessingJobModel).where(ProcessingJobModel.id == job_id)
        result = await self.db_session.execute(query)
        db_job = result.scalar_one_or_none()
        
        if db_job is None:
            raise ValueError(f"ProcessingJob with id {job_id} not found")
            
        db_job.status = status.value
        db_job.completed_at = datetime.utcnow() if status == TaskStatus.COMPLETED else None
        db_job.result_url = result_url
        
        await self.db_session.commit()
        await self.db_session.refresh(db_job)
        
        return await self.get_by_id(job_id)

    async def delete(self, id: str) -> bool:
        query = select(ProcessingJobModel).where(ProcessingJobModel.id == id)
        result = await self.db_session.execute(query)
        db_job = result.scalar_one_or_none()
        
        if db_job is None:
            return False
            
        await self.db_session.delete(db_job)
        await self.db_session.commit()
        
        return True
