from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class UserRole(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"

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
    role: UserRole  # Ajout du champ role
    level: UserLevel
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
