# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class UserBase(BaseModel):
    email: EmailStr
    username: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    level: UserLevel = UserLevel.BEGINNER

class UserCreate(UserBase):
    password: str  # Required for local auth

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str  # Changed from int to str for UUID
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
