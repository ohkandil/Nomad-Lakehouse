# Architecture Overview

## Design Goals

- Lightweight local deployment
- Portable and reproducible setup
- Secure-by-default operational flow
- Modular scripts that can run independently

## Components

- MinIO: S3-compatible object store for data lake files
- PostgreSQL: JDBC-backed metadata catalog state (initial reachability validation)
- Python scripts: Bronze/Silver/Gold pipeline steps with contract-first ingestion
- DuckDB: Local analytics and Bronze/Silver/Gold table materialization
- Docker Compose: Service orchestration on a single host

## Data Flow

The pipeline uses a medallion architecture (Bronze/Silver/Gold) implemented primarily through DuckDB materialization of CSV source data:

1. `create_bronze_tables.py` validates source CSV, checks JDBC catalog backend reachability, and materializes `bronze.orders` in DuckDB.
2. `bronze_to_silver.py` applies cleaning and normalization, outputting `silver_orders.csv`.
3. `silver_to_gold.py` computes aggregated business metrics, outputting `gold_daily_revenue.csv`.

*(Note: The current architecture is designed to be Iceberg-ready with a PostgreSQL-backed JDBC catalog, but the actual data materialization currently uses DuckDB table formats.)*

## Week 2 Design Decisions

- Contract-first Bronze ingestion:
	- Contract file at `data/contracts/bronze_orders_contract.json`
	- Enforces required columns and core business constraints
- Idempotent Bronze build:
	- Uses `CREATE OR REPLACE TABLE bronze.orders`
	- Avoids manual cleanup between runs and supports rapid iteration
- Catalog readiness check:
	- Uses `CATALOG_JDBC_URI` to validate PostgreSQL backend reachability before downstream steps

## Public Release Rationale

- Reproducibility: deterministic scripts and explicit outputs
- Learnability: each stage has clear commands and expected artifacts
- Portfolio readiness: architecture narrative maps to real-world medallion data engineering practices

## Runtime Model

- Target OS: Ubuntu 24.04 LTS
- Host profile: low-resource server/homelab compatible
- Networking: LAN-only for MVP
- Security gate: script-based scan/remediation workflow per stage
