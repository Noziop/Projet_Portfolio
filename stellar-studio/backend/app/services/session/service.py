# services/session/service.py
from datetime import datetime, timezone
from typing import Optional
from app.core.security import create_access_token
from app.core.session import SessionManager
from app.domain.models.user import User
from app.schemas.auth import Token

class SessionService:
    def __init__(self):
        self.session_manager = SessionManager()

    async def create_session(self, user: User) -> Token:
        """Crée une nouvelle session pour l'utilisateur"""
        access_token = create_access_token(subject=user.id)
        
        session_data = {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "level": user.level.value,
            "last_login": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if not await self.session_manager.create_session(user.id, session_data):
            raise ValueError("Failed to create session")

        return Token(
            access_token=access_token,
            token_type="bearer"
        )

    async def get_session(self, user_id: str) -> Optional[dict]:
        """Récupère les données de session d'un utilisateur"""
        return await self.session_manager.get_session(user_id)

    async def revoke_session(self, user_id: str) -> bool:
        """Révoque la session d'un utilisateur"""
        if not await self.session_manager.revoke_session(user_id):
            raise ValueError("Failed to revoke session")
        return True

    async def validate_session(self, user_id: str) -> bool:
        """Vérifie si la session est valide"""
        session = await self.session_manager.get_session(user_id)
        if not session:
            return False
            
        # Vérification supplémentaire possible ici
        # Par exemple, vérifier si la session n'est pas trop vieille
        created_at = datetime.fromisoformat(session["created_at"])
        if (datetime.now(timezone.utc) - created_at).days > 7:
            await self.revoke_session(user_id)
            return False
            
        return True

    async def refresh_session(self, user_id: str) -> bool:
        """Rafraîchit les données de session"""
        session = await self.get_session(user_id)
        if not session:
            return False
            
        session["last_activity"] = datetime.now(timezone.utc).isoformat()
        return await self.session_manager.update_session(user_id, session)
