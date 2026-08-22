#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_PATH="${PROJECT_ROOT}/configs/systemd/nomad-dashboard.service.template"
UNIT_PATH="/etc/systemd/system/nomad-dashboard.service"

if [[ ! -f "${PROJECT_ROOT}/.venv/bin/python3" ]]; then
  echo "[dashboard-service] Missing ${PROJECT_ROOT}/.venv/bin/python3"
  echo "[dashboard-service] Run scripts/setup_python_env.sh first"
  exit 1
fi

if [[ ! -f "${TEMPLATE_PATH}" ]]; then
  echo "[dashboard-service] Missing template: ${TEMPLATE_PATH}"
  exit 1
fi

echo "[dashboard-service] Rendering unit file"
sed "s|{{PROJECT_ROOT}}|${PROJECT_ROOT}|g" "${TEMPLATE_PATH}" >"${UNIT_PATH}"

echo "[dashboard-service] Reloading systemd daemon"
systemctl daemon-reload

echo "[dashboard-service] Enabling service"
systemctl enable nomad-dashboard.service

echo "[dashboard-service] Restarting service"
systemctl restart nomad-dashboard.service

echo "[dashboard-service] Service status"
systemctl status --no-pager nomad-dashboard.service

echo "[dashboard-service] Completed"
