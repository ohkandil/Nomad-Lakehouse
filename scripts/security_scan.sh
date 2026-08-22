#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "[security] Stage security scan started"

if command -v python3 >/dev/null; then
  echo "[security] Running pip-audit (if available)"
  if python3 -m pip show pip-audit >/dev/null 2>&1; then
    python3 -m pip_audit --skip-editable --ignore-vuln CVE-2026-3219 || true
  else
    echo "[security] pip-audit not installed in current environment"
  fi
else
  echo "[security] python3 not found"
fi

if command -v trivy >/dev/null; then
  echo "[security] Running trivy fs scan"
  trivy fs --severity HIGH,CRITICAL --no-progress . || true
else
  echo "[security] trivy not installed"
fi

if command -v docker >/dev/null; then
  echo "[security] Listing local images for optional CVE scanning"
  docker images --format '{{.Repository}}:{{.Tag}}' | sed '/^<none>/d' | head -n 20 || true
fi

echo "[security] Stage security scan completed"
