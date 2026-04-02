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
- rotate default credentials before first shared use

## Stage Security Procedure
Run after each implementation stage:
```bash
sudo ./scripts/security_scan.sh
```
Record results in README stage notes.
