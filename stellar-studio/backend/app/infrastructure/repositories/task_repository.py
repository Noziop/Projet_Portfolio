# app/infrastructure/repositories/task_repository.py
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.task import Task
from app.domain.value_objects.task_types import TaskType, TaskStatus
from uuid import UUID

class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

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
