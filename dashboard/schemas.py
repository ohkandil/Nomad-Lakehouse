from __future__ import annotations

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Schema for reading user data."""
    id: str
    email: str
    is_active: bool
    is_superuser: bool


class UserUpdate(BaseModel):
    """Schema for updating user data."""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
