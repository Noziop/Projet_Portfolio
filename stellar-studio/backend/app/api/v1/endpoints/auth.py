# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import json

from app.api.deps import get_db, get_current_user, get_session_service
from app.core.config import settings
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import PasswordChange
from app.services.auth.service import AuthService
from app.services.auth.session import SessionService
from app.services.user.service import UserService

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)  # Utilise la fonction
):
    """Création d'un nouveau compte utilisateur"""
    auth_service = AuthService(db, session_service)
    try:
        user = await auth_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """Authentification et génération du token JWT"""
    auth_service = AuthService(db, session_service)
    user, token = await auth_service.authenticate_user(
        form_data.username,
        form_data.password
    )
    if not user or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects"
        )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Récupération des informations de l'utilisateur connecté"""
    return current_user

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """Déconnexion de l'utilisateur"""
    auth_service = AuthService(db, session_service)
    await auth_service.logout(str(current_user.id))
    return {"detail": "À bientôt dans les étoiles ! ✨"}


@router.post("/password/change")
async def change_password(
    data: PasswordChange,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """Changement de mot de passe"""
    auth_service = AuthService(db, session_service)
    user_service = UserService(db, auth_service)  # Utilisation du bon service
    try:
        await user_service.update_password(  # Appel de la bonne méthode
            current_user.id,
            data.old_password,
            data.new_password
        )
        # Déconnexion des autres sessions
        await session_service.clear_user_sessions(current_user.id)
        return {"detail": "Mot de passe mis à jour avec succès"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# @router.get("/debug-redis")
# async def debug_redis(session_service: SessionService = Depends(get_session_service)):
#     """Endpoint temporaire pour déboguer Redis"""
#     try:
#         # Tester la connexion
#         ping_result = await session_service.redis.ping()
        
#         # Lister toutes les clés de session
#         keys = []
#         async for key in session_service.redis.scan_iter(f"{session_service.prefix}*"):
#             keys.append(key.decode())
        
#         # Récupérer les valeurs pour chaque clé
#         values = {}
#         for key in keys:
#             value = await session_service.redis.get(key)
#             if value:
#                 values[key] = json.loads(value)
            
#         return {
#             "ping": ping_result,
#             "keys": keys,
#             "values": values
#         }
#     except Exception as e:
#         return {"error": str(e), "type": type(e).__name__}
