#app/domain/value_objects/user_types.py
from enum import Enum

class UserLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    USER = "USER"
