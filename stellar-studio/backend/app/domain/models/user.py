from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..value_objects.user_types import UserLevel, UserRole

@dataclass
class User:
    id: str
    email: str
    username: str
    firstname: Optional[str]
    lastname: Optional[str]
    role: UserRole
    level: UserLevel
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
