from fastapi import APIRouter, Depends
from app.services.task_manager import TaskManager
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/download")
async def start_download(
    telescope: str,
    object_name: str,
    current_user = Depends(get_current_user)
):
    task = await TaskManager.create_task(
        current_user.id,
        "download_fits",
        {"telescope": telescope, "object_name": object_name}
    )
    return {"task_id": task.id}
