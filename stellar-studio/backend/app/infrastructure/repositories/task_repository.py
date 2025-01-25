# app/infrastructure/repositories/task_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from .base_repository import BaseRepository
from ..repositories.models.task import Task as TaskModel
from app.domain.models.task import Task, TaskStatus, TaskType

class TaskRepository(BaseRepository[Task]):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    async def get_by_id(self, id: str) -> Optional[Task]:
        query = select(TaskModel).where(TaskModel.id == id)
        result = await self.db_session.execute(query)
        db_task = result.scalar_one_or_none()
        
        if db_task is None:
            return None
            
        return Task(
            id=db_task.id,
            user_id=db_task.user_id,
            type=TaskType[db_task.type.upper()],
            status=TaskStatus[db_task.status.upper()],
            parameters=db_task.parameters,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
            result=db_task.result,
            error_message=db_task.result.get('error') if db_task.result else None
        )

    async def list_by_user(self, user_id: str) -> List[Task]:
        query = select(TaskModel).where(TaskModel.user_id == user_id)
        result = await self.db_session.execute(query)
        db_tasks = result.scalars().all()
        
        return [
            Task(
                id=db_task.id,
                user_id=db_task.user_id,
                type=TaskType[db_task.type.upper()],
                status=TaskStatus[db_task.status.upper()],
                parameters=db_task.parameters,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at,
                result=db_task.result,
                error_message=db_task.result.get('error') if db_task.result else None
            )
            for db_task in db_tasks
        ]

    async def create(self, task: Task) -> Task:
        db_task = TaskModel(
            id=task.id,
            user_id=task.user_id,
            type=task.type.value,
            status=task.status.value,
            parameters=task.parameters,
            created_at=task.created_at,
            updated_at=task.updated_at,
            result=task.result
        )
        
        self.db_session.add(db_task)
        await self.db_session.commit()
        await self.db_session.refresh(db_task)
        
        return task

    async def update_status(self, task_id: str, status: TaskStatus, result: dict = None) -> Task:
        query = select(TaskModel).where(TaskModel.id == task_id)
        result_db = await self.db_session.execute(query)
        db_task = result_db.scalar_one_or_none()
        
        if db_task is None:
            raise ValueError(f"Task with id {task_id} not found")
            
        db_task.status = status.value
        db_task.updated_at = datetime.utcnow()
        if result:
            db_task.result = result
        
        await self.db_session.commit()
        await self.db_session.refresh(db_task)
        
        return await self.get_by_id(task_id)

    async def list(self) -> List[Task]:
        query = select(TaskModel)
        result = await self.db_session.execute(query)
        db_tasks = result.scalars().all()
        
        return [
            Task(
                id=db_task.id,
                user_id=db_task.user_id,
                type=TaskType[db_task.type.upper()],
                status=TaskStatus[db_task.status.upper()],
                parameters=db_task.parameters,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at,
                result=db_task.result,
                error_message=db_task.result.get('error') if db_task.result else None
            )
            for db_task in db_tasks
        ]

    async def delete(self, id: str) -> bool:
        query = select(TaskModel).where(TaskModel.id == id)
        result = await self.db_session.execute(query)
        db_task = result.scalar_one_or_none()
        
        if db_task is None:
            return False
            
        await self.db_session.delete(db_task)
        await self.db_session.commit()
        
        return True
