#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_PATH="${PROJECT_ROOT}/configs/systemd/nomad-lakehouse.service.template"
UNIT_PATH="/etc/systemd/system/nomad-lakehouse.service"

if [[ ! -f "${TEMPLATE_PATH}" ]]; then
  echo "[systemd-install] Missing template: ${TEMPLATE_PATH}"
  exit 1
fi

echo "[systemd-install] Rendering unit file"
sed "s|{{PROJECT_ROOT}}|${PROJECT_ROOT}|g" "${TEMPLATE_PATH}" >"${UNIT_PATH}"

echo "[systemd-install] Reloading systemd daemon"
systemctl daemon-reload

echo "[systemd-install] Enabling nomad-lakehouse service"
systemctl enable nomad-lakehouse.service

echo "[systemd-install] Starting nomad-lakehouse service"
systemctl restart nomad-lakehouse.service

echo "[systemd-install] Service status"
systemctl status --no-pager nomad-lakehouse.service

echo "[systemd-install] Completed"
