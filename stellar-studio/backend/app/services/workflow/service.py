# app/services/workflow/service.py
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, Gauge
from celery import chain

from app.core.ws.manager import ConnectionManager
from app.core.ws.events import (
    WebSocketEventType,
    create_download_started_event,
    create_processing_event,
    create_preview_event
)

from app.infrastructure.repositories.workflow_repository import WorkflowRepository
from app.infrastructure.repositories.processing_repository import ProcessingRepository
from app.infrastructure.repositories.target_repository import TargetRepository
from app.infrastructure.repositories.preset_repository import PresetRepository
from app.infrastructure.repositories.task_repository import TaskRepository
from app.infrastructure.repositories.models.workflow import Workflow
from app.infrastructure.repositories.models.processing import ProcessingJob
from app.infrastructure.repositories.models.task import Task

from app.domain.value_objects.task_types import TaskType, TaskStatus
from app.domain.value_objects.processing_types import ProcessingStepType

from app.services.storage.service import StorageService
from app.tasks.processing.tasks import (
    process_hoo_preset, 
    generate_channel_previews, 
    wait_user_validation
)

# Métriques Prometheus
workflow_operations = Counter(
    'workflow_operations_total',
    'Total number of workflow operations',
    ['operation', 'status']  # start, process, complete x success/failed
)

