# Query and Pipeline Examples

## 1. Run Starter Pipeline

```bash
sudo ./scripts/setup_python_env.sh
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

## 2. Inspect Outputs

```bash
cat data/output/silver_orders.csv
cat data/output/gold_daily_revenue.csv
```

## 3. Service Verification

```bash
sudo ./scripts/healthcheck.sh
docker compose ps
```

## 4. Security Verification

```bash
sudo ./scripts/security_scan.sh
python3 -m pip_audit
python3 -m bandit -r scripts
```
