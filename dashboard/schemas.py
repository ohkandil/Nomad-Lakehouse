from __future__ import annotations

from pydantic import BaseModel, EmailStr


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
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
