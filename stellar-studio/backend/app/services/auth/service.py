# services/auth/service.py
from datetime import datetime, timezone
from typing import Optional
from app.core.security import verify_password, get_password_hash
from app.services.user.service import UserService
from app.services.session.service import SessionService
from app.schemas.user import UserCreate, User
from app.schemas.auth import Token
from app.domain.value_objects.user_types import UserRole

class AuthService:
    def __init__(self, user_service: UserService, session_service: SessionService):
        self.user_service = user_service
        self.session_service = session_service

    async def register(self, user_data: UserCreate) -> User:
        """Enregistre un nouvel utilisateur"""
        # Vérification du mot de passe
        if len(user_data.password) < 12:
            raise ValueError("Password must be at least 12 characters long")

        hashed_password = get_password_hash(user_data.password)
        return await self.user_service.create_user(user_data, hashed_password)

    async def authenticate(self, email: str, password: str) -> Token:
        """Authentifie un utilisateur et crée une session"""
        user = await self.user_service.get_by_email(email.lower())
        if not user:
            # Message volontairement vague pour la sécurité
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            # Log tentative échouée ici
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("Account is disabled")

        # Mise à jour du last_login
        user.last_login = datetime.now(timezone.utc)
        await self.user_service.update_user(user.id, {"last_login": user.last_login})

        # Création de la session
        return await self.session_service.create_session(user)

    async def logout(self, user_id: str) -> bool:
        """Déconnecte un utilisateur en révoquant sa session"""
        return await self.session_service.revoke_session(user_id)

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change le mot de passe d'un utilisateur"""
        user = await self.user_service.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        if not verify_password(old_password, user.hashed_password):
            # Log tentative échouée ici
            raise ValueError("Current password is incorrect")

        if len(new_password) < 12:
            raise ValueError("New password must be at least 12 characters long")

        if old_password == new_password:
            raise ValueError("New password must be different from current password")

        hashed_password = get_password_hash(new_password)
        success = await self.user_service.update_password(user_id, hashed_password)
        
        if success:
            # Révoque toutes les sessions existantes
            await self.session_service.revoke_session(user_id)
        
        return success

    async def reset_password_request(self, email: str) -> bool:
        """Initie une demande de réinitialisation de mot de passe"""
        user = await self.user_service.get_by_email(email.lower())
        if not user or not user.is_active:
            # Toujours retourner True même si l'utilisateur n'existe pas (sécurité)
            return True

        # TODO: Implémenter l'envoi d'email avec token de réinitialisation
        return True

    async def validate_session(self, user_id: str) -> bool:
        """Vérifie si la session de l'utilisateur est valide"""
        return await self.session_service.validate_session(user_id)

    async def check_permissions(self, user_id: str, required_role: UserRole) -> bool:
        """Vérifie si l'utilisateur a les permissions requises"""
        user = await self.user_service.get_user(user_id)
        if not user or not user.is_active:
            return False

        # Admin a tous les droits
        if user.role == UserRole.ADMIN:
            return True

        return user.role == required_role
