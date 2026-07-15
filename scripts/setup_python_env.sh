#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  echo "[python-setup] Do not run this script as root/sudo."
  echo "[python-setup] Run as your normal user so .venv and *.egg-info stay writable."
  exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
INSTALL_PROFILE="${INSTALL_PROFILE:-dev}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[python-setup] ${PYTHON_BIN} not found. Install Python 3.12+ and retry."
  exit 1
fi

PY_VERSION="$(${PYTHON_BIN} -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
REQ_MAJOR=3
REQ_MINOR=12

if ! ${PYTHON_BIN} -c "import sys; sys.exit(0 if sys.version_info >= (${REQ_MAJOR}, ${REQ_MINOR}) else 1)"; then
  echo "[python-setup] Python ${REQ_MAJOR}.${REQ_MINOR}+ required. Found ${PY_VERSION}."
  exit 1
fi

echo "[python-setup] Using Python ${PY_VERSION}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[python-setup] Creating virtual environment at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  echo "[python-setup] Existing .venv is not a Linux virtualenv layout. Recreating."
  rm -rf "${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[python-setup] Upgrading pip/setuptools/wheel"
python3 -m pip install --upgrade pip setuptools wheel

echo "[python-setup] Installing project dependencies profile: ${INSTALL_PROFILE}"
python3 -m pip install -e ".[${INSTALL_PROFILE}]"

if [[ "${INSTALL_PROFILE}" != "lakehouse" ]]; then
  echo "[python-setup] Note: install optional lakehouse deps with INSTALL_PROFILE=lakehouse"
fi

echo "[python-setup] Completed. Activate with: source .venv/bin/activate"
