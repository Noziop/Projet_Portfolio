#app/domain/value_objects/user_types.py
from enum import Enum

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
