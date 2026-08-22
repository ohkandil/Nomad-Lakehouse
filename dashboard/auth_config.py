from __future__ import annotations

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from dashboard.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User table for authentication."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)


# Simple in-memory auth for demo (use real auth in production)
SECRET_KEY = "your-secret-key-change-in-production"

# Define JWT strategy
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET_KEY, lifetime_seconds=3600)

# Define transport
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# Define authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Define fastapi users instance
fastapi_users = FastAPIUsers[User, str](
    lambda user: user.id,
    [auth_backend],
)

get_current_user = fastapi_users.current_user()
get_current_active_user = fastapi_users.current_user(active=True)
get_current_superuser = fastapi_users.current_user(superuser=True)
