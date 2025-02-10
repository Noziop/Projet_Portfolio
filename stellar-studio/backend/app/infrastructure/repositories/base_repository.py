# app/infrastructure/repositories/base_repository.py
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, id: str) -> Optional[T]:
        raise NotImplementedError

    async def list(self) -> List[T]:
        raise NotImplementedError

    async def create(self, entity: T) -> T:
        raise NotImplementedError

    async def update(self, entity: T) -> T:
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        raise NotImplementedError
