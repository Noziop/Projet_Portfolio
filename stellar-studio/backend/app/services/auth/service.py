# app/services/auth/service.py
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.user import UserCreate, User, Token, UserUpdate
from app.infrastructure.repositories.models.user import User as UserModel
from .password import PasswordManager
from .session import SessionHandler

class AuthService:
    def __init__(self):
        self.session_handler = SessionHandler()
        self.password_manager = PasswordManager(self.session_handler)

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
            if not user or not self.password_manager.verify_password(password, user.hashed_password):
                raise ValueError("Invalid email or password")
            
            if not user.is_active:
                raise ValueError("User account is disabled")

            return self.session_handler.create_session(db, user)

    async def logout(self, user_id: str) -> bool:
        return self.session_handler.revoke_session(user_id)

    async def validate_token(self, user_id: str) -> bool:
        return self.session_handler.validate_session(user_id)

    def _get_user_by_email(self, db: Session, email: str) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.email == email).first()

    def _get_user_by_username(self, db: Session, username: str) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.username == username).first()

    def _create_user(self, db: Session, user_data: UserCreate) -> User:
        db_user = UserModel(
            email=user_data.email,
            username=user_data.username,
            hashed_password=self.password_manager.hash_password(user_data.password),
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            level=user_data.level,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return User.from_orm(db_user)

    async def deactivate_account(self, user_id: str) -> bool:
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            user.is_active = False
            db.commit()
            
            await self.session_handler.revoke_session(user_id)
            return True

    async def list_all_users(self) -> List[User]:
        """Liste tous les utilisateurs (admin only)"""
        with SessionLocal() as db:
            users = db.query(UserModel).all()
            return [User.from_orm(user) for user in users]

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                return None
            return User.from_orm(user)

    async def update_user(self, user_id: str, user_update: UserUpdate) -> User:
        """Met à jour les informations d'un utilisateur"""
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            # Vérification de l'unicité de l'email et du username si modifiés
            if user_update.email and user_update.email != user.email:
                if self._get_user_by_email(db, user_update.email):
                    raise ValueError("Email already registered")
                
            if user_update.username and user_update.username != user.username:
                if self._get_user_by_username(db, user_update.username):
                    raise ValueError("Username already taken")

            # Mise à jour des champs
            update_data = user_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(user, key, value)

            db.commit()
            db.refresh(user)
            return User.from_orm(user)

    async def delete_user(self, user_id: str) -> bool:
        """Supprime un utilisateur"""
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            # Révocation de la session avant suppression
            await self.session_handler.revoke_session(user_id)
            
            db.delete(user)
            db.commit()
            return True
