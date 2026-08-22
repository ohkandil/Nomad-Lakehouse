from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

StatusLevel = Literal["ok", "warn", "fail", "unknown"]


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class HealthItem(BaseModel):
    name: str
    status: StatusLevel
    detail: str
    hint: str | None = None


class OverviewStatus(BaseModel):
    generated_at: str = Field(default_factory=utc_now_iso)
    overall_status: StatusLevel
    items: list[HealthItem]


class PipelineStageStatus(BaseModel):
    layer: str
    status: StatusLevel
    row_count: int | None
    last_updated: str | None
    detail: str


class PipelineStatus(BaseModel):
    generated_at: str = Field(default_factory=utc_now_iso)
    overall_status: StatusLevel = "unknown"
    stages: list[PipelineStageStatus]


class QualityCheck(BaseModel):
    name: str
    status: StatusLevel
    value: str
    detail: str


class QualityStatus(BaseModel):
    generated_at: str = Field(default_factory=utc_now_iso)
    checks: list[QualityCheck]


class SecurityStatus(BaseModel):
    generated_at: str = Field(default_factory=utc_now_iso)
    status: StatusLevel
    detail: str
    report_path: str | None = None
    high_count: int | None = None
    critical_count: int | None = None


class DashboardHealthItem(BaseModel):
    name: str
    status: StatusLevel
    detail: str
    hint: str | None = None
