from pydantic import BaseModel, EmailStr
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
    password: str  # Required for local auth

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
