from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class UserLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    @classmethod
    def get_default(cls) -> "UserLevel":
        """Retourne la valeur par défaut du niveau utilisateur"""
        return cls.BEGINNER

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"

    @classmethod
    def get_default(cls) -> "UserRole":
        """Retourne la valeur par défaut du rôle utilisateur"""
        return cls.USER


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
