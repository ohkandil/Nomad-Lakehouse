#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

if [[ ! -d ".venv" ]]; then
  echo "[dashboard] .venv not found; run scripts/setup_python_env.sh first"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

HOST="${DASHBOARD_HOST:-127.0.0.1}"
PORT="${DASHBOARD_PORT:-8088}"

echo "[dashboard] starting on http://${HOST}:${PORT}"
python3 -m uvicorn dashboard.app:app --host "${HOST}" --port "${PORT}" --reload