processing_duration = Histogram(
    'processing_duration_seconds',
    'Time spent processing images',
    ['preset_type'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

active_jobs = Gauge(
    'active_processing_jobs',
    'Number of currently active processing jobs'
)

class WorkflowService:
    def __init__(
        self,
        session: AsyncSession,
        storage_service: StorageService,
        ws_manager: ConnectionManager
    ):
        self.workflow_repository = WorkflowRepository(session)
        self.processing_repository = ProcessingRepository(session)
        self.target_repository = TargetRepository(session)
        self.preset_repository = PresetRepository(session)
        self.task_repository = TaskRepository(session)
        self.storage_service = storage_service
        self.ws_manager = ws_manager

    async def start_workflow(
        self,
        target_id: UUID,
        preset_id: UUID,
        user_id: UUID
    ) -> Optional[ProcessingJob]:
        """Démarre un nouveau workflow de traitement"""
        try:
            # Validation des données
            target = await self.target_repository.get(target_id)
            preset = await self.preset_repository.get(preset_id)
            
            if not target or not preset:
                workflow_operations.labels(operation='start', status='failed').inc()
                await self.ws_manager.send_error(
                    user_id,
                    "Target ou preset invalide"
                )
                return None

            # Création de la tâche
            task = Task(
                type=TaskType.PROCESSING,
                status=TaskStatus.PENDING,
                user_id=user_id,
                params={
                    "target_id": str(target_id),
                    "preset_id": str(preset_id)
                }
            )
            task = await self.task_repository.create(task)

            # Création du workflow
            workflow = await self.workflow_repository.get_default_for_type(target.object_type)
            
            # Calcul de la durée estimée
            estimated_duration = await self.calculate_estimated_duration(workflow.id)
            
            # Création du job de processing avec durée estimée
            job = ProcessingJob(
                user_id=user_id,
                telescope_id=target.telescope_id,
                workflow_id=workflow.id,
                target_id=target_id,
                preset_id=preset_id,
                task_id=task.id,
                current_step=ProcessingStepType.INITIALIZATION,
                estimated_duration=estimated_duration
            )
            
            job = await self.processing_repository.create(job)
            active_jobs.inc()

            # Notification WebSocket du démarrage
            await self.ws_manager.send_processing_update(
                user_id,
                create_processing_event(
                    str(job.id),
                    WebSocketEventType.PROCESSING_STARTED,
                    step="initialization",
                    details={
                        "target_id": str(target_id),
                        "preset_id": str(preset_id),
                        "estimated_duration": estimated_duration
                    }
                )
            )

            # Lancement des tâches Celery
            chain(
                generate_channel_previews.s(),
                wait_user_validation.s()
            ).apply_async()

            workflow_operations.labels(operation='start', status='success').inc()
            return job

        except Exception as e:
            workflow_operations.labels(operation='start', status='failed').inc()
            await self.ws_manager.send_error(
                user_id,
                f"Erreur lors du démarrage du workflow: {str(e)}"
            )
            raise

    async def get_processing_status(
        self,
        job_id: UUID
    ) -> Optional[Dict]:
        """Récupère le statut d'un traitement"""
        job = await self.processing_repository.get(job_id)
        if not job:
            return None

        task = await self.task_repository.get(job.task_id)
        return {
            "status": task.status,
            "current_step": job.current_step,
            "progress": job.steps if job.steps else {},
            "error": task.error
        }

    async def update_processing_step(
        self,
        job_id: UUID,
        step: ProcessingStepType,
        step_data: Optional[Dict] = None
    ) -> bool:
        """Met à jour l'étape de traitement"""
        job = await self.processing_repository.get(job_id)
        if not job:
            return False

        job.current_step = step
        if step_data:
            job.steps = {**job.steps, step.value: step_data} if job.steps else {step.value: step_data}
        
        await self.processing_repository.update(job)

        # Notification WebSocket
        await self.ws_manager.send_processing_update(
            job.user_id,
            create_processing_event(
                str(job.id),
                WebSocketEventType.PROCESSING_PROGRESS,
                step=step.value,
                details=step_data
            )
        )

        return True

    async def send_preview(
        self,
        job_id: UUID,
        preview_url: str,
        channel: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Envoie une preview via WebSocket"""
        job = await self.processing_repository.get(job_id)
        if job:
            await self.ws_manager.send_preview(
                job.user_id,
                create_preview_event(
                    str(job.id),
                    preview_url,
                    channel,
                    metadata
                )
            )

    async def complete_processing(
        self,
        job_id: UUID,
        result_data: Dict
    ) -> bool:
        """Termine un traitement"""
        with processing_duration.labels(preset_type='complete').time():
            job = await self.processing_repository.get(job_id)
            if not job:
                workflow_operations.labels(operation='complete', status='failed').inc()
                return False

            # Calcul de la durée réelle
            task = await self.task_repository.get(job.task_id)
            start_time = task.created_at
            end_time = datetime.utcnow()
            actual_duration = int((end_time - start_time).total_seconds())

            # Mise à jour des statistiques
            await self.update_workflow_stats(job.workflow_id, actual_duration)

            # Mise à jour de la tâche
            task.status = TaskStatus.COMPLETED
            task.result = result_data
            task.completed_at = end_time
            await self.task_repository.update(task)

            # Mise à jour du job
            job.current_step = ProcessingStepType.COMPLETED
            await self.processing_repository.update(job)
            
            # Notification WebSocket
            await self.ws_manager.send_processing_update(
                job.user_id,
                create_processing_event(
                    str(job.id),
                    WebSocketEventType.PROCESSING_COMPLETED,
                    step="completed",
                    details={
                        **result_data,
                        "actual_duration": actual_duration
                    }
                )
            )
            
            active_jobs.dec()
            workflow_operations.labels(operation='complete', status='success').inc()
            return True

    async def handle_processing_error(
        self,
        job_id: UUID,
        error_message: str
    ) -> bool:
        """Gère une erreur de traitement"""
        job = await self.processing_repository.get(job_id)
        if not job:
            return False

        # Mise à jour de la tâche
        task = await self.task_repository.get(job.task_id)
        task.status = TaskStatus.FAILED
        task.error = error_message
        await self.task_repository.update(task)

        # Mise à jour du job
        job.current_step = ProcessingStepType.ERROR
        job.error_message = error_message
        await self.processing_repository.update(job)
        
        # Notification WebSocket
        await self.ws_manager.send_error(
            job.user_id,
            error_message
        )
        
        active_jobs.dec()
        workflow_operations.labels(operation='process', status='failed').inc()
        return True

    async def get_user_processing_jobs(
        self,
        user_id: UUID,
        status: Optional[TaskStatus] = None
    ) -> List[ProcessingJob]:
        """Récupère les jobs de traitement d'un utilisateur"""
        return await self.processing_repository.get_by_user(user_id, status)

    async def calculate_estimated_duration(self, workflow_id: UUID) -> int:
        """Calcule la durée estimée d'un workflow basée sur l'historique"""
        workflow = await self.workflow_repository.get(workflow_id)
        if not workflow:
            return 0
        
        stats = await self.workflow_repository.get_workflow_stats(workflow_id)
        if not stats or workflow.execution_count == 0:
            return sum(step.estimated_duration or 0 for step in workflow.steps)
            
        return workflow.estimated_duration

    async def update_workflow_stats(self, workflow_id: UUID, actual_duration: int):
        """Met à jour les statistiques après exécution"""
        workflow = await self.workflow_repository.get(workflow_id)
        if workflow:
            # Incrémente le compteur d'exécutions
            workflow.execution_count += 1
            
            # Met à jour la durée estimée (moyenne mobile)
            workflow.estimated_duration = (workflow.estimated_duration or 0 + actual_duration) // 2
            await self.workflow_repository.update(workflow)

    async def get_workflow_stats(self, workflow_id: UUID) -> Optional[Dict]:
        """Récupère les statistiques d'un workflow"""
        workflow = await self.workflow_repository.get(workflow_id)
        if not workflow:
            return None
            
        return {
            "execution_count": workflow.execution_count,
            "estimated_duration": workflow.estimated_duration,
            "success_rate": await self.calculate_success_rate(workflow_id),
            "average_duration": await self.calculate_average_duration(workflow_id)
        }

    async def get_task(self, task_id: UUID, user_id: UUID) -> Optional[Dict]:
        """Récupère une tâche"""
        task = await self.task_repository.get(task_id)
        if not task or task.user_id != user_id:
            return None
            
        # Retourne un dictionnaire correctement formaté
        task_dict = {
            "id": task.id,
            "user_id": task.user_id,
            "status": task.status,
            "progress": task.progress if hasattr(task, "progress") else 0,
            "created_at": task.created_at,
            "updated_at": task.updated_at if hasattr(task, "updated_at") else None,
            "params": task.params if hasattr(task, "params") else {},
            "result": task.result if hasattr(task, "result") else None,
            "error": task.error if hasattr(task, "error") else None,
            "completed_at": task.completed_at if hasattr(task, "completed_at") else None,
            "type": task.type if hasattr(task, "type") else "PROCESSING"  # Valeur par défaut pour la rétrocompatibilité
        }
        
        return task_dict

    async def get_task_result(self, task_id: UUID, user_id: UUID) -> Optional[Dict]:
        """Récupère le résultat d'une tâche terminée"""
        task = await self.task_repository.get(task_id)
        if not task or task.user_id != user_id:
            return None
        
        # Vérifier explicitement si la tâche est terminée et a un résultat
        if not hasattr(task, "status") or task.status != TaskStatus.COMPLETED:
            return None
        
        if not hasattr(task, "result") or task.result is None:
            return None
        
        return task.result
