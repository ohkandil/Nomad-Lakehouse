from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dashboard.auth_config import User

# Initialize logger
logger = structlog.get_logger()

router = APIRouter()

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def verify_admin(username: str, password: str) -> User:
    """Verify admin credentials."""
    # Hardcoded admin for demo (use real auth in production)
    if username == "admin" and password == "admin":
        return User(
            id="admin",
            email="admin@nomad.lakehouse",
            is_active=True,
            is_superuser=True
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
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
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
) -> RedirectResponse:
    """Handle login."""
    try:
        user = verify_admin(username, password)
    except HTTPException:
        return RedirectResponse(url="/login?error=invalid", status_code=302)

    # Create session (using simple session for demo)
    request.session["user_id"] = str(user.id)
    request.session["is_superuser"] = user.is_superuser

    return RedirectResponse(url="/", status_code=302)


@router.get("/logout")
def logout(request: Request) -> RedirectResponse:
    """Handle logout."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/protected", response_class=HTMLResponse)
def protected_page(request: Request) -> Response:
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
