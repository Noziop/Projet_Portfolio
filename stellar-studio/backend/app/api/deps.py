# app/api/deps.py
from typing import AsyncGenerator, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.domain.models.user import User, UserRole
from app.infrastructure.repositories.models.user import User as UserModel
from app.services.auth.session import SessionService
from redis.asyncio import Redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def convert_to_domain_user(db_user: UserModel) -> User:
    return User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        firstname=db_user.firstname,
        lastname=db_user.lastname,
        role=UserRole[db_user.role.name],
        level=db_user.level,
        created_at=db_user.created_at,
        last_login=db_user.last_login,
        is_active=db_user.is_active,
        hashed_password=db_user.hashed_password
    )

async def get_session_service() -> SessionService:
    """Dépendance pour obtenir une instance de SessionService"""
    from app.core.redis import redis_client
    
    print(f"DEBUG - Configuration Redis: host={settings.REDIS_HOST}, port={settings.REDIS_PORT}, db={settings.REDIS_SESSION_DB}")
    
    # Créer une nouvelle instance Redis à chaque fois pour être sûr
    async_redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_SESSION_DB
    )
    
    # Test de connexion
    try:
        ping_result = await async_redis.ping()
    except Exception as e:
        print(f"DEBUG - Erreur connexion Redis: {str(e)}")
    
    return SessionService(async_redis)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    session_service: SessionService = Depends(get_session_service)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Décode le token JWT
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    # Vérification session Redis avec l'ID utilisateur
    session = await session_service.get_session(user_id)
    if not session:
        raise credentials_exception

    # Utilisation de select() avec async
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()
    
    if db_user is None:
        raise credentials_exception
    
    return convert_to_domain_user(db_user)

def require_role(*roles: UserRole):
    """
    Décorateur pour vérifier les rôles utilisateur.
    Utilise get_current_user en interne.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission insuffisante pour cette opération"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
