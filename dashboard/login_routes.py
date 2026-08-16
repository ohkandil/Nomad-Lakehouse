from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from dashboard.auth_config import User

# Initialize logger
logger = structlog.get_logger()

router = APIRouter()
security = HTTPBasic()

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def verify_admin(credentials: HTTPBasicCredentials | None) -> User:
    """Verify admin credentials."""
    credentials = Depends(security)(credentials)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Hardcoded admin for demo (use real auth in production)
    if credentials.username == "admin" and credentials.password == "admin":
        user = User(
            id="admin",
            email="admin@nomad.lakehouse",
            is_active=True,
            is_superuser=True
        )
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    """Login page."""
    return templates.TemplateResponse(
        request,
        "login.html",
        {"request": request, "title": "Login"}
    )


@router.post("/login")
def login(credentials: HTTPBasicCredentials, request: Request):
    """Handle login."""
    credentials = Depends(security)(credentials)
    user = verify_admin(credentials)

    # Create session (using simple session for demo)
    request.session["user_id"] = str(user.id)
    request.session["is_superuser"] = user.is_superuser

    return RedirectResponse(url="/", status_code=302)


@router.get("/logout")
def logout(request: Request):
    """Handle logout."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/protected")
def protected_page(request: Request) -> HTMLResponse:
    """Protected page requiring authentication."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        request,
        "overview.html",
        {
            "request": request,
            "title": "Overview",
            "api_endpoint": "/api/status/overview",
            "user": {"id": user_id}
        }
    )
