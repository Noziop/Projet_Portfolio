# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserResponse

class LoginRequest(BaseModel):
    """Schema pour la requête de login"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Schema pour la réponse de login"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshToken(BaseModel):
    """Schema pour le refresh token"""
    refresh_token: str

class PasswordReset(BaseModel):
    """Schema pour la réinitialisation de mot de passe"""
    email: EmailStr

class PasswordChange(BaseModel):
    """Schema pour le changement de mot de passe"""
    old_password: str
    new_password: str
