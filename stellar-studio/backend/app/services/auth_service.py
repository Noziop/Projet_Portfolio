# app/services/auth_service.py
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.session import SessionManager
from app.schemas.user import UserCreate, User, Token
from app.db.session import SessionLocal
from app.models.user import User as UserModel, UserLevel

class AuthService:
    def __init__(self):
        self.session_manager = SessionManager()

    async def register_new_user(self, user_data: UserCreate) -> User:
        with SessionLocal() as db:
            if self._get_user_by_email(db, user_data.email):
                raise ValueError("Email already registered")
            
            if self._get_user_by_username(db, user_data.username):
                raise ValueError("Username already taken")
            
            return self._create_user(db, user_data)

    async def authenticate(self, email: str, password: str) -> Token:
        with SessionLocal() as db:
            user = self._get_user_by_email(db, email)
            if not user or not verify_password(password, user.hashed_password):
                raise ValueError("Invalid email or password")
            
            if not user.is_active:
                raise ValueError("User account is disabled")

            return self._create_session(db, user)

    async def logout(self, user_id: int) -> bool:
        """Révoque la session de l'utilisateur"""
        return self.session_manager.revoke_session(user_id)

    async def validate_token(self, user_id: int) -> bool:
        """Vérifie si la session est toujours valide"""
        session = self.session_manager.get_session(user_id)
        return session is not None

    def _get_user_by_email(self, db: Session, email: str) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.email == email).first()

    def _get_user_by_username(self, db: Session, username: str) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.username == username).first()

    def _create_user(self, db: Session, user_data: UserCreate) -> User:
        db_user = UserModel(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            level=user_data.level or UserLevel.BEGINNER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return User.from_orm(db_user)

    def _create_session(self, db: Session, user: UserModel) -> Token:
        # Mise à jour du last_login
        user.last_login = datetime.utcnow()
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

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change le mot de passe de l'utilisateur"""
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user or not verify_password(old_password, user.hashed_password):
                raise ValueError("Invalid current password")
            
            user.hashed_password = get_password_hash(new_password)
            db.commit()
            
            # Révoquer toutes les sessions existantes
            self.session_manager.revoke_session(user_id)
            return True

    async def deactivate_account(self, user_id: int) -> bool:
        """Désactive le compte utilisateur"""
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            user.is_active = False
            db.commit()
            
            # Révoquer la session
            self.session_manager.revoke_session(user_id)
            return True
