# Query and Pipeline Examples

## 1. Run Starter Pipeline

```bash
INSTALL_PROFILE=lakehouse sudo ./scripts/setup_python_env.sh
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

## 2. Inspect Bronze Contract

```bash
cat data/contracts/bronze_orders_contract.json
```

## 3. Query Bronze Table (DuckDB)

```bash
python3 - <<'PY'
import duckdb
con = duckdb.connect("data/output/lakehouse.duckdb")
print(con.execute("SELECT order_date, COUNT(*) AS orders, SUM(amount) AS amount FROM bronze.orders GROUP BY 1 ORDER BY 1").fetchdf())
PY
```

## 4. Inspect Silver and Gold Outputs

```bash
cat data/output/silver_orders.csv
cat data/output/gold_daily_revenue.csv
```

## 5. Service Verification

```bash
sudo ./scripts/healthcheck.sh
docker compose ps
```

## 6. Security Verification

```bash
sudo ./scripts/security_scan.sh
python3 -m pip_audit
python3 -m bandit -r scripts
```
