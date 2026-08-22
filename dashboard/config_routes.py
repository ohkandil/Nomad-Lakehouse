from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Initialize logger
logger = structlog.get_logger()

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class ConfigResponse(BaseModel):
    success: bool
    message: str


@router.get("/config", response_class=HTMLResponse)
def config_page(request: Request) -> HTMLResponse:
    """Configuration page."""
    return templates.TemplateResponse(
        request,
        "config.html",
        {"request": request, "title": "Configuration"}
    )


@router.get("/api/config", response_class=HTMLResponse)
def get_config(request: Request) -> HTMLResponse:
    """Get current configuration."""
    return templates.TemplateResponse(
        request,
        "config.html",
        {"request": request, "title": "Configuration"}
    )


@router.post("/api/config/save", response_class=HTMLResponse)
def save_config(
    request: Request,
    minio_api_port: str,
    minio_console_port: str,
    postgres_port: str,
    dashboard_host: str,
    dashboard_port: str,
    warehouse_bucket: str
) -> ConfigResponse:
    """Save configuration."""
    # In production, save to a config file or environment variables
    logger.info(
        "Configuration saved",
        minio_api_port=minio_api_port,
        minio_console_port=minio_console_port,
        postgres_port=postgres_port,
        dashboard_host=dashboard_host,
        dashboard_port=dashboard_port,
        warehouse_bucket=warehouse_bucket
    )

    return ConfigResponse(
        success=True,
        message="Configuration saved successfully"
    )
