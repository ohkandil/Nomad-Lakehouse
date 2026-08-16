from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from dashboard.auth_config import User

# Import all route modules
from dashboard.auth_routes import router as auth_router
from dashboard.config_routes import router as config_router
from dashboard.database import get_db, init_db
from dashboard.login_routes import router as login_router
from dashboard.security import get_password_hash
from dashboard.status_routes import router as status_router

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "your-secret-key-change-in-production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize database on startup
    init_db()

    # Create default admin user if not exists
    db = next(get_db())
    try:
        existing_user = db.query(User).filter(User.email == "admin@nomad.lakehouse").first()
        if not existing_user:
            admin = User(
                email="admin@nomad.lakehouse",
                hashed_password=get_password_hash("admin"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="Nomad Admin Dashboard",
    version="0.2.0",
    lifespan=lifespan
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Include all routers
app.include_router(auth_router)
app.include_router(login_router)
app.include_router(status_router)
app.include_router(config_router)

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# Root route - redirect to login if not authenticated
@app.get("/", response_class=HTMLResponse)
def root(request: Request) -> HTMLResponse:
    """Root route - redirect to login if not authenticated."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    # User is authenticated, show overview
    return templates.TemplateResponse(
        request,
        "overview.html",
        {"request": request, "title": "Overview"}
    )


# Login page
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    """Login page."""
    return templates.TemplateResponse(
        request,
        "login.html",
        {"request": request, "title": "Login"}
    )


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}