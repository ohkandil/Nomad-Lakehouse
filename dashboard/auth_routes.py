from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dashboard.auth_config import User
from dashboard.database import get_db
from dashboard.schemas import UserRead
from dashboard.security import get_password_hash

router = APIRouter()


# Create initial admin user
@router.get("/init-admin", status_code=status.HTTP_201_CREATED)
def create_admin_user(db: Session = Depends(get_db)) -> UserRead:
    """Create admin user if not exists."""
    existing_user = db.query(User).filter(User.email == "admin@nomad.lakehouse").first()
    if existing_user:
        return UserRead(
            id=str(existing_user.id),
            email=existing_user.email,
            is_active=existing_user.is_active,
            is_superuser=existing_user.is_superuser
        )

    admin = User(
        email="admin@nomad.lakehouse",
        hashed_password=get_password_hash("admin"),
        is_active=True,
        is_superuser=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return UserRead(
        id=str(admin.id),
        email=admin.email,
        is_active=admin.is_active,
        is_superuser=admin.is_superuser
    )


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
