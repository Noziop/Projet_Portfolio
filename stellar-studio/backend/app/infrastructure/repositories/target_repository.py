# app/infrastructure/repositories/target_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from .base_repository import BaseRepository
from ..repositories.models.target import Target as TargetModel
from app.domain.models.target import Target
from app.domain.value_objects.coordinates import Coordinates

class TargetRepository(BaseRepository[Target]):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    async def get_by_id(self, id: str) -> Optional[Target]:
        query = select(TargetModel).where(TargetModel.id == id)
        result = await self.db_session.execute(query)
        db_target = result.scalar_one_or_none()
        
        if db_target is None:
            return None
            
        return Target(
            id=db_target.id,
            name=db_target.name,
            description=db_target.description,
            telescope_id=db_target.telescope_id,
            coordinates=Coordinates(
                ra=db_target.coordinates_ra,
                dec=db_target.coordinates_dec
            ),
            object_type=db_target.object_type
        )

    async def list_by_telescope(self, telescope_id: str) -> List[Target]:
        query = select(TargetModel).where(TargetModel.telescope_id == telescope_id)
        result = await self.db_session.execute(query)
        db_targets = result.scalars().all()
        
        return [
            Target(
                id=db_target.id,
                name=db_target.name,
                description=db_target.description,
                telescope_id=db_target.telescope_id,
                coordinates=Coordinates(
                    ra=db_target.coordinates_ra,
                    dec=db_target.coordinates_dec
                ),
                object_type=db_target.object_type
            )
            for db_target in db_targets
        ]

    async def create(self, target: Target) -> Target:
        db_target = TargetModel(
            id=target.id,
            name=target.name,
            description=target.description,
            telescope_id=target.telescope_id,
            coordinates_ra=target.coordinates.ra,
            coordinates_dec=target.coordinates.dec,
            object_type=target.object_type
        )
        
        self.db_session.add(db_target)
        await self.db_session.commit()
        await self.db_session.refresh(db_target)
        
        return target

    async def update(self, target: Target) -> Target:
        query = select(TargetModel).where(TargetModel.id == target.id)
        result = await self.db_session.execute(query)
        db_target = result.scalar_one_or_none()
        
        if db_target is None:
            raise ValueError(f"Target with id {target.id} not found")
            
        db_target.name = target.name
        db_target.description = target.description
        db_target.telescope_id = target.telescope_id
        db_target.coordinates_ra = target.coordinates.ra
        db_target.coordinates_dec = target.coordinates.dec
        db_target.object_type = target.object_type
        
        await self.db_session.commit()
        await self.db_session.refresh(db_target)
        
        return target

    async def delete(self, id: str) -> bool:
        query = select(TargetModel).where(TargetModel.id == id)
        result = await self.db_session.execute(query)
        db_target = result.scalar_one_or_none()
        
        if db_target is None:
            return False
            
        await self.db_session.delete(db_target)
        await self.db_session.commit()
        
        return True
