# Ubuntu Deployment Runbook

## Service Management

Start and stop:

```bash
docker compose up -d
docker compose down
```

Logs:

```bash
docker compose logs -f minio
docker compose logs -f postgres
```

Health:

```bash
sudo ./scripts/healthcheck.sh
```

## Auto-Start On Reboot (systemd)

Install and enable service:

```bash
sudo ./scripts/install_systemd_service.sh
systemctl is-enabled nomad-lakehouse.service
```

Reboot validation:

```bash
sudo reboot
# reconnect after reboot
systemctl status --no-pager nomad-lakehouse.service
docker compose ps
sudo ./scripts/healthcheck.sh
```

## Diagnostics (journalctl + container logs)

```bash
journalctl -u nomad-lakehouse.service -n 200 --no-pager
journalctl -u docker.service -n 200 --no-pager
docker compose logs --tail=200 minio postgres
```

## Metadata Backup and Restore

Backup:

```bash
sudo ./scripts/backup_metadata.sh ./backups
```

Restore:

```bash
sudo ./scripts/restore_metadata.sh ./backups/<file>.sql
```

## Minimum Hardening

- SSH key auth only, root login disabled
- UFW allow only required LAN ports
- fail2ban enabled
- unattended upgrades enabled
- Rotate default credentials before first shared use

## Stage Security Procedure

Run after each implementation stage:

```bash
sudo ./scripts/security_scan.sh
```

Record results in README stage notes.
Capture evidence in:

- `docs/week1-closure.md` for foundation/runtime checks
- `docs/week2-closure.md` for Bronze contract and queryability checks

## Week 2 Operational Validation

```bash
source .venv/bin/activate
python3 scripts/create_bronze_tables.py
python3 - <<'PY'
import duckdb
con = duckdb.connect("data/output/lakehouse.duckdb")
print(con.execute("SELECT COUNT(*) FROM bronze.orders").fetchall())
PY
```
