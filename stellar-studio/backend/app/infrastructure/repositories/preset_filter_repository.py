# app/infrastructure/repositories/preset_filter_repository.py
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.preset_filter import PresetFilter
from uuid import UUID

class PresetFilterRepository(BaseRepository[PresetFilter]):
    def __init__(self, session: AsyncSession):
        super().__init__(PresetFilter, session)

    async def get_by_preset(self, preset_id: UUID) -> List[PresetFilter]:
        query = select(PresetFilter).where(PresetFilter.preset_id == str(preset_id))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_filter(self, filter_id: UUID) -> List[PresetFilter]:
        query = select(PresetFilter).where(PresetFilter.filter_id == str(filter_id))
        result = await self.session.execute(query)
        return result.scalars().all()
