# app/services/user/service.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.models.user import User
from app.domain.value_objects.user_types import UserLevel, UserRole
from app.services.auth.service import AuthService

# Métriques Prometheus
user_operations = Counter(
    'user_operations_total',
    'Total number of user operations',
    ['operation']  # create, update, deactivate, reactivate
)

user_operation_duration = Histogram(
    'user_operation_duration_seconds',
    'Time spent processing user operations',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5)
)

class UserService:
    def __init__(self, session: AsyncSession, auth_service: AuthService):
        self.user_repository = UserRepository(session)
        self.auth_service = auth_service

    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        level: UserLevel = UserLevel.BEGINNER,
        role: UserRole = UserRole.USER,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None
    ) -> User:
        """Crée un nouvel utilisateur"""
        with user_operation_duration.time():
            if await self.user_repository.get_by_email(email):
                raise ValueError("Email déjà utilisé")
            if await self.user_repository.get_by_username(username):
                raise ValueError("Nom d'utilisateur déjà utilisé")

            user = User(
                email=email,
                username=username,
                hashed_password=self.auth_service.get_password_hash(password),
                level=level,
                role=role,
                firstname=firstname,
                lastname=lastname
            )
            created_user = await self.user_repository.create(user)
            user_operations.labels(operation='create').inc()
            return created_user

    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        return await self.user_repository.get(user_id)

    async def update_user(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        username: Optional[str] = None,
        level: Optional[UserLevel] = None,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None
    ) -> Optional[User]:
        """Met à jour les informations d'un utilisateur"""
        with user_operation_duration.time():
            user = await self.user_repository.get(user_id)
            if not user:
                return None

            if email and email != user.email:
                if await self.user_repository.get_by_email(email):
                    raise ValueError("Email déjà utilisé")
                user.email = email

            if username and username != user.username:
                if await self.user_repository.get_by_username(username):
                    raise ValueError("Nom d'utilisateur déjà utilisé")
                user.username = username

            if level:
                user.level = level
            if firstname:
                user.firstname = firstname
            if lastname:
                user.lastname = lastname

            updated_user = await self.user_repository.update(user)
            user_operations.labels(operation='update').inc()
            return updated_user

    async def update_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> bool:
        """Met à jour le mot de passe d'un utilisateur"""
        user = await self.user_repository.get(user_id)
        if not user:
            return False

        if not self.auth_service.verify_password(current_password, user.hashed_password):
            raise ValueError("Mot de passe actuel incorrect")

        user.hashed_password = self.auth_service.get_password_hash(new_password)
        await self.user_repository.update(user)
        return True

    async def deactivate_user(self, user_id: UUID) -> bool:
        """Désactive un compte utilisateur"""
        with user_operation_duration.time():
            user = await self.user_repository.get(user_id)
            if not user:
                return False

            user.is_active = False
            await self.user_repository.update(user)
            user_operations.labels(operation='deactivate').inc()
            return True

    async def reactivate_user(self, user_id: UUID) -> bool:
        """Réactive un compte utilisateur"""
        with user_operation_duration.time():
            user = await self.user_repository.get(user_id)
            if not user:
                return False

            user.is_active = True
            await self.user_repository.update(user)
            user_operations.labels(operation='reactivate').inc()
            return True
