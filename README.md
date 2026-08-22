# Nomad Lakehouse

<p align="center">
 <img src="docs/assets/nomad-lakehouse-logo.png" alt="Nomad Lakehouse Logo" width="260">
</p>

Local-first data lakehouse for Ubuntu servers and homelabs — with an interactive setup wizard, Bronze/Silver/Gold medallion pipeline, and a real-time admin dashboard.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ohkandil/nomad-lakehouse nomad-lakehouse
cd nomad-lakehouse

# 2. Run the bootstrap script (Ubuntu)
chmod +x scripts/*.sh
./scripts/bootstrap.sh
```

The bootstrap script will:
- Install system dependencies (Docker, Node.js, Python)
- Launch the **npm-based Setup Wizard** for environment configuration
- Start core services (MinIO, PostgreSQL)
- Prepare the Python lakehouse environment

---

## 🖥️ Setup Wizard & Service Health (npm)

The TUI is a TypeScript/React application built with [Ink](https://github.com/vadimdemedes/ink) and managed via npm in the `tui/` directory. It provides two views: a guided wizard to configure your `.env` file, ports, and credentials, and a live Service Health dashboard showing endpoint, resolved IP addresses, status, and latency for MinIO API, MinIO Console, PostgreSQL Catalog, and the Admin Dashboard.

```bash
cd tui
npm install
npm start
```

**Note:** The TUI requires Node.js 20+; it uses no native binaries. Press `[Tab]` to switch views, `[r]` to refresh health checks, `[q]` to quit.

### Admin Dashboard

<p align="center">
 <img src="docs/assets/dashboard-screenshot.png" alt="Nomad Lakehouse Admin Dashboard — overview, pipeline health, data quality, and security views" width="640">
</p>

Four-views dashboard built with FastAPI + Jinja2:
overview → pipeline health → data quality → security. Access locally at `127.0.0.1:8088` or via the Caddy HTTPS reverse proxy on your LAN.

### Stack Architecture Diagram

<p align="center">
 <img src="docs/assets/stack-diagram.png" alt="Nomad Lakehouse stack diagram — MinIO, PostgreSQL, Iceberg, DuckDB, Python scripts, FastAPI dashboard" width="640">
</p>

Medallion (Bronze → Silver → Gold) data flow over MinIO + Apache Iceberg, queried via DuckDB, monitored via the FastAPI dashboard.

---

## 💼 Why It Works On A Resume Or LinkedIn

- 📐 Shows production-style architecture in a small, explainable footprint
- 🔍 Makes the operational flow visible instead of hiding it behind a managed platform
- 🗣️ Gives you a clean story for data engineering interviews, demos, and portfolio posts
- 🧰 Hands-on with MinIO, Iceberg, DuckDB, FastAPI, Docker Compose, and shell scripting
- 🎯 Demonstrates end-to-end ownership: setup → pipeline → monitoring → security

---

## 🧰 Stack

| Layer          | Technology                 | Role                                                |
| -------------- | -------------------------- | --------------------------------------------------- |
| Object Storage | **MinIO**            | S3-compatible storage for lakehouse files           |
| Metadata       | **PostgreSQL**       | JDBC catalog backend for table state                |
| Table Format   | **Apache Iceberg**   | ACID-compliant table schema direction               |
| Query Engine   | **DuckDB**           | Fast local analytics over Bronze/Silver/Gold tables |
| Pipeline       | **Python 3**         | Ingestion, transformation, and validation scripts   |
| Dashboard      | **FastAPI + Jinja2** | Real-time operational UI with four views            |
| Orchestration  | **Docker Compose**   | Single-machine service coordination                 |
| Front Door     | **Caddy**            | HTTPS reverse proxy with basic auth                 |

---

## 🚀 Quick Start

```bash
git clone https://github.com/ohkandil/nomad-lakehouse nomad-lakehouse
cd nomad-lakehouse
cp .env.example .env
chmod +x scripts/*.sh
INSTALL_PROFILE=lakehouse ./scripts/setup_python_env.sh
source .venv/bin/activate
cd tui && npm install && npm start  # Interactive setup wizard + service health (TypeScript + Ink)
cd ..
sudo ./scripts/setup_minio.sh
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

### What the TUI provides

The TUI (`tui/`) is a TypeScript/React terminal application built on the [Ink](https://github.com/vadimdemedes/ink) library. It gives you an interactive terminal UI with:

- ✏️ **15 configuration fields** — MinIO admin credentials, S3 ports, PostgreSQL connection, bucket name, AWS region, dashboard domain/auth/upstream/CIDRs
- 🩺 **Service Health dashboard** — live status, endpoint, resolved IPs, and latency for MinIO API, MinIO Console, PostgreSQL Catalog, and the Admin Dashboard (auto-refresh every 10s)
- 💾 **Safe .env merging** — existing values are pre-filled and preserved; saving writes a merged `.env` at the repository root

When you press **S** to save, the wizard writes `.env`, validates everything, and prints a guided post-save checklist tailored to your toggle selections.

---

## 📊 Dashboard

### Local access

```bash
source .venv/bin/activate
python3 -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8088
```

| Route         | View                                               |
| ------------- | -------------------------------------------------- |
| `/`         | Overview — service health at a glance (auth-gated) |
| `/login`    | HTTP Basic auth login (admin/admin for demo)       |
| `/pipeline` | Pipeline health — Bronze/Silver/Gold run status   |
| `/quality`  | Data quality — contract adherence and row counts  |
| `/security` | Security — audit results and vulnerability status |

### Secure LAN access (Caddy + TLS + basic auth)

```bash
sudo ./scripts/install_dashboard_service.sh
set -a; source .env; set +a
sudo -E ./scripts/install_dashboard_reverse_proxy.sh
```

Then open `https://dashboard.home.arpa` from any device on your LAN.

All four dashboard views are served behind HTTPS with basic-auth credentials you configured in the TUI wizard.

---

## ✅ Features

- 🐧 Linux-first deployment (Ubuntu Server / homelab)
- 🧪 MinIO + PostgreSQL health checks and systemd auto-start
- 🪣 Bucket bootstrap and environment setup
- 📄 Bronze ingestion contract generation
- 🪄 Bronze table materialization with rerunnable `CREATE OR REPLACE`
- 🌊 Bronze → Silver → Gold starter pipeline
- 📊 Four-view admin dashboard with API-driven status
- 🔐 Security gate: `pip-audit`, Bandit, and remediation scripts
- 🤖 CI pipeline with lint (Ruff), typing (mypy), tests (pytest), and security
- 🎨 Interactive terminal-based setup wizard + service-health dashboard (TypeScript + Ink)

---

## 🔐 Security Workflow

Mandatory stage gate before committing:

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

---

## 🧪 Validation

### Week 1 — Core stack

1. `sudo ./scripts/setup_minio.sh`
2. `sudo ./scripts/healthcheck.sh`
3. `sudo ./scripts/install_systemd_service.sh`
4. Reboot and verify `nomad-lakehouse.service` auto-starts
5. `./scripts/setup_python_env.sh`
6. Run all three pipeline scripts
7. Verify outputs in `data/output/`
8. Run the security workflow and log findings
9. Record evidence in `docs/week1-closure.md`

### Week 2 — Catalog & contracts

1. Ensure services are running: `sudo ./scripts/setup_minio.sh`
2. Activate environment: `source .venv/bin/activate`
3. Run Bronze workflow: `python3 scripts/create_bronze_tables.py`
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

> Current verification evidence may vary by host environment. Treat the week-closure docs as the source of truth for your latest local validation run.

---

## 🛣️ Roadmap

- [ ] Full Iceberg table commit flow (beyond DuckDB materialization)
- [ ] Incremental ingestion with watermark tracking
- [ ] Stronger data quality contracts with automated enforcement
- [ ] Richer observability and operational diagnostics
- [ ] Near plug-and-play deployment with minimal user input

---

## 📚 Documentation Index

| Document                         | Description                        |
| -------------------------------- | ---------------------------------- |
| `docs/setup.md`                | Environment setup guide            |
| `docs/ubuntu-deploy.md`        | Full deployment runbook            |
| `docs/architecture.md`         | Architecture overview              |
| `docs/examples.md`             | Pipeline and query examples        |
| `docs/admin-dashboard-plan.md` | Dashboard implementation plan      |
| `docs/admin-dashboard.md`      | Dashboard usage and endpoints      |
| `docs/onboarding.md`           | Onboarding guide for new engineers |
| `docs/week1-closure.md`        | Week 1 validation evidence         |
| `docs/week2-closure.md`        | Week 2 validation evidence         |
| `PROJECT_PLAN.md`              | Long-term implementation roadmap   |
| `Local_Lakehouse_MVP.md`       | Original MVP specification         |

---

## 🗂️ Repository Layout

```text
.
├── docker-compose.yml        # MinIO + PostgreSQL orchestration
├── pyproject.toml            # Python deps, tool config, metadata
├── scripts/
│   ├── create_bronze_tables.py   # Bronze ingestion + contract
│   ├── bronze_to_silver.py       # Silver transformation
│   ├── silver_to_gold.py         # Gold aggregation
│   ├── setup_minio.sh            # MinIO + PostgreSQL launcher
│   ├── setup_python_env.sh       # Virtual env creation
│   ├── healthcheck.sh            # Service health probes
│   └── security_scan.sh          # pip-audit + Bandit runner
├── tui/
│   ├── src/                      # TypeScript TUI source (wizard + service health)
│   └── package.json              # npm deps (Ink, React)
├── dashboard/
│   ├── app.py                    # FastAPI application
│   ├── health_sources.py         # Service health collectors
│   ├── pipeline_sources.py       # Pipeline status collectors
│   ├── security_sources.py       # Security audit collectors
│   ├── templates/                # Jinja2 HTML templates
│   └── static/                   # Dashboard assets
├── docs/
│   ├── assets/                   # Logo, screenshots, diagrams
│   ├── architecture.md
│   └── ...                       # Full documentation
├── data/
│   ├── contracts/                # Versioned ingestion contracts
│   ├── output/                   # DuckDB database files
│   └── sample/                   # Sample source data
└── tests/
```

---

## 👤 Portfolio Notes

This repository is structured so a junior engineer can clearly present project ownership:

- **Problem framing** — local-first lakehouse that mirrors production patterns without cloud spend
- **Technical depth** — medallion architecture, contract-based ingestion, JDBC-backed catalog connectivity, interactive TUI wizard
- **Engineering maturity** — CI, type checks, security scanning, and documentation discipline
- **Communication quality** — setup guides, architecture notes, examples, screenshot placeholders, and closure evidence artifacts

---

## 📄 License

See `LICENSE`.
