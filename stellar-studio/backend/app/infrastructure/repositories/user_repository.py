from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone

from .base_repository import BaseRepository
from .models.user import User as UserModel
from app.domain.models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    async def get_by_id(self, id: str) -> Optional[User]:
        query = select(UserModel).where(UserModel.id == id)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        return self._map_to_domain(db_user) if db_user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(UserModel).where(UserModel.email == email)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        return self._map_to_domain(db_user) if db_user else None

    async def create(self, user: User, hashed_password: str) -> User:
        db_user = UserModel(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            firstname=user.firstname,
            lastname=user.lastname,
            role=user.role,
            level=user.level,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        
        self.db_session.add(db_user)
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        
        return self._map_to_domain(db_user)

    async def update(self, user: User) -> User:
        query = select(UserModel).where(UserModel.id == user.id)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        if db_user is None:
            raise ValueError(f"User with id {user.id} not found")
            
        db_user.email = user.email
        db_user.username = user.username
        db_user.firstname = user.firstname
        db_user.lastname = user.lastname
        db_user.role = user.role
        db_user.level = user.level
        db_user.last_login = user.last_login
        db_user.is_active = user.is_active
        
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        
        return self._map_to_domain(db_user)

    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        if db_user is None:
            return False
            
        db_user.hashed_password = hashed_password
        await self.db_session.commit()
        
        return True

    async def update_last_login(self, user_id: str) -> bool:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        if db_user is None:
            return False
            
        db_user.last_login = datetime.now(timezone.utc)
        await self.db_session.commit()
        
        return True

    async def delete(self, id: str) -> bool:
        query = select(UserModel).where(UserModel.id == id)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return False
            
        await self.db_session.delete(db_user)
        await self.db_session.commit()
        return True

    def _map_to_domain(self, db_user: UserModel) -> User:
        """Convertit un modèle SQLAlchemy en modèle de domaine"""
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            firstname=db_user.firstname,
            lastname=db_user.lastname,
            role=db_user.role,
            level=db_user.level,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            is_active=db_user.is_active
        )
