# app/services/auth/__init__.py
from app.services.user.service import UserService
from app.services.session.service import SessionService
from app.infrastructure.repositories.user_repository import UserRepository
from .service import AuthService
from app.db.session import AsyncSessionLocal
from typing import AsyncGenerator
from fastapi import Depends

# Création d'une fonction async pour obtenir le service
async def get_auth_service() -> AsyncGenerator[AuthService, None]:
    async with AsyncSessionLocal() as db:
        user_repository = UserRepository(db)
        user_service = UserService(user_repository)
        session_service = SessionService()
        auth_service = AuthService(user_service, session_service)
        try:
            yield auth_service
        finally:
            await db.close()

__all__ = ['get_auth_service']
