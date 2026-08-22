# Admin Dashboard Implementation Plan

Status update (2026-04):

1. Baseline dashboard is implemented under `dashboard/`.
1. HTML routes and status APIs are available and covered by tests.
1. This document now acts as a roadmap for incremental improvements.

## Objective

Build a local-first admin dashboard that gives operators one place to monitor Nomad Lakehouse health, data pipeline freshness, and key service signals.

Primary outcomes:

1. Detect service outages quickly.
1. Detect stale data or failed medallion stages.
1. Provide fast operational troubleshooting context.

## Scope

In scope for first release:

1. Service health overview for MinIO and PostgreSQL.
1. Pipeline artifact health for Bronze, Silver, and Gold outputs.
1. Data freshness indicators and row-count trend snapshots.
1. Security scan status summary from latest local scan reports.
1. Read-only dashboard access on LAN.

Implemented in current baseline:

1. Service health overview APIs and pages.
1. Pipeline, quality, and security status APIs and pages.
1. Basic tests in `tests/test_dashboard_sources.py`.

Out of scope for first release:

1. Write-back actions (restart services, run pipelines) from UI.
1. Internet exposure, auth federation, or multi-user RBAC.
1. Historical metrics retention beyond local snapshots.

## Proposed Technical Approach

Recommended stack:

1. Backend: FastAPI service in Python.
1. Frontend: server-rendered Jinja templates with lightweight JS charts.
1. Data source adapters: existing scripts and local artifacts (DuckDB, CSV, JSON, Docker status).
1. Optional charting: Chart.js loaded locally.
1. Authentication: JWT-based auth via fastapi-users with session middleware.

Why this approach:

1. Aligns with current Python-first repository.
1. Keeps dependency footprint low.
1. Supports simple local hosting and systemd integration.

## Dashboard Information Architecture

Page 1: Overview

1. Overall system status badge (Healthy/Degraded/Down).
1. MinIO status (live endpoint check).
1. PostgreSQL status (pg_isready check through Docker exec or host socket fallback).
1. Last successful pipeline run time per layer.

Page 2: Pipeline Health

1. Bronze: contract file presence, contract version, bronze row count.
1. Silver: file presence, row count, newest order_date.
1. Gold: file presence, row count, latest aggregation date.
1. Stage-level validation messages and failure hints.

Page 3: Data Quality and Freshness

1. Null and duplicate summary from Silver output.
1. Revenue sanity checks from Gold output.
1. Freshness SLA indicator (for example: green if updated in last 24h).

Page 4: Security and Ops

1. Latest security scan run timestamp.
1. High/Critical vulnerability count from latest report file.
1. Quick links to runbook commands.

## File and Module Plan

Proposed additions:

1. `dashboard/app.py` (FastAPI app bootstrap and route wiring).
1. `dashboard/health_sources.py` (MinIO/Postgres/system checks).
1. `dashboard/pipeline_sources.py` (Bronze/Silver/Gold artifact checks).
1. `dashboard/security_sources.py` (scan report parsing).
1. `dashboard/models.py` (typed response models).
1. `dashboard/templates/` (overview, pipeline, quality, security pages).
1. `dashboard/static/` (css and chart js assets).
1. `scripts/run_dashboard.sh` (local launcher for Linux).
1. `tests/test_dashboard_sources.py` (unit tests for health data adapters).
1. `tests/test_dashboard_login.py` (login flow and session tests).

## API and Data Contracts

Internal API endpoints to support UI:

1. `GET /api/status/overview` (JSON: `overall_status` + `items`)
1. `GET /api/status/pipeline`
1. `GET /api/status/quality`
1. `GET /api/status/security`

Contract requirements:

1. Every endpoint returns `generated_at` in ISO-8601 UTC.
1. Every health item includes `status` in `ok|warn|fail|unknown`.
1. Every warning/failure includes a short remediation hint.

## Milestone Plan (Roadmap)

Phase 1: Foundation (completed)

1. Scaffold dashboard package and FastAPI app entrypoint.
1. Add overview route and basic HTML template.
1. Add health adapters for MinIO and PostgreSQL.

Exit criteria:

1. Overview page loads locally.
1. Service status indicators render correctly for up/down cases.

Phase 2: Pipeline Observability (completed)

1. Add Bronze/Silver/Gold artifact readers.
1. Add row count and freshness cards.
1. Add pipeline status API endpoint and page.

Exit criteria:

1. Dashboard detects missing contract/output files.
1. Pipeline freshness and row counts display correctly.

Phase 3: Data Quality and Security (completed baseline)

1. Add Silver/Gold quality checks and threshold warnings.
1. Parse latest security scan artifacts.
1. Add quality and security pages.

Exit criteria:

1. Quality warnings surface clearly.
1. Security summary displays latest scan result.

Phase 4: Hardening and Docs (in progress / next)

1. Add tests for all status adapters.
1. Add run script and setup docs.
1. Add troubleshooting matrix for common dashboard issues.

Exit criteria:

1. Tests pass in CI.
1. Setup documentation is reproducible on Ubuntu 24.04.

## Dependencies and Configuration

Planned dependencies:

1. `fastapi`
1. `uvicorn`
1. `jinja2`

Optional:

1. `psutil` (host metrics)

Environment variables:

1. `DASHBOARD_HOST` default `127.0.0.1`
1. `DASHBOARD_PORT` default `8088`
1. `DASHBOARD_READ_TIMEOUT_SECONDS` default `2`
1. `DASHBOARD_DATA_DIR` default `data/output`

## Testing Strategy

Unit tests:

1. Service health adapters (success and failure cases).
1. Pipeline artifact parsers with sample fixtures.
1. Security report parsing logic.

Integration tests:

1. Dashboard endpoint smoke tests.
1. End-to-end test with generated Bronze/Silver/Gold artifacts.

CI additions:

1. Include dashboard tests in existing `pytest` execution.
1. Add lint and typing checks for new dashboard modules.

## Risks and Mitigations

Risk: False alarms when running on non-Linux hosts.

Mitigation: Separate host checks from container checks and mark unsupported checks as `unknown`.

Risk: Slow dashboard load due to large artifact scans.

Mitigation: Cache computed health snapshots for short intervals (for example 10-30 seconds).

Risk: Drift between scripts and dashboard assumptions.

Mitigation: Reuse parsing logic from existing output contracts; add tests tied to sample data.

## Definition of Done

The admin dashboard first release is complete when:

1. Overview and pipeline pages are functional.
1. Bronze/Silver/Gold health signals are visible and actionable.
1. Security summary is displayed from latest artifacts.
1. Setup and operations docs are published.
1. CI validates dashboard code paths.
