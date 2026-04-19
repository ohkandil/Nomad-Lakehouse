from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.pipeline_sources import collect_pipeline_status, collect_quality_status
from dashboard.security_sources import collect_security_status

client = TestClient(app)


def test_pipeline_status_returns_three_stages() -> None:
    status = collect_pipeline_status()
    assert len(status.stages) == 3
    assert {stage.layer for stage in status.stages} == {"bronze", "silver", "gold"}


def test_quality_status_returns_checks() -> None:
    quality = collect_quality_status()
    assert len(quality.checks) >= 2


def test_security_status_handles_missing_report() -> None:
    status = collect_security_status()
    assert status.status in {"ok", "warn", "fail", "unknown"}


def test_overview_api_responds() -> None:
    response = client.get("/api/status/overview")
    assert response.status_code == 200
    payload = response.json()
    assert "overall_status" in payload
    assert "items" in payload


def test_pipeline_api_responds() -> None:
    response = client.get("/api/status/pipeline")
    assert response.status_code == 200
    payload = response.json()
    assert "stages" in payload


def test_quality_api_responds() -> None:
    response = client.get("/api/status/quality")
    assert response.status_code == 200
    payload = response.json()
    assert "checks" in payload


def test_security_api_responds() -> None:
    response = client.get("/api/status/security")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload


def test_security_report_parsing(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "pip-audit-report.json"
    payload = {
        "vulnerabilities": [
            {"severity": "high"},
            {"severity": "critical"},
            {"severity": "low"},
        ]
    }
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr("dashboard.security_sources.CANDIDATE_REPORTS", [report_path])
    status = collect_security_status()

    assert status.status == "fail"
    assert status.high_count == 1
    assert status.critical_count == 1
