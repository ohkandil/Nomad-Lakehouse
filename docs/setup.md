# Setup Guide (Ubuntu 24.04 LTS)

## Prerequisites

- Ubuntu 24.04 LTS server
- Docker Engine + Docker Compose plugin
- Python 3.11+
- curl

## 1. Clone and Configure

```bash
git clone <repo-url> nomad-lakehouse
cd nomad-lakehouse
cp .env.example .env
# Edit .env and rotate passwords
```

## 2. Start Core Services

```bash
docker compose up -d minio postgres minio-init
```

## 3. Verify Health

```bash
sudo ./scripts/healthcheck.sh
```

## 4. Run Data Pipeline (Local CSV Starter)

```bash
sudo ./scripts/setup_python_env.sh
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

## 5. Run Security Checks (End of Stage)

```bash
sudo ./scripts/security_scan.sh
sudo ./scripts/remediate_python_vulns.sh
```

## Notes

- MinIO API: port 9000
- MinIO Console: port 9001
- PostgreSQL catalog backend: port 5432
