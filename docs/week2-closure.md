# Week 2 Closure Checklist

Use this file to record objective completion evidence for Week 2.

Keep entries environment-specific and update them each time you run validation.

## 1) JDBC Catalog Backend Reachability

Command:

```bash
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
```

Evidence:

- Date/time:
- `CATALOG_JDBC_URI` value used:
- Reachability message from script:
- Follow-up action if failed:

## 2) Bronze Ingestion Contract Generated

Command:

```bash
cat data/contracts/bronze_orders_contract.json
```

Evidence:

- Date/time:
- Contract version:
- Contract required columns count:
- Notes:

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

- Date/time:
- Row count:
- Sample rows verified:

## 4) Rerunnable Without Manual Cleanup

Commands:

```bash
python3 scripts/create_bronze_tables.py
python3 scripts/create_bronze_tables.py
```

Evidence:

- Date/time:
- First run result:
- Second run result:
- Manual cleanup required? (yes/no):

## 5) Integration With Silver and Gold

Commands:

```bash
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

Evidence:

- Date/time:
- Silver output row count:
- Gold output row count:
- Notes:
