# endpoints/tasks.py
from fastapi import APIRouter, Depends
from app.services.task_manager import TaskManager
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/tasks")
async def get_user_tasks(current_user = Depends(get_current_user)):
    return await TaskManager.get_user_tasks(current_user.id)