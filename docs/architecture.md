# Architecture Overview

## Design Goals

- Lightweight local deployment
- Portable and reproducible setup
- Secure-by-default operational flow
- Modular scripts that can run independently

## Components

- MinIO: S3-compatible object store for data lake files
- PostgreSQL: JDBC-backed metadata catalog state
- Python scripts: Bronze/Silver/Gold pipeline steps
- DuckDB: optional local analytics entry point
- Docker Compose: service orchestration on a single host

## Data Flow

1. `create_bronze_tables.py` validates incoming source data.
1. `bronze_to_silver.py` applies cleaning and normalization.
1. `silver_to_gold.py` computes aggregated business metrics.

## Runtime Model

- Target OS: Ubuntu 24.04 LTS
- Host profile: low-resource server/homelab compatible
- Networking: LAN-only for MVP
- Security gate: script-based scan/remediation workflow per stage
