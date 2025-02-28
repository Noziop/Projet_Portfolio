# app/services/auth/service.py
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram
from app.core.config import settings
from app.schemas.user import UserCreate
from app.infrastructure.repositories.user_repository import UserRepository
from app.services.auth.session import SessionService
from app.infrastructure.repositories.models.user import User

# Métriques Prometheus
auth_attempts = Counter(
    'auth_attempts_total',
    'Total number of authentication attempts',
    ['status']  # success, failed
)

auth_duration = Histogram(
    'auth_duration_seconds',
    'Time spent processing authentication requests',
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

token_operations = Counter(
    'token_operations_total',
    'Total number of token operations',
    ['operation']  # create, verify, refresh
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, session: AsyncSession, session_service: SessionService):
        self.user_repository = UserRepository(session)
        self.session_service = session_service

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie si le mot de passe en clair correspond au hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Génère un hash pour un mot de passe"""
        return pwd_context.hash(password)

    def create_access_token(self, user_id: UUID) -> str:
        """Crée un JWT token pour l'utilisateur"""
        token_operations.labels(operation='create').inc()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "exp": expire,
            "sub": str(user_id)
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def authenticate_user(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """Authentifie un utilisateur et retourne l'utilisateur et le token si succès"""
        with auth_duration.time():
            user = await self.user_repository.get_by_email(email)
            
            if not user or not self.verify_password(password, user.hashed_password):
                auth_attempts.labels(status='failed').inc()
                return None, None

            # Mise à jour du last_login
            user.last_login = datetime.utcnow()
            await self.user_repository.update(user)

            # Création de la session avec l'ID utilisateur comme clé
            session_data = {
                "email": user.email,
                "role": user.role.value,
                "level": user.level.value,
                "last_login": datetime.utcnow().isoformat()
            }
            
            # Crée la session et vérifie le succès
            session_created = await self.session_service.create_session(user.id, session_data)
            if not session_created:
                auth_attempts.labels(status='failed').inc()
                return None, None
            
            # Crée le token avec l'ID utilisateur uniquement
            access_token = self.create_access_token(user.id)

            auth_attempts.labels(status='success').inc()
            return user, access_token

    async def get_current_user(self, token: str) -> Optional[User]:
        """Récupère l'utilisateur à partir du token JWT"""
        try:
            token_operations.labels(operation='verify').inc()
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id = UUID(payload["sub"])
            
            # Vérifie si la session existe
            session = await self.session_service.get_session(user_id)
            if not session:
                return None
                
            return await self.user_repository.get(user_id)
        except (jwt.JWTError, ValueError) as e:
            print(f"DEBUG - Erreur JWT: {str(e)}")
            return None

    async def logout(self, user_id: UUID) -> bool:
        """Déconnecte un utilisateur en supprimant sa session"""
        return await self.session_service.delete_session(user_id)

    async def refresh_token(self, user_id: UUID) -> str:
        """Rafraîchit le token d'un utilisateur"""
        token_operations.labels(operation='refresh').inc()
        
        # Récupère les données de la session
        session = await self.session_service.get_session(user_id)
        if not session:
            raise ValueError("Invalid session")
            
        # Met à jour la session
        session["refreshed_at"] = datetime.utcnow().isoformat()
        await self.session_service.update_session(user_id, session)
        
        # Crée un nouveau token
        return self.create_access_token(user_id)

    async def create_user(self, user_data: UserCreate) -> User:
        """Crée un nouvel utilisateur"""
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        user_dict = user_data.model_dump(exclude={"password"})
        
        user = User(**user_dict)
        user.hashed_password = self.get_password_hash(user_data.password)
        
        return await self.user_repository.create(user)