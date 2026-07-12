from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

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
        request,
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
        request,
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
        request,
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
        request,
        "security.html",
        {
            "request": request,
            "title": "Security",
            "api_endpoint": "/api/status/security",
        },
    )


class ConfigUpdate(BaseModel):
    env_vars: dict[str, str]

@app.get("/config", response_class=HTMLResponse)
def config_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "config.html",
        {
            "request": request,
            "title": "Configuration",
            "api_endpoint": "/api/config",
        },
    )

@app.get("/api/config")
def get_config() -> dict[str, str]:
    env_path = BASE_DIR.parent / ".env"
    config = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                config[key] = val
    return {"env_vars": config}

@app.post("/api/config")
def update_config(update: ConfigUpdate) -> dict[str, str]:
    env_path = BASE_DIR.parent / ".env"
    lines = []
    updated = set()
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith("#") and "=" in line_stripped:
                key, _ = line_stripped.split("=", 1)
                if key in update.env_vars:
                    lines.append(f"{key}={update.env_vars[key]}")
                    updated.add(key)
                else:
                    lines.append(line)
            else:
                lines.append(line)
    
    for key, val in update.env_vars.items():
        if key not in updated:
            lines.append(f"{key}={val}")
            
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"status": "success", "message": "Configuration saved"}

@app.post("/api/action/{script_name}")
def run_action(script_name: str) -> dict[str, str]:
    allowed_scripts = {
        "create_bronze": "create_bronze_tables.py",
        "bronze_to_silver": "bronze_to_silver.py",
        "silver_to_gold": "silver_to_gold.py",
    }
    if script_name not in allowed_scripts:
        return {"status": "error", "message": "Invalid script"}
        
    script_path = BASE_DIR.parent / "scripts" / allowed_scripts[script_name]
    try:
        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "output": e.stdout + "\n" + e.stderr}

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
