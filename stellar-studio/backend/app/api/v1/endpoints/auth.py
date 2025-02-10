# api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, User, PasswordChange
from app.schemas.auth import Token
from app.api.deps import get_current_user
from app.services.auth import get_auth_service
from app.services.auth.service import AuthService

router = APIRouter(tags=["Authentication"])

@router.post("/register", 
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    description="Register a new user")
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Enregistre un nouvel utilisateur"""
    try:
        return await auth_service.register(user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", 
    response_model=Token,
    description="Authenticate user and create session")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authentifie un utilisateur"""
    try:
        return await auth_service.authenticate(
            email=form_data.username,
            password=form_data.password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Logout current user")
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Déconnecte l'utilisateur courant"""
    await auth_service.logout(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/password", 
    status_code=status.HTTP_204_NO_CONTENT,
    description="Change user password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change le mot de passe de l'utilisateur"""
    try:
        await auth_service.change_password(
            current_user.id,
            password_data.old_password,
            password_data.new_password
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", 
    response_model=User,
    description="Get current user information")
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """Retourne les informations de l'utilisateur courant"""
    return current_user
