from __future__ import annotations

import subprocess
import structlog
from pathlib import Path
from typing import Literal
from datetime import UTC, datetime

import pandas as pd

from dashboard.models import PipelineStageStatus, PipelineStatus, QualityCheck, QualityStatus, SecurityStatus
from dashboard.pipeline_sources import DUCKDB_PATH, SILVER_PATH, GOLD_PATH, CONTRACT_PATH

# Initialize logger
logger = structlog.get_logger()

StatusLevel = Literal["ok", "warn", "fail", "unknown"]


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _iso_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return pd.Timestamp(path.stat().st_mtime_ns, unit="ns", tz="UTC").isoformat()


def _bronze_row_count() -> tuple[int | None, str]:
    if not DUCKDB_PATH.exists():
        return None, "DuckDB database not found"

    try:
        import duckdb
    except ImportError:
        return None, "duckdb package not installed; cannot query bronze table"

    try:
        with duckdb.connect(str(DUCKDB_PATH)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM bronze.orders").fetchone()
            if row is None:
                return None, "bronze.orders returned no row count"
            return int(row[0]), "bronze.orders row count loaded"
    except Exception as exc:
        logger.exception("Error querying bronze.orders")
        return None, f"Unable to query bronze.orders: {exc}"


def _csv_stage(layer: str, path: Path) -> PipelineStageStatus:
    if not path.exists():
        return PipelineStageStatus(
            layer=layer,
            status="fail",
            row_count=None,
            last_updated=None,
            detail=f"Missing artifact: {path.relative_to(Path(__file__).resolve().parent.parent)}",
        )

    mtime = _iso_mtime(path)
    return PipelineStageStatus(
        layer=layer,
        status="ok",
        row_count=None,  # CSV files don't have row counts in this implementation
        last_updated=mtime,
        detail=f"Artifact exists: {path.name}",
    )


def collect_pipeline_status() -> PipelineStatus:
    """Collect pipeline status across all stages."""
    bronze_row_count, bronze_detail = _bronze_row_count()
    bronze_status = "ok" if bronze_row_count is not None else "fail"

    silver = _csv_stage("silver", SILVER_PATH)
    gold = _csv_stage("gold", GOLD_PATH)

    stages = [
        PipelineStageStatus(
            layer="bronze",
            status=bronze_status,
            row_count=bronze_row_count,
            last_updated=_iso_mtime(DUCKDB_PATH) if DUCKDB_PATH.exists() else None,
            detail=bronze_detail,
        ),
        silver,
        gold,
    ]

    overall = "fail"
    for stage in stages:
        if stage.status == "ok":
            overall = "ok"
            break
        elif stage.status == "warn":
            if overall != "fail":
                overall = "warn"

    return PipelineStatus(
        generated_at=utc_now_iso(),
        stages=stages,
        overall_status=overall,
    )


def collect_quality_status() -> QualityStatus:
    """Collect data quality metrics."""
    checks: list[QualityCheck] = []

    # Check bronze row count
    bronze_row_count, bronze_detail = _bronze_row_count()
    if bronze_row_count is not None and bronze_row_count > 0:
        checks.append(
            QualityCheck(
                name="Bronze Orders Count",
                status="ok",
                value=str(bronze_row_count),
                detail=bronze_detail,
            )
        )
    else:
        checks.append(
            QualityCheck(
                name="Bronze Orders Count",
                status="fail",
                value="0",
                detail=bronze_detail,
            )
        )

    # Check silver artifact
    silver_status = "ok" if SILVER_PATH.exists() else "fail"
    checks.append(
        QualityCheck(
            name="Silver Artifact",
            status=silver_status,
            value="exists" if SILVER_PATH.exists() else "missing",
            detail="Silver orders CSV" if SILVER_PATH.exists() else "Silver artifact not found",
        )
    )

    # Check gold artifact
    gold_status = "ok" if GOLD_PATH.exists() else "fail"
    checks.append(
        QualityCheck(
            name="Gold Artifact",
            status=gold_status,
            value="exists" if GOLD_PATH.exists() else "missing",
            detail="Gold daily revenue CSV" if GOLD_PATH.exists() else "Gold artifact not found",
        )
    )

    # Check contract artifact
    contract_status = "ok" if CONTRACT_PATH.exists() else "fail"
    checks.append(
        QualityCheck(
            name="Ingestion Contract",
            status=contract_status,
            value="exists" if CONTRACT_PATH.exists() else "missing",
            detail="Bronze orders contract JSON" if CONTRACT_PATH.exists() else "Contract not found",
        )
    )

    return QualityStatus(
        generated_at=utc_now_iso(),
        checks=checks,
    )


def collect_security_status() -> SecurityStatus:
    """Collect security scan results."""
    try:
        # Read security scan results if available
        report_path = Path(__file__).parent.parent / "data" / "output" / "security_report.txt"
        if report_path.exists():
            with open(report_path, "r") as f:
                content = f.read()
            lines = content.split("\n")
            high_count = sum(1 for line in lines if "HIGH" in line or "CRITICAL" in line)
            critical_count = sum(1 for line in lines if "CRITICAL" in line)
            detail = f"Security scan completed with {high_count} high severity findings"
            status = "warn" if high_count > 0 else "ok"
        else:
            detail = "No security scan report found"
            high_count = 0
            critical_count = 0
            status = "ok"

        return SecurityStatus(
            generated_at=utc_now_iso(),
            status=status,
            detail=detail,
            report_path=str(report_path) if report_path.exists() else None,
            high_count=high_count,
            critical_count=critical_count,
        )
    except Exception as exc:
        logger.exception("Error collecting security status")
        return SecurityStatus(
            generated_at=utc_now_iso(),
            status="unknown",
            detail=f"Error collecting security status: {exc}",
            report_path=None,
            high_count=None,
            critical_count=None,
        )


def collect_overview_status() -> dict:
    """Collect overall system health status."""
    try:
        # Check MinIO
        minio_port = os.environ.get("MINIO_API_PORT", "9000")
        minio_health = subprocess.run(
            ["curl", "-fsS", f"http://localhost:{minio_port}/minio/health/live"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        minio_status = "ok" if minio_health.returncode == 0 else "fail"
        minio_detail = "MinIO is healthy" if minio_status == "ok" else "MinIO is unreachable"

        # Check PostgreSQL
        postgres_user = os.environ.get("POSTGRES_USER", "iceberg")
        postgres_db = os.environ.get("POSTGRES_DB", "iceberg")
        postgres_port = os.environ.get("POSTGRES_PORT", "5432")

        postgres_health = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres", "pg_isready", "-U", postgres_user, "-d", postgres_db],
            capture_output=True,
            text=True,
            timeout=5,
        )

        postgres_status = "ok" if postgres_health.returncode == 0 else "fail"
        postgres_detail = "PostgreSQL is healthy" if postgres_status == "ok" else "PostgreSQL is unreachable"

        # Collect pipeline status
        pipeline = collect_pipeline_status()

        # Overall status
        overall_status = pipeline.overall_status

        # Build health items
        items = [
            DashboardHealthItem(name="MinIO", status=minio_status, detail=minio_detail),
            DashboardHealthItem(name="PostgreSQL", status=postgres_status, detail=postgres_detail),
        ]

        for stage in pipeline.stages:
            items.append(DashboardHealthItem(name=f"Bronze ({stage.layer})", status=stage.status, detail=stage.detail))

        return {
            "generated_at": utc_now_iso(),
            "overall_status": overall_status,
            "items": items,
        }
    except Exception as exc:
        logger.exception("Error collecting overview status")
        return {
            "generated_at": utc_now_iso(),
            "overall_status": "fail",
            "items": [
                DashboardHealthItem(
                    name="System",
                    status="fail",
                    detail=f"Error collecting status: {exc}",
                )
            ],
        }


class DashboardHealthItem(BaseModel):
    name: str
    status: StatusLevel
    detail: str
    hint: str | None = None
