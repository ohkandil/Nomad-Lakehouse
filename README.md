# Nomad Lakehouse

<p align="center">
 <img src="docs/assets/nomad-lakehouse-logo.png" alt="Nomad Lakehouse Logo" width="260">
</p>

Local-first data lakehouse for Ubuntu servers and homelabs.

Nomad Lakehouse is a portfolio-ready project that demonstrates Bronze/Silver/Gold data engineering patterns without cloud overhead. It combines open-source storage, metadata, analytics, and a FastAPI dashboard into a reproducible, script-driven workflow.

## ✨ At a Glance

- 🏠 Local-first lakehouse for homelabs and Ubuntu servers
- 🔁 Bronze/Silver/Gold pipeline with contract-based ingestion
- 🧱 MinIO, PostgreSQL, DuckDB, Python, and FastAPI
- 🛠️ Docker Compose plus shell scripts for repeatable operations
- 🔒 Security, validation, and documentation baked into the repo

## 💼 Why It Works Well On A Resume Or LinkedIn

- 📐 Shows production-style architecture in a small, explainable footprint
- 🔍 Makes the operational flow visible instead of hiding it behind a managed platform
- 🗣️ Gives you a clean story for data engineering interviews, demos, and portfolio posts

## 🧰 Stack

- MinIO: S3-compatible object storage for local data lake files
- PostgreSQL: JDBC metadata backend for catalog state
- Apache Iceberg path: modern table-format direction for ACID and versioned data patterns
- Python 3: portable pipeline and validation scripts
- DuckDB: fast local query engine for analytics and verification
- FastAPI dashboard: interactive operational UI for health and pipeline monitoring
- Docker Compose: reproducible service orchestration on a single machine

## 🚀 Quick Start

```bash
git clone https://github.com/ohkandil/nomad-lakehouse nomad-lakehouse
cd nomad-lakehouse
cp .env.example .env
python3 scripts/configure_setup_tui.py
chmod +x scripts/*.sh
sudo ./scripts/setup_minio.sh
INSTALL_PROFILE=lakehouse ./scripts/setup_python_env.sh
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

The first-setup wizard now lets you:

- set and validate credentials and service ports
- customize dashboard reverse-proxy settings (`DASHBOARD_*`)
- choose setup preferences (stack, Python env, pipeline, services)
- receive a guided post-save checklist for stack startup and dashboard access

## 📊 Dashboard

Run the dashboard locally:

```bash
source .venv/bin/activate
python3 -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8088
```

Open:

- [http://127.0.0.1:8088/](http://127.0.0.1:8088/)
- [http://127.0.0.1:8088/pipeline](http://127.0.0.1:8088/pipeline)
- [http://127.0.0.1:8088/quality](http://127.0.0.1:8088/quality)
- [http://127.0.0.1:8088/security](http://127.0.0.1:8088/security)

Secure LAN access with reverse proxy, auth, and TLS:

```bash
sudo ./scripts/install_dashboard_service.sh
set -a; source .env; set +a
sudo -E ./scripts/install_dashboard_reverse_proxy.sh
```

Then open `https://dashboard.home.arpa` from your LAN device.

## ✅ What It Includes

- 🐧 Linux-first deployment baseline
- 🧪 MinIO and PostgreSQL services with health checks
- 🪣 Bucket bootstrap (`minio-init`) and environment bootstrap scripts
- 📄 Bronze ingestion contract generation (`data/contracts/bronze_orders_contract.json`)
- 🪄 Bronze table materialization in DuckDB (`bronze.orders`) with rerunnable `CREATE OR REPLACE` semantics
- 🌊 Bronze -> Silver -> Gold starter pipeline
- 🤖 CI with lint, typing, tests, and security checks

## 🌟 Week 2 Highlights

- 🔗 Catalog backend connectivity validation: `create_bronze_tables.py` validates JDBC target reachability from `CATALOG_JDBC_URI`
- ♻️ Repeatable Bronze setup: reruns update the same `bronze.orders` table without manual cleanup
- 📑 Contract-first ingestion: schema and constraints exported as a versioned JSON contract
- 🧾 Recruiter-friendly evidence path: closure checklist and explicit verification commands

Current verification evidence may vary by host environment. Treat `docs/week2-closure.md` as the source of truth for your latest local validation run.

## 🔐 Security Workflow

Mandatory stage gate:

```bash
sudo ./scripts/security_scan.sh
python3 -m pip_audit --skip-editable --ignore-vuln CVE-2026-3219
python3 -m bandit -r scripts
```

If vulnerabilities are found:

```bash
./scripts/remediate_python_vulns.sh
python3 -m pip_audit --skip-editable --ignore-vuln CVE-2026-3219
```

## 🧪 Validation

Stage 1:

1. `sudo ./scripts/setup_minio.sh`
2. `sudo ./scripts/healthcheck.sh`
3. `sudo ./scripts/install_systemd_service.sh`
4. Reboot the host and verify `nomad-lakehouse.service` auto-starts
5. `./scripts/setup_python_env.sh`
6. Run all three pipeline scripts
7. Verify outputs in `data/output/`
8. Run the security workflow and log findings
9. Record evidence in `docs/week1-closure.md`

Week 2:

1. Ensure services are running: `sudo ./scripts/setup_minio.sh`
2. Activate the environment: `source .venv/bin/activate`
3. Run the Bronze workflow: `python3 scripts/create_bronze_tables.py`
4. Verify the generated contract: `cat data/contracts/bronze_orders_contract.json`
5. Verify the Bronze table is queryable:

```bash
python3 - <<'PY'
import duckdb

con = duckdb.connect("data/output/lakehouse.duckdb")
print(con.execute("SELECT COUNT(*) AS rows FROM bronze.orders").fetchall())
print(con.execute("SELECT * FROM bronze.orders ORDER BY order_id LIMIT 5").fetchdf())
PY
```

1. Record evidence in `docs/week2-closure.md`

## 🛣️ Next Steps

- Expand from Bronze contract and DuckDB table materialization to full Iceberg table commit flow
- Add incremental ingestion and stronger data quality contracts
- Add richer observability and operational diagnostics
- Improve onboarding toward near plug-and-play deployment

## 📚 Documentation Index

- Setup guide: `docs/setup.md`
- Deployment runbook: `docs/ubuntu-deploy.md`
- Architecture summary: `docs/architecture.md`
- Pipeline and query examples: `docs/examples.md`
- Admin dashboard implementation plan: `docs/admin-dashboard-plan.md`
- Admin dashboard documentation: `docs/admin-dashboard.md`
- Week 1 closure evidence: `docs/week1-closure.md`
- Week 2 closure evidence: `docs/week2-closure.md`
- Implementation roadmap: `PROJECT_PLAN.md`

## 🗂️ Repository Layout

```text
.
├── docker-compose.yml
├── pyproject.toml
├── dashboard/
├── scripts/
├── docs/
├── data/
└── tests/
```

## 👤 Portfolio Notes

This repository is structured so a junior engineer can clearly present project ownership:

- Problem framing: local-first lakehouse that mirrors production patterns without cloud spend
- Technical depth: medallion architecture, contract-based ingestion, JDBC-backed catalog checks
- Engineering maturity: CI, type checks, security scanning, and documentation discipline
- Communication quality: setup guides, architecture notes, examples, and closure evidence artifacts

## 📄 License

See `LICENSE`.
