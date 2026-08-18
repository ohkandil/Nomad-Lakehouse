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

The bootstrap script automates environment configuration, launches the **npm-based Setup Wizard** (in `tui/`) for environment configuration, starts core Docker services, and prepares the Python environment.

## Setup Wizard (TUI)

The setup wizard is a terminal-based configuration tool built with TypeScript, React, and [OpenTUI](https://github.com/opentui/core) v0.5+. It provides a guided interface to configure your `.env` file, ports, and credentials.

### Quick Start

```bash
cd tui
bun install
bun start
```

### Key Features

- **Keyboard-driven navigation**: Use `Enter` to proceed, `Backspace` to go back, `q` to quit.
- **Secure fields**: Passwords are masked during input.
- **Validation**: Real-time validation for ports, required fields, and credentials.
- **Persistence**: Saves progress automatically; resumes from last step if interrupted.
- **Pre-fill**: Existing `.env` values are pre-filled if found.

### Supported Platforms

- Linux (x64/ARM64)
- macOS (x64/ARM64)
- Windows (WSL2 recommended)

> **Note**: OpenTUI uses native bindings. Ensure your platform is supported by checking the [OpenTUI compatibility matrix](https://github.com/opentui/core#compatibility).

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
