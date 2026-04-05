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
cp .env.example .env
chmod +x scripts/*.sh
```

Edit `.env` and rotate at least:

- `MINIO_ROOT_PASSWORD`
- `POSTGRES_PASSWORD`

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
INSTALL_PROFILE=lakehouse sudo ./scripts/setup_python_env.sh
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

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
python3 -m pip_audit
python3 -m bandit -r scripts
```

If vulnerabilities are reported:

```bash
sudo ./scripts/remediate_python_vulns.sh
python3 -m pip_audit
```

## Ports

- MinIO API: `9000`
- MinIO Console: `9001`
- PostgreSQL: `5432`

## Release-Readiness Notes

- Keep `.env.example` values generic and never commit real credentials
- Keep setup steps deterministic and copy-paste runnable
- For every behavior change, update `README.md`, `docs/examples.md`, and closure checklist docs in the same PR
