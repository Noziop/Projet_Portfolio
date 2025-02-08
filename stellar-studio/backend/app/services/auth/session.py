# app/services/auth/session.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.core.session import SessionManager
from app.schemas.user import Token
from app.infrastructure.repositories.models.user import User as UserModel

class SessionHandler:
    def __init__(self):
        self.session_manager = SessionManager()

    def create_session(self, db: Session, user: UserModel) -> Token:
        # Mise à jour du last_login
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        # Création du token
        access_token = create_access_token(subject=user.id)
        
        # Stockage de la session dans Redis
        session_data = {
            "user_id": user.id,
            "email": user.email,
            "level": user.level.value,
            "last_login": user.last_login.isoformat()
        }
        self.session_manager.create_session(user.id, session_data)

        return Token(
            access_token=access_token,
            token_type="bearer"
        )

    def revoke_session(self, user_id: str) -> bool:
        return self.session_manager.revoke_session(user_id)

    def validate_session(self, user_id: str) -> bool:
        session = self.session_manager.get_session(user_id)
        return session is not None
