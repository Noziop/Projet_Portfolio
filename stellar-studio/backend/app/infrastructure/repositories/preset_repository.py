# app/infrastructure/repositories/preset_repository.py
from typing import List, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.preset import Preset
from uuid import UUID
from sqlalchemy.orm import selectinload

class PresetRepository(BaseRepository[Preset]):
    def __init__(self, session: AsyncSession):
        super().__init__(Preset, session)

    async def get_by_telescope(self, telescope_id: UUID) -> List[Preset]:
        """Récupère tous les presets pour un télescope donné avec chargement contrôlé des relations"""
        query = (
            select(Preset)
            .where(Preset.telescope_id == str(telescope_id))
            .options(
                selectinload(Preset.telescope)
            )
            .order_by(Preset.name)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_object_type(self, object_type: str) -> List[Preset]:
        """Récupère les presets par type d'objet"""
        query = select(Preset).where(Preset.target_type == object_type)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_usage_stats(self, preset_id: UUID) -> Dict:
        """Récupère les statistiques d'utilisation d'un preset"""
        query = select(
            func.count().label('total_uses'),
            func.avg(Preset.processing_params['stretch_factor']).label('avg_stretch')
        ).where(Preset.id == str(preset_id))
        
        result = await self.session.execute(query)
        stats = result.first()
        
        return {
            "total_uses": stats.total_uses,
            "average_stretch": stats.avg_stretch
        }
