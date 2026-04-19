# Nomad Lakehouse

Lightweight, local-first data lakehouse for Ubuntu servers and homelabs.

Nomad focuses on practical Bronze/Silver/Gold workflows using open-source components, with minimal infrastructure overhead and strong security defaults.

## Main Goal

Nomad is designed to fill the gap between toy local demos and heavyweight enterprise lakehouse stacks.

It is intentionally:

- Lightweight and resource-aware
- Easy to deploy on local servers
- Portable across machines using Docker Compose
- Modular, so each operational function is script-based and composable

## Stack and Why

- MinIO: S3-compatible object storage for local data lake files
- PostgreSQL: stable JDBC metadata backend for catalog state
- Apache Iceberg workflow path: modern table-format direction for ACID/versioned data patterns
- Python 3: portable pipeline and validation scripts
- DuckDB: fast local query engine for analytics and verification
- FastAPI dashboard: interactive operational UI for health and pipeline monitoring
- Docker Compose: reproducible service orchestration on a single machine

## Quick Start (Ubuntu 24.04)

```bash
git clone https://github.com/ohkandil/nomad-lakehouse nomad-lakehouse
cd nomad-lakehouse
cp .env.example .env
chmod +x scripts/*.sh
sudo ./scripts/setup_minio.sh
INSTALL_PROFILE=lakehouse ./scripts/setup_python_env.sh
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

## Admin Dashboard

Run:

```bash
source .venv/bin/activate
python3 -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8088
```

Open:

- http://127.0.0.1:8088/
- http://127.0.0.1:8088/pipeline
- http://127.0.0.1:8088/quality
- http://127.0.0.1:8088/security

## Current Implementation

- Linux-first deployment baseline
- MinIO + PostgreSQL services with health checks
- Bucket bootstrap (`minio-init`) and environment bootstrap scripts
- Bronze ingestion contract generation (`data/contracts/bronze_orders_contract.json`)
- Bronze table materialization in DuckDB (`bronze.orders`) with rerunnable `CREATE OR REPLACE` semantics
- Bronze -> Silver -> Gold starter pipeline
- CI with lint, typing, tests, and security checks

## Week 2 Highlights

- Catalog backend connectivity validation: `create_bronze_tables.py` validates JDBC target reachability from `CATALOG_JDBC_URI`
- Repeatable Bronze setup: reruns update the same `bronze.orders` table without manual cleanup
- Contract-first ingestion: schema/constraints exported as a versioned JSON contract
- Recruiter-friendly evidence path: closure checklist and explicit verification commands

Current verification evidence may vary by host environment. Treat `docs/week2-closure.md` as the source of truth for your latest local validation run.

## Security Workflow

Mandatory stage gate:

```bash
sudo ./scripts/security_scan.sh
python3 -m pip_audit
python3 -m bandit -r scripts
```

If vulnerabilities are found:

```bash
./scripts/remediate_python_vulns.sh
python3 -m pip_audit
```

## Stage 1 Validation Checklist

1. `sudo ./scripts/setup_minio.sh`
1. `sudo ./scripts/healthcheck.sh`
1. `sudo ./scripts/install_systemd_service.sh`
1. Reboot host and verify `nomad-lakehouse.service` auto-start
1. `./scripts/setup_python_env.sh`
1. Run all three pipeline scripts
1. Verify outputs in `data/output/`
1. Run security workflow and log findings
1. Record evidence in `docs/week1-closure.md`

## Week 2 Validation Checklist

1. Ensure services are running: `sudo ./scripts/setup_minio.sh`
1. Activate environment: `source .venv/bin/activate`
1. Run Bronze workflow: `python3 scripts/create_bronze_tables.py`
1. Verify generated contract: `cat data/contracts/bronze_orders_contract.json`
1. Verify Bronze table is queryable:

```bash
python3 - <<'PY'
import duckdb
con = duckdb.connect("data/output/lakehouse.duckdb")
print(con.execute("SELECT COUNT(*) AS rows FROM bronze.orders").fetchall())
print(con.execute("SELECT * FROM bronze.orders ORDER BY order_id LIMIT 5").fetchdf())
PY
```

1. Record evidence in `docs/week2-closure.md`

## Next Steps

- Expand from Bronze contract and DuckDB table materialization to full Iceberg table commit flow
- Add incremental ingestion and stronger data quality contracts
- Add richer observability and operational diagnostics
- Improve onboarding path toward near plug-and-play deployment

## Documentation Policy

Every behavioral, operational, or workflow change must include matching documentation updates in the same pull request.

## Repository Layout

```text
.
├── .github/workflows/ci.yml
├── docker-compose.yml
├── pyproject.toml
├── dashboard/
│   ├── app.py
│   ├── health_sources.py
│   ├── pipeline_sources.py
│   ├── security_sources.py
│   ├── static/
│   └── templates/
├── scripts/
│   ├── setup_minio.sh
│   ├── install_systemd_service.sh
│   ├── setup_python_env.sh
│   ├── healthcheck.sh
│   ├── security_scan.sh
│   ├── remediate_python_vulns.sh
│   ├── hardening_checklist.sh
│   ├── backup_metadata.sh
│   ├── restore_metadata.sh
│   ├── create_bronze_tables.py
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py
├── docs/
│   ├── setup.md
│   ├── ubuntu-deploy.md
│   ├── architecture.md
│   ├── examples.md
│   ├── admin-dashboard-plan.md
│   ├── admin-dashboard.md
│   ├── week1-closure.md
│   └── week2-closure.md
├── data/sample/orders.csv
└── tests/
```

## Documentation Index

- Setup guide: `docs/setup.md`
- Deployment runbook: `docs/ubuntu-deploy.md`
- Architecture summary: `docs/architecture.md`
- Pipeline and query examples: `docs/examples.md`
- Admin dashboard implementation plan: `docs/admin-dashboard-plan.md`
- Admin dashboard documentation: `docs/admin-dashboard.md`
- Week 1 closure evidence: `docs/week1-closure.md`
- Week 2 closure evidence: `docs/week2-closure.md`
- Implementation roadmap: `PROJECT_PLAN.md`

## Portfolio Notes (Junior Data Engineer)

This repository is structured so a junior engineer can clearly present project ownership:

- Problem framing: local-first lakehouse that mirrors production patterns without cloud spend
- Technical depth: medallion architecture, contract-based ingestion, JDBC-backed catalog checks
- Engineering maturity: CI, type checks, security scanning, and documentation discipline
- Communication quality: setup guides, architecture notes, examples, and closure evidence artifacts

## License

See `LICENSE`.
