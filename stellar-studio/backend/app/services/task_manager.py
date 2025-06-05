# services/task_manager.py
from app.infrastructure.repositories.models.task import Task # Changed to SQLAlchemy model
from app.core.celery import celery_app
from app.db.session import SessionLocal
from datetime import datetime, timezone # Added import

class TaskManager:
    @staticmethod
    async def create_task(user_id: int, task_type: str, parameters: dict):
        async_task = celery_app.send_task(f"app.tasks.{task_type}", kwargs=parameters)
        
        db = SessionLocal()
        task = Task(
            id=async_task.id,
            user_id=user_id,
            type=task_type,
            status="PENDING",
            parameters=parameters,
            created_at=datetime.now(timezone.utc) # Added created_at
        )
        db.add(task)
        db.commit()
        
        return task