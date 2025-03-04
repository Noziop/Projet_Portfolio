# app/infrastructure/repositories/target_file_repository.py
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.target_file import TargetFile
from uuid import UUID

class TargetFileRepository(BaseRepository[TargetFile]):
    def __init__(self, session: AsyncSession):
        super().__init__(TargetFile, session)

    async def get_by_target(self, target_id: UUID) -> List[TargetFile]:
        target_id_str = str(target_id) if isinstance(target_id, UUID) else target_id
        query = select(TargetFile).where(TargetFile.target_id == target_id_str)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_filter(self, filter_id: UUID) -> List[TargetFile]:
        filter_id_str = str(filter_id) if isinstance(filter_id, UUID) else filter_id
        query = select(TargetFile).where(TargetFile.filter_id == filter_id_str)
        result = await self.session.execute(query)
        return result.scalars().all()
