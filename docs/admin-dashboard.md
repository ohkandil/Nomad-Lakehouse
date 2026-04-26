# Admin Dashboard Documentation

## Purpose

The admin dashboard provides a single operational view for Nomad Lakehouse health and data pipeline status.

It is intended for local operators running the stack on Ubuntu or homelab infrastructure.

Current status: implemented and available in this repository under `dashboard/`.

## Functional Requirements

The dashboard should expose these operator views:

1. Core service health (MinIO and PostgreSQL).
1. Bronze/Silver/Gold pipeline artifact status.
1. Data freshness and basic data quality checks.
1. Security scan summary from latest local reports.

## Non-Functional Requirements

1. Local-first deployment, no cloud dependency.
1. Read-only UI for first release.
1. Fast load time on low-resource machines.
1. Clear degraded-state messaging when dependencies are unavailable.

## Runtime Architecture

1. FastAPI app serves HTML and JSON status endpoints.
1. Source adapters collect status from local files and service checks.
1. UI reads API payloads and renders cards/tables/charts.
 
Suggested runtime command:

```bash
uvicorn dashboard.app:app --host ${DASHBOARD_HOST:-127.0.0.1} --port ${DASHBOARD_PORT:-8088}
```

Implemented routes:

1. `dashboard/app.py`
1. `dashboard/health_sources.py`
1. `dashboard/pipeline_sources.py`
1. `dashboard/security_sources.py`

## Endpoint Reference

1. `GET /`:
   Overview dashboard page.
1. `GET /pipeline`:
   Bronze/Silver/Gold health page.
1. `GET /quality`:
   Data quality and freshness page.
1. `GET /security`:
   Security and scan summary page.
1. `GET /api/status/overview`:
   JSON payload for service health.
1. `GET /api/status/pipeline`:
   JSON payload for medallion stage health.
1. `GET /api/status/quality`:
   JSON payload for quality/freshness checks.
1. `GET /api/status/security`:
   JSON payload for scan summary.

## Health Signal Definitions

Status levels:

1. `ok`: service or dataset check passed.
1. `warn`: check passed with concern (for example stale data).
1. `fail`: check failed and needs action.
1. `unknown`: check could not run in current environment.

Core checks:

1. MinIO liveness endpoint reachable.
1. PostgreSQL readiness check reachable.
1. Bronze contract file exists and has expected fields.
1. Bronze DuckDB table exists and row count is positive.
1. Silver and Gold outputs exist and are readable.
1. Freshness window for latest pipeline outputs is acceptable.

## Configuration

Environment variables:

1. `DASHBOARD_HOST` default `127.0.0.1`
1. `DASHBOARD_PORT` default `8088`
1. `DASHBOARD_DATA_DIR` default `data/output`
1. `DASHBOARD_CONTRACT_DIR` default `data/contracts`
1. `DASHBOARD_REFRESH_SECONDS` default `15`

Notes on current implementation:

1. Host and port are controlled at runtime via `uvicorn` arguments.
1. Service checks currently use `MINIO_API_PORT` and `CATALOG_JDBC_URI`.

## Security Notes

1. Keep dashboard LAN-only for MVP.
1. Avoid exposing secrets in rendered pages or logs.
1. Redact connection strings and credentials from all payloads.
1. Dashboard network exposure should be through reverse proxy with auth + TLS only.

## Secure Reverse Proxy Deployment

Recommended local-network pattern:

1. Dashboard app listens on `127.0.0.1:8088` only.
1. `nomad-dashboard.service` manages uvicorn uptime.
1. Caddy handles HTTPS (`tls internal`), Basic Auth, and proxying to loopback upstream.
1. Caddy route is limited to configured private CIDRs by default.

Install sequence:

```bash
sudo ./scripts/install_dashboard_service.sh
sudo DASHBOARD_DOMAIN=dashboard.home.arpa \
   DASHBOARD_AUTH_USER=admin \
   DASHBOARD_AUTH_PASSWORD='change-me-strong-password' \
   ./scripts/install_dashboard_reverse_proxy.sh
```

Verification:

```bash
curl -fsS http://127.0.0.1:8088/api/status/overview
curl -k -u admin:'change-me-strong-password' https://dashboard.home.arpa/api/status/overview
```

Operational notes:

1. Import Caddy local CA cert to client trust stores for warning-free HTTPS.
1. Rotate dashboard credentials regularly.
1. Keep direct Uvicorn port blocked from LAN firewall rules.

## Operations Runbook

Start dashboard:

```bash
source .venv/bin/activate
uvicorn dashboard.app:app --host 127.0.0.1 --port 8088
```

Or run as a managed service:

```bash
sudo ./scripts/install_dashboard_service.sh
systemctl status --no-pager nomad-dashboard.service
```

Verify:

```bash
curl -fsS http://127.0.0.1:8088/api/status/overview
curl -k -u <user>:<password> https://<dashboard-domain>/api/status/overview
```

Stop:

1. `Ctrl+C` in foreground process, or
1. stop the associated systemd unit when configured.

## Troubleshooting Guide

Dashboard returns `unknown` for PostgreSQL:

1. Ensure Docker engine is running.
1. Ensure `postgres` container is healthy.
1. Validate compose env values in `.env`.

Bronze status is `fail` with missing contract:

1. Run `python3 scripts/create_bronze_tables.py`.
1. Verify file at `data/contracts/bronze_orders_contract.json`.

Gold freshness warning:

1. Run `python3 scripts/bronze_to_silver.py`.
1. Run `python3 scripts/silver_to_gold.py`.
1. Refresh dashboard after pipeline completion.

## Documentation Maintenance Rules

When dashboard behavior changes, update in the same PR:

1. `README.md` documentation index.
1. `docs/admin-dashboard-plan.md` if scope or milestone changes.
1. `docs/admin-dashboard.md` endpoint/config/runbook details.
1. `docs/setup.md` if setup commands change.
