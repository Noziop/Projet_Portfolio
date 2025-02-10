# schemas/user.py
from pydantic import BaseModel, EmailStr, Field, constr
from typing import Optional
from datetime import datetime
from app.domain.value_objects.user_types import UserRole, UserLevel

class UserBase(BaseModel):
    email: EmailStr
    username: constr(min_length=8, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$") = Field(
        ...,
        description="Username: 8-20 caractères, lettres, chiffres, - et _"
    )
    firstname: Optional[constr(min_length=2, max_length=30, pattern=r"^[a-zA-Z\s-]+$")] = Field(
        None,
        description="Prénom: 2-30 caractères, lettres et -"
    )
    lastname: Optional[constr(min_length=2, max_length=30, pattern=r"^[a-zA-Z\s-]+$")] = Field(
        None,
        description="Nom: 2-30 caractères, lettres et -"
    )
    level: UserLevel = Field(default_factory=UserLevel.get_default)
    role: UserRole = Field(default_factory=UserRole.get_default)

class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=12,
        description="Mot de passe: min 12 caractères"
    )

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[constr(min_length=8, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")] = None
    firstname: Optional[constr(min_length=2, max_length=30, pattern=r"^[a-zA-Z\s-]+$")] = None
    lastname: Optional[constr(min_length=2, max_length=30, pattern=r"^[a-zA-Z\s-]+$")] = None
    level: Optional[UserLevel] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True

class User(UserInDB):
    """Schéma de réponse API (sans le hashed_password)"""
    pass

class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=12)
    new_password: str = Field(
        ...,
        min_length=12,
        description="Nouveau mot de passe: min 12 caractères"
    )
