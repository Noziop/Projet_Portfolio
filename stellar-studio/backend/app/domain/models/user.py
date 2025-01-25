# app/domain/models/user.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class UserLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class User:
    id: str
    email: str
    username: str
    firstname: Optional[str]
    lastname: Optional[str]
    level: UserLevel
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
