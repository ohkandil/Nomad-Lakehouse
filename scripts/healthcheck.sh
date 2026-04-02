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
check "Iceberg REST catalog" "http://localhost:${ICEBERG_REST_PORT:-8181}/v1/config"

echo "[ok] Core service health checks passed"
