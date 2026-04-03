# Week 1 Closure Checklist

Use this file to record objective completion evidence for Week 1.

## 1) Core Services Up

Command:

```bash
docker compose ps
```

Evidence:

- Date/time:
- `minio` status:
- `postgres` status:
- `minio-init` status:

## 2) Health Checks

Commands:

```bash
sudo ./scripts/healthcheck.sh
curl -fsS http://localhost:9000/minio/health/live
docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-iceberg}" -d "${POSTGRES_DB:-iceberg}"
```

Evidence:

- Date/time:
- Healthcheck result:
- MinIO endpoint result:
- PostgreSQL readiness result:

## 3) Systemd Auto-Start Configured

Commands:

```bash
sudo ./scripts/install_systemd_service.sh
systemctl is-enabled nomad-lakehouse.service
systemctl status --no-pager nomad-lakehouse.service
```

Evidence:

- Date/time:
- `is-enabled` output:
- Current status:

## 4) Reboot Validation

Commands:

```bash
sudo reboot
# reconnect after reboot
systemctl status --no-pager nomad-lakehouse.service
docker compose ps
sudo ./scripts/healthcheck.sh
```

Evidence:

- Date/time of reboot:
- Service state after reboot:
- Compose states after reboot:
- Healthcheck after reboot:

## 5) Journal Diagnostics

Commands:

```bash
journalctl -u nomad-lakehouse.service -n 200 --no-pager
journalctl -u docker.service -n 200 --no-pager
docker compose logs --tail=200 minio postgres
```

Evidence:

- Date/time:
- Any warnings/errors:
- Follow-up actions:

## 6) Minimum Hardening Validation

Command:

```bash
sudo ./scripts/hardening_checklist.sh
```

Evidence:

- Date/time:
- Checklist warnings:
- Remediations applied:
