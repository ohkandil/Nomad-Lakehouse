# Query and Pipeline Examples

## Run Starter Pipeline
```bash
python3 scripts/create_bronze_tables.py
python3 scripts/bronze_to_silver.py
python3 scripts/silver_to_gold.py
```

## Inspect Outputs
```bash
cat data/output/silver_orders.csv
cat data/output/gold_daily_revenue.csv
```

## Service Verification
```bash
sudo ./scripts/healthcheck.sh
docker compose ps
```

## Security Verification
```bash
sudo ./scripts/security_scan.sh
```
