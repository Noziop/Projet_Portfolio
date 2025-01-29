# app/infrastructure/repositories/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum
import uuid
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base

class UserLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class UserRole(enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    firstname = Column(String(100), nullable=True)
    lastname = Column(String(100), nullable=True)
    level = Column(Enum(UserLevel), nullable=False, default=UserLevel.BEGINNER)  
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
