# app/services/auth/password.py
from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash
from app.infrastructure.repositories.models.user import User as UserModel
from app.db.session import SessionLocal

class PasswordManager:
    def __init__(self, session_handler=None):
        self.session_handler = session_handler

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        return get_password_hash(password)

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user or not self.verify_password(old_password, user.hashed_password):
                raise ValueError("Invalid current password")
            
            user.hashed_password = self.hash_password(new_password)
            db.commit()
            
            if self.session_handler:
                await self.session_handler.revoke_session(user_id)
            return True
