# Setup Guide (Ubuntu 24.04 LTS)

## Prerequisites

- Ubuntu 24.04 LTS
- Docker Engine with Compose plugin
- Python 3.11+
- `curl`, `git`

## Installation

```bash
git clone <repo-url> nomad-lakehouse
cd nomad-lakehouse
chmod +x scripts/*.sh
./scripts/bootstrap.sh
```

The bootstrap script automates environment configuration, launches the **npm-based TUI** (in `tui/`) for environment configuration and service-health monitoring, starts core Docker services, and prepares the Python environment.

## Setup Wizard & Service Health (TUI)

The TUI is a TypeScript/React application built with [Ink](https://github.com/vadimdemedes/ink) and managed via npm in the `tui/` directory. It has two views:

- **Setup Wizard** (`w`): guided terminal interface to configure your `.env` file, ports, and credentials. Existing `.env` values are pre-filled and preserved; saving writes a merged `.env` at the repository root.
- **Service Health** (`d`): live dashboard of MinIO API, MinIO Console, PostgreSQL Catalog, and Admin Dashboard — showing endpoint host:port, resolved IP addresses, status, latency, and remediation hints. Auto-refreshes every 10 seconds (`r` refreshes immediately).

Keybindings: `[Tab]`/`[Shift+Tab]` switch views, `[r]` refresh health checks, `[q]` quit.

```bash
cd tui
npm install
npm start
```

**Note:** The TUI requires Node.js 20+ and no native binaries. If checks show `unresolved` IPs or `fail` statuses, ensure Docker services are up (`docker compose ps`).

## Start Services

```bash
sudo ./scripts/setup_minio.sh
docker compose ps
```

## Configure Auto-Start (systemd)

```bash
sudo ./scripts/install_systemd_service.sh
systemctl is-enabled nomad-lakehouse.service
```

## Verify Service Health

```bash
sudo ./scripts/healthcheck.sh
curl -fsS http://localhost:9000/minio/health/live
docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-iceberg}" -d "${POSTGRES_DB:-iceberg}"
```

## Run Starter Pipeline

```bash
INSTALL_PROFILE=lakehouse ./scripts/setup_python_env.sh
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

## Run Admin Dashboard

```bash
source .venv/bin/activate
python3 -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8088
```

Verify dashboard API:

```bash
curl -fsS http://127.0.0.1:8088/health
curl -fsS http://127.0.0.1:8088/api/status/overview   # returns HTML page
curl -fsS http://127.0.0.1:8088/api/status/pipeline   # returns HTML page
```

## Secure LAN Dashboard Access (Reverse Proxy + TLS)

Install the dashboard systemd service and Caddy reverse proxy:

```bash
sudo ./scripts/install_dashboard_service.sh
set -a; source .env; set +a
sudo -E ./scripts/install_dashboard_reverse_proxy.sh
```

Verify from server:

```bash
curl -k -u "${DASHBOARD_AUTH_USER}":"${DASHBOARD_AUTH_PASSWORD}" "https://${DASHBOARD_DOMAIN}/api/status/overview"
systemctl status --no-pager nomad-dashboard.service caddy
```

Notes:

- Keep dashboard upstream bound to `127.0.0.1:8088`.
- `tls internal` is used for local SSL certificates.
- Import/trust Caddy local CA on client devices to remove browser certificate warnings.

## Week 2 Bronze Verification

Validate that the Bronze workflow produced both contract and table artifacts:

```bash
cat data/contracts/bronze_orders_contract.json

python3 - <<'PY'
import duckdb
con = duckdb.connect("data/output/lakehouse.duckdb")
print(con.execute("SELECT COUNT(*) AS rows FROM bronze.orders").fetchall())
print(con.execute("DESCRIBE bronze.orders").fetchdf())
PY
```

Expected behavior:

- `create_bronze_tables.py` validates source contract constraints
- JDBC catalog target from `CATALOG_JDBC_URI` is checked for connectivity
- `bronze.orders` is rebuilt idempotently on each run (`CREATE OR REPLACE`)

## Security Gate

```bash
sudo ./scripts/security_scan.sh
python3 -m pip_audit --skip-editable --ignore-vuln CVE-2026-3219
python3 -m bandit -r scripts
```

If vulnerabilities are reported:

```bash
./scripts/remediate_python_vulns.sh
python3 -m pip_audit --skip-editable --ignore-vuln CVE-2026-3219
```

## Ports

- MinIO API: `9000`
- MinIO Console: `9001`
- PostgreSQL: `5432`

## Release-Readiness Notes

- Keep `.env.example` values generic and never commit real credentials
- Keep setup steps deterministic and copy-paste runnable
- For every behavior change, update `README.md`, `docs/examples.md`, and closure checklist docs in the same PR
