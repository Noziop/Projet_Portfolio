# app/infrastructure/repositories/base_repository.py
from typing import Generic, TypeVar, Type, Optional, List
import time
import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base_class import Base

# Logging
logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> Optional[ModelType]:
        start_time = time.time()
        logger.debug(f"DB: Fetching {self.model.__name__} with id={id}")
        
        query = select(self.model).where(self.model.id == str(id))
        result = await self.session.execute(query)
        obj = result.scalar_one_or_none()
        
        query_time = time.time() - start_time
        if obj:
            logger.debug(f"DB: Found {self.model.__name__} in {query_time:.3f}s")
        else:
            logger.debug(f"DB: {self.model.__name__} with id={id} not found ({query_time:.3f}s)")
            
        # Log une alerte si la requête est trop lente
        if query_time > 0.5:  # seuil d'alerte: 0.5 seconde
            logger.warning(f"Slow query detected: get {self.model.__name__} took {query_time:.3f}s")
            
        return obj

    async def get_all(self) -> List[ModelType]:
        start_time = time.time()
        logger.debug(f"DB: Fetching all {self.model.__name__} records")
        
        query = select(self.model)
        result = await self.session.execute(query)
        objects = result.scalars().all()
        
        query_time = time.time() - start_time
        logger.debug(f"DB: Retrieved {len(objects)} {self.model.__name__} records in {query_time:.3f}s")
        
        # Log une alerte si la requête est trop lente
        if query_time > 1.0:  # seuil d'alerte: 1 seconde
            logger.warning(f"Slow query detected: get_all {self.model.__name__} took {query_time:.3f}s")
            
        return objects

    async def create(self, obj_in: ModelType) -> ModelType:
        self.session.add(obj_in)
        await self.session.commit()
        await self.session.refresh(obj_in)
        return obj_in

    async def update(self, obj_in: ModelType) -> ModelType:
        await self.session.merge(obj_in)
        await self.session.commit()
        return obj_in

    async def delete(self, id: UUID) -> bool:
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False
