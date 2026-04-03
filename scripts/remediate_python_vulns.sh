#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

if [[ ! -d "${VENV_DIR}" || ! -f "${VENV_DIR}/bin/activate" ]]; then
  echo "[remediate] .venv missing or invalid. Bootstrapping Python environment first."
  "${PROJECT_ROOT}/scripts/setup_python_env.sh"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[remediate] Upgrading packaging tooling"
python3 -m pip install --upgrade "pip>=26.0" "setuptools>=78.1.1" "wheel>=0.46.2"

declare -A MIN_SAFE
MIN_SAFE[certifi]="2024.7.4"
MIN_SAFE[configobj]="5.0.9"
MIN_SAFE[cryptography]="46.0.6"
MIN_SAFE[idna]="3.7"
MIN_SAFE[jinja2]="3.1.6"
MIN_SAFE[pyasn1]="0.6.3"
MIN_SAFE[pygments]="2.20.0"
MIN_SAFE[pyjwt]="2.12.0"
MIN_SAFE[pyopenssl]="26.0.0"
MIN_SAFE[requests]="2.33.0"
MIN_SAFE[twisted]="24.7.0"
MIN_SAFE[urllib3]="2.6.3"

UPGRADE_LIST=()

for pkg in "${!MIN_SAFE[@]}"; do
  if python3 -m pip show "$pkg" >/dev/null 2>&1; then
    UPGRADE_LIST+=("${pkg}>=${MIN_SAFE[$pkg]}")
  fi
done

if [[ ${#UPGRADE_LIST[@]} -gt 0 ]]; then
  echo "[remediate] Upgrading vulnerable installed packages"
  python3 -m pip install --upgrade "${UPGRADE_LIST[@]}"
else
  echo "[remediate] None of the known vulnerable packages are installed in .venv"
fi

echo "[remediate] Re-installing project dependencies"
python3 -m pip install -e ".[dev]"

echo "[remediate] Re-running vulnerability scan"
python3 -m pip_audit || true

echo "[remediate] Completed"
