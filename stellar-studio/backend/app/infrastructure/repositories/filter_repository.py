# app/infrastructure/repositories/filter_repository.py
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.filter import Filter
from app.domain.value_objects.filter_types import FilterType
from uuid import UUID
from sqlalchemy.orm import selectinload, load_only

class FilterRepository(BaseRepository[Filter]):
    def __init__(self, session: AsyncSession):
        super().__init__(Filter, session)

    async def get_by_telescope(self, telescope_id: UUID) -> List[Filter]:
        """Récupère tous les filtres associés à un télescope donné
        
        Args:
            telescope_id: ID du télescope
            
        Returns:
            Liste des filtres associés au télescope
        """
        query = select(Filter).where(Filter.telescope_id == str(telescope_id))
        result = await self.session.execute(query)
        filters = result.scalars().all()
        
        return list(filters)

    async def get_by_type(self, filter_type: FilterType) -> List[Filter]:
        query = select(Filter).where(Filter.filter_type == filter_type)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[Filter]:
        """Récupère un filtre par son nom"""
        query = select(Filter).where(Filter.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_telescope_and_type(
        self, 
        telescope_id: UUID, 
        filter_type: FilterType
    ) -> List[Filter]:
        """Récupère tous les filtres d'un type pour un télescope donné"""
        query = select(Filter).where(
            and_(
                Filter.telescope_id == str(telescope_id),
                Filter.filter_type == filter_type
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_wavelength_range(
        self, 
        min_wavelength: int, 
        max_wavelength: int
    ) -> List[Filter]:
        """Récupère tous les filtres dans une plage de longueur d'onde"""
        query = select(Filter).where(
            and_(
                Filter.wavelength >= min_wavelength,
                Filter.wavelength <= max_wavelength
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

