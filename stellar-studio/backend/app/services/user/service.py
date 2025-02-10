# services/user/service.py
from typing import Optional, List
from datetime import datetime, timezone
from app.domain.models.user import User
from app.domain.value_objects.user_types import UserRole, UserLevel
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user(self, user_id: str) -> Optional[User]:
        return await self.user_repository.get_by_id(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.user_repository.get_by_email(email)

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.user_repository.get_by_username(username)

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        # Vérifications métier
        if await self.get_by_email(user_data.email.lower()):
            raise ValueError("Email already registered")

        if await self.get_by_username(user_data.username):
            raise ValueError("Username already taken")

        if user_data.username.lower() in ["admin", "root", "system", "superuser"]:
            raise ValueError("This username is reserved")

        user = User(
            id="",  # Sera généré par le repository
            email=user_data.email.lower(),
            username=user_data.username,
            firstname=user_data.firstname.strip() if user_data.firstname else None,
            lastname=user_data.lastname.strip() if user_data.lastname else None,
            role=user_data.role or UserRole.get_default(),
            level=user_data.level or UserLevel.get_default(),
            created_at=datetime.now(timezone.utc),
            last_login=None,
            is_active=True
        )
        
        return await self.user_repository.create(user, hashed_password)

    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        # Vérification email unique si changé
        if user_data.email and user_data.email.lower() != user.email:
            if await self.get_by_email(user_data.email.lower()):
                raise ValueError("Email already registered")

        # Vérification username unique si changé
        if user_data.username and user_data.username != user.username:
            if await self.get_by_username(user_data.username):
                raise ValueError("Username already taken")
            if user_data.username.lower() in ["admin", "root", "system", "superuser"]:
                raise ValueError("This username is reserved")

        # Mise à jour des attributs
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Nettoyage des données
        if "email" in update_data:
            update_data["email"] = update_data["email"].lower()
        if "firstname" in update_data:
            update_data["firstname"] = update_data["firstname"].strip() if update_data["firstname"] else None
        if "lastname" in update_data:
            update_data["lastname"] = update_data["lastname"].strip() if update_data["lastname"] else None

        # Vérification des permissions pour changer le rôle
        if "role" in update_data and update_data["role"] != user.role:
            if user.role == UserRole.ADMIN:
                raise ValueError("Cannot change admin role")

        for key, value in update_data.items():
            setattr(user, key, value)

        return await self.user_repository.update(user)

    async def delete_user(self, user_id: str, current_user_role: UserRole) -> bool:
        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        # Vérifications métier avant suppression
        if user.role == UserRole.ADMIN:
            if current_user_role != UserRole.ADMIN:
                raise ValueError("Only admin can delete admin users")
            
            # Vérifier s'il reste d'autres admins
            admins = await self.list_users(role=UserRole.ADMIN)
            if len(admins) <= 1:
                raise ValueError("Cannot delete last admin user")

        return await self.user_repository.delete(user_id)

    async def list_users(self, role: Optional[UserRole] = None) -> List[User]:
        """Liste les utilisateurs avec filtre optionnel par rôle"""
        users = await self.user_repository.list_all()
        if role:
            return [user for user in users if user.role == role]
        return users
