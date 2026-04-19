#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

if [[ ! -f .env ]]; then
  echo "[setup] .env not found. Copying from .env.example"
  cp .env.example .env
  echo "[setup] Please edit .env and rotate passwords before production use."
fi

echo "[setup] Starting core services"
docker compose up -d minio postgres minio-init

echo "[setup] Waiting for MinIO and PostgreSQL health"
for _ in {1..30}; do
  if curl -fsS "http://localhost:${MINIO_API_PORT:-9000}/minio/health/live" >/dev/null \
    && docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-iceberg}" -d "${POSTGRES_DB:-iceberg}" >/dev/null; then
    echo "[setup] Services are healthy"
    exit 0
  fi
  sleep 2
done

echo "[setup] Timed out waiting for services"
exit 1
