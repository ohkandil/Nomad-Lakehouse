from __future__ import annotations

import subprocess
import structlog
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from dashboard.database import get_db

# Initialize logger
logger = structlog.get_logger()

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    detail: str
    hint: str | None = None


@router.get("/api/status/overview", response_class=HTMLResponse)
def get_overview(request: Request) -> HTMLResponse:
    """Get overview status."""
    try:
        status_data = collect_overview_status()

        return templates.TemplateResponse(
            request,
            "overview.html",
            {
                "request": request,
                "title": "Overview",
                "api_endpoint": "/api/status/overview",
                "status_data": status_data,
                "quality_checks": []
            }
        )
    except Exception as e:
        logger.exception("Error collecting overview status")
        return templates.TemplateResponse(
            request,
            "overview.html",
            {
                "request": request,
                "title": "Overview",
                "api_endpoint": "/api/status/overview",
                "error": str(e)
            }
        )


@router.get("/api/status/pipeline", response_class=HTMLResponse)
def get_pipeline(request: Request) -> HTMLResponse:
    """Get pipeline status."""
    try:
        status_data = collect_pipeline_status()

        return templates.TemplateResponse(
            request,
            "pipeline.html",
            {
                "request": request,
                "title": "Pipeline",
                "api_endpoint": "/api/status/pipeline",
                "status_data": status_data
            }
        )
    except Exception as e:
        logger.exception("Error collecting pipeline status")
        return templates.TemplateResponse(
            request,
            "pipeline.html",
            {
                "request": request,
                "title": "Pipeline",
                "api_endpoint": "/api/status/pipeline",
                "error": str(e)
            }
        )


@router.get("/api/status/quality", response_class=HTMLResponse)
def get_quality(request: Request) -> HTMLResponse:
    """Get quality status."""
    try:
        status_data = collect_quality_status()

        return templates.TemplateResponse(
            request,
            "quality.html",
            {
                "request": request,
                "title": "Quality",
                "api_endpoint": "/api/status/quality",
                "quality_checks": status_data.checks,
                "generated_at": status_data.generated_at
            }
        )
    except Exception as e:
        logger.exception("Error collecting quality status")
        return templates.TemplateResponse(
            request,
            "quality.html",
            {
                "request": request,
                "title": "Quality",
                "api_endpoint": "/api/status/quality",
                "error": str(e)
            }
        )


@router.get("/api/status/security", response_class=HTMLResponse)
def get_security(request: Request) -> HTMLResponse:
    """Get security status."""
    try:
        status_data = collect_security_status()

        return templates.TemplateResponse(
            request,
            "security.html",
            {
                "request": request,
                "title": "Security",
                "api_endpoint": "/api/status/security",
                "status_data": status_data,
                "high_count": status_data.high_count,
                "critical_count": status_data.critical_count,
                "report_path": status_data.report_path,
                "generated_at": status_data.generated_at
            }
        )
    except Exception as e:
        logger.exception("Error collecting security status")
        return templates.TemplateResponse(
            request,
            "security.html",
            {
                "request": request,
                "title": "Security",
                "api_endpoint": "/api/status/security",
                "error": str(e)
            }
        )
