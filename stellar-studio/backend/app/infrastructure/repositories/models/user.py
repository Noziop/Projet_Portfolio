from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
from app.domain.value_objects.user_types import UserLevel, UserRole

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    firstname = Column(String(100), nullable=True)
    lastname = Column(String(100), nullable=True)
    level = Column(Enum(UserLevel), nullable=False, default=UserLevel.get_default)  
    role = Column(Enum(UserRole), nullable=False, default=UserRole.get_default)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
