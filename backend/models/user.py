# /backend/models/user.py

from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import EmailStr
import uuid

from models.base_model import BaseModel


# ------------------------------
# Shared API fields
# ------------------------------
class UserBase(SQLModel):
    full_name: str
    email: EmailStr


# ------------------------------
# Input model for registration / creation
# ------------------------------
class UserInput(SQLModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=40)


# Optional: separate alias for explicit API intent
UserCreate = UserInput
UserRegister = UserInput


# ------------------------------
# Input model for updates
# ------------------------------
class UserUpdate(SQLModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UpdatePassword(SQLModel):
    current_password: str = Field(..., min_length=8, max_length=40)
    new_password: str = Field(..., min_length=8, max_length=40)


# ------------------------------
# Database model
# ------------------------------
class User(BaseModel, table=True):
    __tablename__ = "users"

    full_name: str = Field(..., index=True)
    email: EmailStr = Field(..., unique=True, index=True)
    hashed_password: str = Field(default=None)
    is_active: bool = True
    is_superuser: bool = False
    email_verified: bool = True


# ------------------------------
# Response model
# ------------------------------
class UserPublic(UserBase):
    id: uuid.UUID
    is_active: bool
    is_admin: bool
    email_verified: bool
