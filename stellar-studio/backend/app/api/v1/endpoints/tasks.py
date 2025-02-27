# app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.services.workflow.service import WorkflowService
from app.core.ws.manager import ConnectionManager
from app.schemas.task import TaskResponse
from app.schemas.processing import ProcessingJobCreate

router = APIRouter()

@router.post("/process", status_code=status.HTTP_202_ACCEPTED, response_model=TaskResponse)
async def process_with_preset(
    data: ProcessingJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Lance un traitement d'image avec un preset spécifique"""
    workflow_service = WorkflowService(
        session=db,
        ws_manager=ConnectionManager()
    )
    
    try:
        task = await workflow_service.start_workflow(
            target_id=data.target_id,
            preset_id=data.preset_id,
            user_id=current_user.id
        )
        
        return {"task_id": task.id, "status": task.status.value}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Vérifie le statut d'une tâche"""
    workflow_service = WorkflowService(
        session=db,
        ws_manager=ConnectionManager()
    )
    
    task = await workflow_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tâche non trouvée"
        )
        
    if str(task.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à accéder à cette tâche"
        )
        
    return {"task_id": task.id, "status": task.status.value, "progress": task.progress}

@router.get("/{task_id}/result")
async def get_task_result(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Récupère le résultat d'une tâche terminée"""
    workflow_service = WorkflowService(
        session=db,
        ws_manager=ConnectionManager()
    )
    
    result = await workflow_service.get_task_result(task_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Résultat non trouvé ou tâche non terminée"
        )
        
    return result
