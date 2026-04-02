# Architecture Overview

## Components
- MinIO: S3-compatible object storage for Iceberg files
- Iceberg REST Catalog: table metadata API
- PostgreSQL: catalog metadata backend
- Python scripts: medallion pipeline starter
- DuckDB (tools profile): local analytics entry point

## Data Flow
1. Raw CSV is validated by `create_bronze_tables.py`.
2. `bronze_to_silver.py` cleans and standardizes rows.
3. `silver_to_gold.py` creates daily aggregate metrics.

## Deployment Target
- Ubuntu 24.04 LTS
- Docker Compose as runtime orchestrator
- LAN-only service exposure for MVP
