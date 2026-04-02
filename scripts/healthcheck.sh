#!/usr/bin/env bash
set -euo pipefail

check() {
  local name="$1"
  local url="$2"
  if curl -fsS "$url" >/dev/null; then
    echo "[ok] ${name}"
  else
    echo "[fail] ${name} (${url})"
    return 1
  fi
}

check "MinIO" "http://localhost:${MINIO_API_PORT:-9000}/minio/health/live"

if docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-iceberg}" -d "${POSTGRES_DB:-iceberg}" >/dev/null; then
  echo "[ok] PostgreSQL catalog backend"
else
  echo "[fail] PostgreSQL catalog backend"
  exit 1
fi

echo "[ok] Core service health checks passed"
