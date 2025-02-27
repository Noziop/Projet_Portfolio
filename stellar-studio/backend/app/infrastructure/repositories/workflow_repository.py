# app/infrastructure/repositories/workflow_repository.py
from typing import List, Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.workflow import Workflow

class WorkflowRepository(BaseRepository[Workflow]):
    def __init__(self, session: AsyncSession):
        super().__init__(Workflow, session)

    async def get_by_target_type(self, target_type: str) -> List[Workflow]:
        """Récupère les workflows pour un type de cible"""
        query = select(Workflow).where(Workflow.target_type == target_type)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_default(self) -> Optional[Workflow]:
        """Récupère le workflow par défaut"""
        query = select(Workflow).where(Workflow.is_default == True)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def increment_execution_count(self, workflow_id: str) -> bool:
        """Incrémente le compteur d'exécutions"""
        query = select(Workflow).where(Workflow.id == workflow_id)
        result = await self.session.execute(query)
        workflow = result.scalar_one_or_none()
        
        if workflow:
            workflow.execution_count += 1
            await self.session.commit()
            return True
        return False

    async def update_estimated_duration(self, workflow_id: str, duration: int) -> bool:
        """Met à jour la durée estimée"""
        query = select(Workflow).where(Workflow.id == workflow_id)
        result = await self.session.execute(query)
        workflow = result.scalar_one_or_none()
        
        if workflow:
            workflow.estimated_duration = duration
            await self.session.commit()
            return True
        return False

    async def get_workflow_stats(self, workflow_id: str) -> Optional[Dict]:
        """Récupère les statistiques d'un workflow"""
        workflow = await self.get(workflow_id)
        if not workflow:
            return None

        query = select(
            func.count().label('total_executions'),
            func.avg(Workflow.estimated_duration).label('avg_duration')
        ).where(Workflow.id == workflow_id)
        
        result = await self.session.execute(query)
        stats = result.first()
        
        return {
            "total_executions": workflow.execution_count,
            "estimated_duration": workflow.estimated_duration,
            "average_duration": stats.avg_duration if stats else None
        }
