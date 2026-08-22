#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_PATH="${PROJECT_ROOT}/configs/caddy/dashboard.Caddyfile.template"
CADDYFILE_PATH="/etc/caddy/Caddyfile"

if [[ ! -f "${TEMPLATE_PATH}" ]]; then
  echo "[proxy-install] Missing template: ${TEMPLATE_PATH}"
  exit 1
fi

DASHBOARD_DOMAIN="${DASHBOARD_DOMAIN:-dashboard.home.arpa}"
DASHBOARD_UPSTREAM="${DASHBOARD_UPSTREAM:-127.0.0.1:8088}"
DASHBOARD_AUTH_USER="${DASHBOARD_AUTH_USER:-admin}"
DASHBOARD_ALLOWED_CIDRS="${DASHBOARD_ALLOWED_CIDRS:-192.168.0.0/16 10.0.0.0/8 172.16.0.0/12}"
DASHBOARD_AUTH_HASH="${DASHBOARD_AUTH_HASH:-}"
DASHBOARD_AUTH_PASSWORD="${DASHBOARD_AUTH_PASSWORD:-}"

if ! command -v caddy >/dev/null 2>&1; then
  echo "[proxy-install] Installing caddy"
  apt-get update
  apt-get install -y caddy
fi

if [[ -z "${DASHBOARD_AUTH_HASH}" ]]; then
  if [[ -z "${DASHBOARD_AUTH_PASSWORD}" ]]; then
    DASHBOARD_AUTH_PASSWORD="$(LC_ALL=C tr -dc 'A-Za-z0-9!@#$%^&*()-_=+' </dev/urandom | head -c 24)"
    echo "[proxy-install] Generated password for ${DASHBOARD_AUTH_USER}: ${DASHBOARD_AUTH_PASSWORD}"
    echo "[proxy-install] Save it now. It will not be shown again after script exit."
  fi
  DASHBOARD_AUTH_HASH="$(caddy hash-password --plaintext "${DASHBOARD_AUTH_PASSWORD}")"
fi

echo "[proxy-install] Rendering Caddyfile"
TMP_CADDYFILE="$(mktemp)"
trap 'rm -f "${TMP_CADDYFILE}"' EXIT

sed \
  -e "s|{{DASHBOARD_DOMAIN}}|${DASHBOARD_DOMAIN}|g" \
  -e "s|{{DASHBOARD_UPSTREAM}}|${DASHBOARD_UPSTREAM}|g" \
  -e "s|{{DASHBOARD_AUTH_USER}}|${DASHBOARD_AUTH_USER}|g" \
  -e "s|{{DASHBOARD_AUTH_HASH}}|${DASHBOARD_AUTH_HASH}|g" \
  -e "s|{{DASHBOARD_ALLOWED_CIDRS}}|${DASHBOARD_ALLOWED_CIDRS}|g" \
  "${TEMPLATE_PATH}" >"${TMP_CADDYFILE}"

caddy validate --config "${TMP_CADDYFILE}" --adapter caddyfile
install -m 0644 "${TMP_CADDYFILE}" "${CADDYFILE_PATH}"

echo "[proxy-install] Enabling and restarting caddy"
systemctl daemon-reload
systemctl enable caddy
systemctl restart caddy
systemctl --no-pager --full status caddy

if command -v ufw >/dev/null 2>&1; then
  if ufw status | grep -q "Status: active"; then
    echo "[proxy-install] Allowing HTTPS through UFW"
    ufw allow 443/tcp >/dev/null
  else
    echo "[proxy-install] UFW installed but not active; skipping firewall change"
  fi
else
  echo "[proxy-install] UFW not found; skipping firewall change"
fi

echo "[proxy-install] Completed"
echo "[proxy-install] Dashboard URL: https://${DASHBOARD_DOMAIN}"
echo "[proxy-install] To trust local CA on this host: caddy trust"
echo "[proxy-install] Dashboard app must run on ${DASHBOARD_UPSTREAM}"
