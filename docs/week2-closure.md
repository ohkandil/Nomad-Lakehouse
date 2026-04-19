# Week 2 Closure Checklist

Use this file to record objective completion evidence for Week 2.

## 1) JDBC Catalog Backend Reachability

Command:

```bash
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
```

Evidence:

- Date/time: 2026-04-19 15:49:00 +02:00
- `CATALOG_JDBC_URI` value used: Not executed (environment not ready)
- Reachability message from script: Not available; Docker daemon is not running, and no PostgreSQL listener is reachable on `localhost:5432`
- Follow-up action if failed: Start Docker Desktop or another Docker engine, run `cp .env.example .env`, then `docker compose up -d postgres` and rerun `python3 scripts/create_bronze_tables.py`

## 2) Bronze Ingestion Contract Generated

Command:

```bash
cat data/contracts/bronze_orders_contract.json
```

Evidence:

- Date/time: 2026-04-19 15:54:00 +02:00
- Contract version: Not available (file not generated yet)
- Contract required columns count: Not available
- Notes: `data/contracts/bronze_orders_contract.json` is not present because the Bronze script did not run to completion without catalog backend reachability

## 3) Bronze Table Created and Queryable

Command:

```bash
python3 - <<'PY'
import duckdb
con = duckdb.connect("data/output/lakehouse.duckdb")
print(con.execute("SELECT COUNT(*) FROM bronze.orders").fetchall())
print(con.execute("SELECT * FROM bronze.orders ORDER BY order_id LIMIT 5").fetchdf())
PY
```

Evidence:

- Date/time: 2026-04-19 15:54:00 +02:00
- Row count: Not available (Bronze DuckDB table not materialized in this environment)
- Sample rows verified: No

## 4) Rerunnable Without Manual Cleanup

Commands:

```bash
python3 scripts/create_bronze_tables.py
python3 scripts/create_bronze_tables.py
```

Evidence:

- Date/time: 2026-04-19 15:54:00 +02:00
- First run result: Not executed (catalog backend unavailable)
- Second run result: Not executed
- Manual cleanup required? (yes/no): Not assessed

## 5) Integration With Silver and Gold

Commands:

```bash
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

Evidence:

- Date/time: 2026-04-19 15:50:17 +02:00
- Silver output row count: 6 (`[silver] Wrote 6 rows to data\\output\\silver_orders.csv (dropped 0)`)
- Gold output row count: 3 (`[gold] Wrote 3 rows to data\\output\\gold_daily_revenue.csv`)
- Notes: Gold aggregation preview:

```text
order_date  total_revenue  order_count
2026-03-28         200.50            2
2026-03-29         255.90            2
2026-03-30         115.74            2
```
