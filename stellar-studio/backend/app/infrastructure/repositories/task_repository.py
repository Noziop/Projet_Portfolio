# app/infrastructure/repositories/task_repository.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.task import Task
from app.domain.value_objects.task_types import TaskType, TaskStatus
from uuid import UUID

class TaskRepository(BaseRepository[Task]):
    def __init__(self, session):
        # Le session peut être AsyncSession ou Session (synchrone)
        super().__init__(Task, session)
        self.is_async = isinstance(session, AsyncSession)

    async def get_by_user(self, user_id: UUID) -> List[Task]:
        query = select(Task).where(Task.user_id == str(user_id))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_status(self, status: TaskStatus) -> List[Task]:
        query = select(Task).where(Task.status == status)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_type(self, task_type: TaskType) -> List[Task]:
        query = select(Task).where(Task.type == task_type)
        result = await self.session.execute(query)
        return result.scalars().all()
        
    # Méthodes synchrones pour Celery
    def get_sync(self, id: UUID) -> Optional[Task]:
        """Version synchrone de get() pour les contextes Celery"""
        if self.is_async:
            raise ValueError("Cette méthode ne doit être utilisée qu'avec une session synchrone")
        return self.session.query(self.model).filter(self.model.id == id).first()
        
    def update_sync(self, entity) -> Task:
        """Version synchrone de update() pour les contextes Celery"""
        if self.is_async:
            raise ValueError("Cette méthode ne doit être utilisée qu'avec une session synchrone")
        self.session.add(entity)
        return entity
        
    def get_by_user_sync(self, user_id: UUID) -> List[Task]:
        """Version synchrone de get_by_user() pour les contextes Celery"""
        if self.is_async:
            raise ValueError("Cette méthode ne doit être utilisée qu'avec une session synchrone")
        return self.session.query(self.model).filter(self.model.user_id == str(user_id)).all()
