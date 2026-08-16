from __future__ import annotations

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import Transport, AuthenticationStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dashboard.models import Base
from dashboard.health_sources import collect_overview_status
from dashboard.pipeline_sources import collect_pipeline_status, collect_quality_status
from dashboard.security_sources import collect_security_status


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User table for authentication."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)


# Simple in-memory auth for demo (use real auth in production)
SECRET_KEY = "your-secret-key-change-in-production"


# Mock transport (replace with JWT in production)
class AuthTransport:
    @staticmethod
    def get_strategy():
        return "simple"


# Define fastapi users instance
from fastapi_users import FastAPIUsers

fastapi_users = FastAPIUsers[User, str](
    lambda user: user.id,
    [AuthTransport.get_strategy()],
)

get_current_user = fastapi_users.current_user()
get_current_active_user = fastapi_users.current_user(active=True)
get_current_superuser = fastapi_users.current_user(superuser=True)
