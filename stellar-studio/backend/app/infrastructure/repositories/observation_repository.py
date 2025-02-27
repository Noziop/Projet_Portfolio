# app/infrastructure/repositories/observation_repository.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.observation import Observation
from uuid import UUID

class ObservationRepository(BaseRepository[Observation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Observation, session)

    async def get_by_target(self, target_id: UUID) -> List[Observation]:
        """Récupère toutes les observations d'une cible"""
        query = select(Observation).where(Observation.target_id == str(target_id))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_telescope(self, telescope_id: UUID) -> List[Observation]:
        """Récupère toutes les observations d'un télescope"""
        query = select(Observation).where(Observation.telescope_id == str(telescope_id))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        target_id: Optional[UUID] = None
    ) -> List[Observation]:
        """Récupère les observations dans une plage de dates, optionnellement pour une cible spécifique"""
        conditions = [
            Observation.observation_date >= start_date,
            Observation.observation_date <= end_date
        ]
        if target_id:
            conditions.append(Observation.target_id == str(target_id))
            
        query = select(Observation).where(and_(*conditions))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_target(self, target_id: UUID) -> Optional[Observation]:
        """Récupère la dernière observation d'une cible"""
        query = (
            select(Observation)
            .where(Observation.target_id == str(target_id))
            .order_by(desc(Observation.observation_date))
        )
        result = await self.session.execute(query)
        return await result.scalar_one_or_none()
