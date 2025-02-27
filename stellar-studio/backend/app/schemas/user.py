# app/schemas/user.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator
from app.domain.value_objects.user_types import UserLevel, UserRole

class UserBase(BaseModel):
    """Attributs communs pour tous les schemas User"""
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    username: str = Field(
        ..., 
        description="Nom d'utilisateur",
        min_length=3,
        max_length=100
    )
    firstname: Optional[str] = Field(None, max_length=100)
    lastname: Optional[str] = Field(None, max_length=100)
    level: UserLevel = Field(
        default=UserLevel.BEGINNER,
        description="Niveau d'expertise"
    )
    role: UserRole = Field(
        default=UserRole.USER,
        description="Rôle de l'utilisateur"
    )
    is_active: bool = Field(default=True, description="Compte actif ou non")

class UserCreate(UserBase):
    """Schema pour la création d'un utilisateur"""
    password: str = Field(
        ..., 
        min_length=8,
        description="Mot de passe en clair"
    )

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.islower() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v

class UserUpdate(BaseModel):
    """Schema pour la mise à jour d'un utilisateur"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    password: Optional[str] = None
    level: Optional[UserLevel] = None
    is_active: Optional[bool] = None

    @validator('username')
    def validate_username(cls, v):
        if v is not None and (len(v) < 3 or len(v) > 100):
            raise ValueError("Le nom d'utilisateur doit faire entre 3 et 100 caractères")
        return v

class UserInDB(UserBase):
    """Schema pour un utilisateur en DB"""
    id: UUID
    hashed_password: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserStats(BaseModel):
    """Statistiques utilisateur"""
    total_jobs: int = Field(..., description="Nombre total de traitements")
    successful_jobs: int = Field(..., description="Traitements réussis")
    favorite_presets: List[str] = Field(..., description="Presets les plus utilisés")
    storage_usage: float = Field(..., description="Espace utilisé (Go)")
    last_activity: Optional[datetime] = Field(None, description="Dernière activité")

class UserResponse(UserBase):
    """Schema pour la réponse API"""
    id: UUID
    created_at: datetime
    last_login: Optional[datetime]
    stats: Optional[UserStats] = None
    display_name: Optional[str] = Field(
        None,
        description="Nom complet formaté"
    )

    @validator('display_name', always=True)
    def set_display_name(cls, v, values):
        if not v:
            firstname = values.get('firstname', '')
            lastname = values.get('lastname', '')
            if firstname and lastname:
                return f"{firstname} {lastname}"
            return values.get('username', '')
        return v

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """Schema pour la liste paginée des utilisateurs"""
    items: List[UserResponse]
    total: int
    page: int
    size: int

class Token(BaseModel):
    """Schema pour le token d'authentification"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
