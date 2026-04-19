from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dashboard.health_sources import collect_overview_status
from dashboard.pipeline_sources import collect_pipeline_status, collect_quality_status
from dashboard.security_sources import collect_security_status

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Nomad Admin Dashboard", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def overview_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "overview.html",
        {
            "request": request,
            "title": "Overview",
            "api_endpoint": "/api/status/overview",
        },
    )


@app.get("/pipeline", response_class=HTMLResponse)
def pipeline_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "pipeline.html",
        {
            "request": request,
            "title": "Pipeline Health",
            "api_endpoint": "/api/status/pipeline",
        },
    )


@app.get("/quality", response_class=HTMLResponse)
def quality_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "quality.html",
        {
            "request": request,
            "title": "Data Quality",
            "api_endpoint": "/api/status/quality",
        },
    )


@app.get("/security", response_class=HTMLResponse)
def security_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "security.html",
        {
            "request": request,
            "title": "Security",
            "api_endpoint": "/api/status/security",
        },
    )


@app.get("/api/status/overview")
def overview_status() -> dict[str, object]:
    return collect_overview_status().model_dump()


@app.get("/api/status/pipeline")
def pipeline_status() -> dict[str, object]:
    return collect_pipeline_status().model_dump()


@app.get("/api/status/quality")
def quality_status() -> dict[str, object]:
    return collect_quality_status().model_dump()


@app.get("/api/status/security")
def security_status() -> dict[str, object]:
    return collect_security_status().model_dump()
