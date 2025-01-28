from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from .base_repository import BaseRepository
from ..repositories.models.user import User as UserModel, UserLevel as DBUserLevel, UserRole as DBUserRole
from app.domain.models.user import User, UserLevel, UserRole

class UserRepository(BaseRepository[User]):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    async def get_by_id(self, id: str) -> Optional[User]:
        query = select(UserModel).where(UserModel.id == id)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        if db_user is None:
            return None
            
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            firstname=db_user.firstname,
            lastname=db_user.lastname,
            role=UserRole[db_user.role.name],
            level=UserLevel[db_user.level.name],
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            is_active=db_user.is_active
        )

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(UserModel).where(UserModel.email == email)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        if db_user is None:
            return None
            
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            firstname=db_user.firstname,
            lastname=db_user.lastname,
            role=UserRole[db_user.role.name],
            level=UserLevel[db_user.level.name],
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            is_active=db_user.is_active
        )

    async def create(self, user: User, hashed_password: str) -> User:
        db_user = UserModel(
            id=str(uuid.uuid4()),
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,  # Géré séparément du modèle de domaine
            firstname=user.firstname,
            lastname=user.lastname,
            role=DBUserRole[user.role.name],
            level=DBUserLevel[user.level.name],
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
        
        self.db_session.add(db_user)
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            firstname=db_user.firstname,
            lastname=db_user.lastname,
            role=UserRole[db_user.role.name],
            level=UserLevel[db_user.level.name],
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            is_active=db_user.is_active
        )

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
        db_user.role = DBUserRole[user.role.name]
        db_user.level = DBUserLevel[user.level.name]
        db_user.last_login = user.last_login
        db_user.is_active = user.is_active
        
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        
        return user

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
            
        from datetime import datetime
        db_user.last_login = datetime.utcnow()
        await self.db_session.commit()
        
        return True

    async def delete(self, id: str) -> bool:
        query = select(UserModel).where(UserModel.id == id)
        result = await self.db_session.execute(query)
        db_user = result.scalar_one_or_none()
        
        if db_user is None:
            return False
            
        await self.db_session.delete(db_user)
        await self.db_session.commit()
        
        return True
