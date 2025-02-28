# app/infrastructure/repositories/user_repository.py
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.user import User
from app.schemas.user import UserCreate

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> Optional[User]:
        query = select(User).where(User.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Persiste un nouvel utilisateur en base de données"""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user