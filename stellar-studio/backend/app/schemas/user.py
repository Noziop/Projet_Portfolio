from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Optional
from datetime import datetime
from enum import Enum

class UserLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"

class UserBase(BaseModel):
    email: EmailStr
    username: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    level: UserLevel = UserLevel.BEGINNER
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Mot de passe de l'utilisateur"
    )
    
    @field_validator('password')
    def password_complexity(cls, v):
        """Vérifie la complexité du mot de passe"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not re.search(r'[0-9]', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère spécial')
        return v

    @field_validator('username')
    def username_alphanumeric(cls, v):
        """Vérifie que le username est alphanumérique"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Le username ne peut contenir que des lettres, chiffres, tirets et underscores')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str  # Changed from int to str for UUID
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

class UserInDB(User):
    hashed_password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    level: Optional[UserLevel] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
