#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup.sql>"
  exit 1
fi

BACKUP_FILE="$1"

if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "[restore] Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

echo "[restore] Restoring catalog metadata from ${BACKUP_FILE}"
docker compose exec -T postgres psql -U "${POSTGRES_USER:-iceberg}" -d "${POSTGRES_DB:-iceberg}" <"${BACKUP_FILE}"

echo "[restore] Complete"
