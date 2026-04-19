"""Pydantic schemas for authentication."""
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    STAFF = "staff"
    DEPARTMENT_ADMIN = "department_admin"
    SUPER_ADMIN = "super_admin"

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.USER
    department_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    department_name: Optional[str]
