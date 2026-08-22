from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from dashboard.health_sources import _status_rollup, collect_overview_status
from dashboard.models import HealthItem, OverviewStatus
from dashboard.pipeline_sources import collect_pipeline_status, collect_quality_status
from dashboard.security_sources import collect_security_status

# Initialize logger
logger = structlog.get_logger()

router = APIRouter()

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


class HealthResponse(BaseModel):
    status: str
    detail: str
    hint: str | None = None


@router.get("/api/status/overview", response_model=OverviewStatus)
def get_overview() -> OverviewStatus:
    """Get overview status as JSON."""
    try:
        overview = collect_overview_status()
        pipeline = collect_pipeline_status()
    except Exception as e:
        logger.exception("Error collecting overview status")
        raise HTTPException(status_code=503, detail=str(e)) from e

    pipeline_hint = (
        None
        if pipeline.overall_status == "ok"
        else "Run the pipeline scripts: bronze setup, bronze_to_silver, silver_to_gold"
    )
    items = [
        *overview.items,
        HealthItem(
            name="Pipeline",
            status=pipeline.overall_status,
            detail=" | ".join(
                f"{stage.layer}: {stage.row_count if stage.row_count is not None else 'n/a'} rows"
                for stage in pipeline.stages
            ),
            hint=pipeline_hint,
        ),
    ]

    return OverviewStatus(
        overall_status=_status_rollup(item.status for item in items),
        items=items,
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
