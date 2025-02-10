# app/infrastructure/repositories/telescope_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from .base_repository import BaseRepository
from ..repositories.models.telescope import SpaceTelescope as TelescopeModel
from app.domain.models.telescope import Telescope

class TelescopeRepository(BaseRepository[Telescope]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)

    def _to_domain(self, db_telescope: TelescopeModel) -> Telescope:
        return Telescope(
            id=db_telescope.id,
            name=db_telescope.name,
            description=db_telescope.description,
            aperture=db_telescope.aperture,
            focal_length=db_telescope.focal_length,
            location=db_telescope.location,
            instruments=db_telescope.instruments,
            api_endpoint=db_telescope.api_endpoint,
            status=db_telescope.status
        )

    async def get_by_name(self, name: str) -> Optional[Telescope]:
        query = select(TelescopeModel).where(TelescopeModel.name == name)
        result = await self.db_session.execute(query)
        db_telescope = result.scalar_one_or_none()
        return self._to_domain(db_telescope) if db_telescope else None

    async def get_by_id(self, id: str) -> Optional[Telescope]:
        query = select(TelescopeModel).where(TelescopeModel.id == id)
        result = await self.db_session.execute(query)
        db_telescope = result.scalar_one_or_none()
        
        if db_telescope is None:
            return None
            
        return Telescope(
            id=db_telescope.id,
            name=db_telescope.name,
            description=db_telescope.description,
            aperture=db_telescope.aperture,
            focal_length=db_telescope.focal_length,
            location=db_telescope.location,
            instruments=db_telescope.instruments,
            api_endpoint=db_telescope.api_endpoint
        )

    async def list(self) -> List[Telescope]:
        query = select(TelescopeModel)
        result = await self.db_session.execute(query)
        db_telescopes = result.scalars().all()
        
        return [
            Telescope(
                id=db_telescope.id,
                name=db_telescope.name,
                description=db_telescope.description,
                aperture=db_telescope.aperture,
                focal_length=db_telescope.focal_length,
                location=db_telescope.location,
                instruments=db_telescope.instruments,
                api_endpoint=db_telescope.api_endpoint
            )
            for db_telescope in db_telescopes
        ]

    async def create(self, telescope: Telescope) -> Telescope:
        db_telescope = TelescopeModel(
            id=telescope.id,
            name=telescope.name,
            description=telescope.description,
            aperture=telescope.aperture,
            focal_length=telescope.focal_length,
            location=telescope.location,
            instruments=telescope.instruments,
            api_endpoint=telescope.api_endpoint
        )
        
        self.db_session.add(db_telescope)
        await self.db_session.commit()
        await self.db_session.refresh(db_telescope)
        
        return telescope

    async def update(self, telescope: Telescope) -> Telescope:
        query = select(TelescopeModel).where(TelescopeModel.id == telescope.id)
        result = await self.db_session.execute(query)
        db_telescope = result.scalar_one_or_none()
        
        if db_telescope is None:
            raise ValueError(f"Telescope with id {telescope.id} not found")
            
        db_telescope.name = telescope.name
        db_telescope.description = telescope.description
        db_telescope.aperture = telescope.aperture
        db_telescope.focal_length = telescope.focal_length
        db_telescope.location = telescope.location
        db_telescope.instruments = telescope.instruments
        db_telescope.api_endpoint = telescope.api_endpoint
        
        await self.db_session.commit()
        await self.db_session.refresh(db_telescope)
        
        return telescope

    async def delete(self, id: str) -> bool:
        query = select(TelescopeModel).where(TelescopeModel.id == id)
        result = await self.db_session.execute(query)
        db_telescope = result.scalar_one_or_none()
        
        if db_telescope is None:
            return False
            
        await self.db_session.delete(db_telescope)
        await self.db_session.commit()
        
        return True
