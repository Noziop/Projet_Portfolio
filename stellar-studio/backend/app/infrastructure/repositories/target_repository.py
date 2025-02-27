# app/infrastructure/repositories/target_repository.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.target import Target
from app.domain.value_objects.target_types import ObjectType, TargetStatus
from uuid import UUID

class TargetRepository(BaseRepository[Target]):
    def __init__(self, session: AsyncSession):
        super().__init__(Target, session)

    async def get_by_telescope(self, telescope_id: UUID) -> List[Target]:
        query = select(Target).where(Target.telescope_id == str(telescope_id))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_status(self, status: TargetStatus) -> List[Target]:
        query = select(Target).where(Target.status == status)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_type(self, object_type: ObjectType) -> List[Target]:
        query = select(Target).where(Target.object_type == object_type)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[Target]:
        query = select(Target).where(Target.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
