# app/domain/models/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.domain.value_objects.user_types import UserLevel, UserRole

@dataclass
class User:
    id: UUID
    email: str
    username: str
    hashed_password: str
    level: UserLevel
    role: UserRole
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True
