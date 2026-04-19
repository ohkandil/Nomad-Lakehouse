from __future__ import annotations

import os
import re
import socket
from collections.abc import Iterable

import requests

from dashboard.models import HealthItem, OverviewStatus, StatusLevel


def _status_rollup(statuses: Iterable[StatusLevel]) -> StatusLevel:
    normalized = list(statuses)
    if any(status == "fail" for status in normalized):
        return "fail"
    if any(status == "warn" for status in normalized):
        return "warn"
    if any(status == "unknown" for status in normalized):
        return "unknown"
    return "ok"


def check_minio() -> HealthItem:
    minio_port = os.getenv("MINIO_API_PORT", "9000")
    url = f"http://localhost:{minio_port}/minio/health/live"
    try:
        response = requests.get(url, timeout=2)
        if response.ok:
            return HealthItem(name="MinIO", status="ok", detail=f"Reachable at {url}")
        return HealthItem(
            name="MinIO",
            status="warn",
            detail=f"Endpoint responded with HTTP {response.status_code}",
            hint="Validate the minio container status with docker compose ps",
        )
    except requests.RequestException as exc:
        return HealthItem(
            name="MinIO",
            status="fail",
            detail=f"Not reachable at {url}: {exc}",
            hint="Run scripts/setup_minio.sh and retry",
        )


def _parse_catalog_jdbc() -> tuple[str, int] | None:
    jdbc_uri = os.getenv("CATALOG_JDBC_URI", "")
    match = re.match(r"^jdbc:postgresql://(?P<host>[^:/]+):(?P<port>\d+)/", jdbc_uri)
    if match is None:
        return None
    return match.group("host"), int(match.group("port"))


def check_postgres() -> HealthItem:
    parsed = _parse_catalog_jdbc()
    if parsed is None:
        return HealthItem(
            name="PostgreSQL Catalog",
            status="unknown",
            detail="CATALOG_JDBC_URI is not configured or invalid",
            hint="Set CATALOG_JDBC_URI in .env",
        )

    host, port = parsed
    host_candidates = [host]
    if host == "postgres":
        host_candidates.append("localhost")

    for candidate in host_candidates:
        try:
            with socket.create_connection((candidate, port), timeout=2):
                return HealthItem(
                    name="PostgreSQL Catalog",
                    status="ok",
                    detail=f"TCP reachable at {candidate}:{port}",
                )
        except OSError:
            continue

    return HealthItem(
        name="PostgreSQL Catalog",
        status="fail",
        detail=f"Unable to reach PostgreSQL at {host}:{port}",
        hint="Ensure docker engine is running and postgres service is healthy",
    )


def collect_overview_status() -> OverviewStatus:
    items = [check_minio(), check_postgres()]
    return OverviewStatus(overall_status=_status_rollup(item.status for item in items), items=items)
