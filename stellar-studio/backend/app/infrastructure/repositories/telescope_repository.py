# app/infrastructure/repositories/telescope_repository.py
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.telescope import SpaceTelescope
from app.domain.value_objects.telescope_types import TelescopeStatus

class TelescopeRepository(BaseRepository[SpaceTelescope]):
    def __init__(self, session: AsyncSession):
        super().__init__(SpaceTelescope, session)

    async def get_by_status(self, status: TelescopeStatus) -> List[SpaceTelescope]:
        query = select(SpaceTelescope).where(SpaceTelescope.status == status)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[SpaceTelescope]:
        query = select(SpaceTelescope).where(SpaceTelescope.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
