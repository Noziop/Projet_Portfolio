# app/infrastructure/repositories/processing_repository.py - Version corrigée
from typing import List, Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.processing import ProcessingJob
from app.domain.value_objects.processing_types import ProcessingStatus
from uuid import UUID

class ProcessingRepository(BaseRepository[ProcessingJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(ProcessingJob, session)

    async def get_by_user(self, user_id: UUID, status: Optional[ProcessingStatus] = None) -> List[ProcessingJob]:
        query = select(ProcessingJob).where(ProcessingJob.user_id == str(user_id))
        if status:
            query = query.where(ProcessingJob.status == status)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_target(self, target_id: UUID) -> List[ProcessingJob]:
        query = select(ProcessingJob).where(ProcessingJob.target_id == str(target_id))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_intermediate_results(self, job_id: UUID, results: Dict) -> bool:
        """Met à jour les résultats intermédiaires"""
        job = await self.get(job_id)
        if job:
            job.intermediate_results = results
            await self.session.commit()
            return True
        return False

    async def get_job_stats(self, job_id: UUID) -> Optional[Dict]:
        """Récupère les statistiques d'un job"""
        job = await self.get(job_id)
        if not job:
            return None

        # Modifier cette requête pour utiliser des champs qui existent réellement
        # Par exemple, compter le nombre d'étapes au lieu d'utiliser progress
        query = select(
            func.count().label('total_steps'),
            # Remplacer par une métrique qui existe ou supprimer cette ligne
            func.count(ProcessingJob.steps).label('avg_progress')
        ).where(ProcessingJob.id == str(job_id))
        
        result = await self.session.execute(query)
        stats = result.first()

        return {
            "status": job.status,
            # Remplacer progress par une autre métrique ou le supprimer
            "progress": len(job.steps) if job.steps else 0,  # Utiliser la longueur des étapes comme indicateur de progression
            "total_steps": stats.total_steps,
            "average_progress": stats.avg_progress,
            "intermediate_results": job.intermediate_results
        }
