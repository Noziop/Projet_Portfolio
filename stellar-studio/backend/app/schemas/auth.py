# app/schemas/auth.py
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: int = None
    exp: int = None

class Login(BaseModel):
    email: EmailStr
    password: str
