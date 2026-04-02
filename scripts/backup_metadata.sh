#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${1:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_FILE="${BACKUP_DIR}/iceberg_catalog_${TIMESTAMP}.sql"

mkdir -p "${BACKUP_DIR}"

echo "[backup] Exporting PostgreSQL metadata to ${OUT_FILE}"
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-iceberg}" "${POSTGRES_DB:-iceberg}" >"${OUT_FILE}"

echo "[backup] Complete"
