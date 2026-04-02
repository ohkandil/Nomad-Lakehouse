# Nomad Lakehouse

Production-grade local lakehouse architecture running on Ubuntu Linux with open-source components.

## Why This Project

This repository demonstrates modern lakehouse patterns without cloud spend:

- MinIO as S3-compatible object storage
- Apache Iceberg REST Catalog for table metadata APIs
- PostgreSQL for catalog metadata persistence
- Python medallion starter pipelines (Bronze -> Silver -> Gold)
- Docker Compose for reproducible local/server deployment

## Current Stage

Stage 1 (Foundation) is in progress and includes:

- Linux-first (Ubuntu 24.04 LTS) deployment baseline
- `docker-compose.yml` with MinIO + PostgreSQL + Iceberg REST Catalog
- Bash operational scripts for setup, health, backup/restore, and security scanning
- Starter transformation scripts and sample dataset
- CI workflow with lint, type-check, tests, and security checks

## Quick Start (Ubuntu 24.04)

1. Clone and configure environment

```bash
git clone <repo-url> nomad-lakehouse
cd nomad-lakehouse
cp .env.example .env
# Rotate passwords in .env before first run
```

1. Start core services

```bash
docker compose up -d minio postgres iceberg-rest minio-init
```

1. Run health checks

```bash
./scripts/healthcheck.sh
```

1. Run starter data flow

```bash
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

## Stage Security Gate (Mandatory)

After each implementation stage:

1. Run CVE/dependency and security checks

```bash
./scripts/security_scan.sh
```

1. Record findings and remediations in README stage notes.
1. Do not mark a stage complete until HIGH/CRITICAL issues are triaged.

CI also enforces security-related checks:

- `pip-audit` for dependency vulnerabilities
- `bandit` for Python security linting

### Stage 1 Security Findings (2026-04-02)

- Quality gates: `ruff`, `mypy`, and `pytest` passed.
- `bandit` result: no issues identified in `scripts`.
- `pip-audit` reported 4 vulnerabilities in this local Python environment.
- Findings: `cryptography` 46.0.5 -> 46.0.6, `pygments` 2.19.2 -> 2.20.0, `tornado` 6.5.4 -> 6.5.5 (GHSA-78cv-mqj4-43f7, CVE-2026-31958)

Remediation policy:

- Use project-scoped virtual environments for repeatable scans.
- Upgrade vulnerable dependencies in the execution environment before production deployment.
- Re-run `python -m pip_audit` at the end of each stage and update this section.

## Stage 1 Validation On Your Local Server

Use this checklist on your Ubuntu server to validate Stage 1 end to end.

### 1. Prepare host packages

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
```

### 2. Install Docker Engine and Compose plugin

Follow Docker official Ubuntu instructions, then verify:

```bash
docker --version
docker compose version
```

### 3. Clone and configure project

```bash
git clone <repo-url> nomad-lakehouse
cd nomad-lakehouse
cp .env.example .env
```

Edit `.env` and rotate at minimum:

- `MINIO_ROOT_PASSWORD`
- `POSTGRES_PASSWORD`

### 4. Make scripts executable

```bash
chmod +x scripts/*.sh
```

### 5. Start Stage 1 services

```bash
./scripts/setup_minio.sh
docker compose ps
```

Expected running services:

- `minio`
- `postgres`
- `iceberg-rest`

### 6. Validate health endpoints

```bash
./scripts/healthcheck.sh
curl -fsS http://localhost:9000/minio/health/live
curl -fsS http://localhost:8181/v1/config
```

### 7. Run starter data flow

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python scripts/create_bronze_tables.py
python scripts/bronze_to_silver.py
python scripts/silver_to_gold.py
```

Check outputs:

```bash
ls -lh data/output
cat data/output/gold_daily_revenue.csv
```

### 8. Run mandatory stage security checks

```bash
./scripts/security_scan.sh
python -m pip_audit
python -m bandit -r scripts
```

### 9. Run hardening audit checklist

```bash
sudo ./scripts/hardening_checklist.sh
```

### 10. Stage 1 pass criteria

- Core services are healthy and stay up after restart.
- Starter pipeline completes and writes Silver/Gold outputs.
- Security scan and bandit run successfully.
- Any CVEs are logged with remediation actions in this README.

## Repository Layout

```text
.
├── .github/workflows/ci.yml
├── docker-compose.yml
├── pyproject.toml
├── scripts/
│   ├── setup_minio.sh
│   ├── healthcheck.sh
│   ├── security_scan.sh
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
│   └── examples.md
├── data/sample/orders.csv
└── tests/test_transformations.py
```

## Documentation Standards

Code and operational documentation follows these rules:

- Keep setup steps executable and copy-paste friendly
- Document assumptions, inputs, outputs, and failure modes for scripts
- Update README whenever stage scope, commands, or architecture changes
- Keep security posture visible (hardening checklist and security gate status)

## Security and Hardening

Minimum server hardening checklist is tracked in plan and supported by:

- `scripts/hardening_checklist.sh` (audit helper)
- `docs/ubuntu-deploy.md` (deployment runbook)

Recommended baseline:

- SSH key-only auth, root SSH disabled
- UFW LAN-only rules for required ports
- fail2ban enabled
- unattended security updates enabled

## Implementation Plan

Primary roadmap is tracked in:

- `PROJECT_PLAN.md`

## License

See `LICENSE`.
