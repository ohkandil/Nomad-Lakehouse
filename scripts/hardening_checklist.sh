#!/usr/bin/env bash
set -euo pipefail

warn() { echo "[warn] $1"; }
ok() { echo "[ok] $1"; }

if [[ "$(id -u)" -eq 0 ]]; then
  warn "Running as root. Use a non-root sudo user for operations."
else
  ok "Non-root user in use"
fi

if command -v ufw >/dev/null; then
  ufw status | grep -qi active && ok "UFW is active" || warn "UFW is not active"
else
  warn "ufw not installed"
fi

if systemctl is-enabled fail2ban >/dev/null 2>&1; then
  ok "fail2ban enabled"
else
  warn "fail2ban not enabled"
fi

if grep -qE '^PasswordAuthentication\s+no' /etc/ssh/sshd_config 2>/dev/null; then
  ok "SSH password authentication disabled"
else
  warn "SSH password authentication may be enabled"
fi

if grep -qE '^PermitRootLogin\s+no' /etc/ssh/sshd_config 2>/dev/null; then
  ok "Root SSH login disabled"
else
  warn "Root SSH login may be enabled"
fi

echo "[info] Hardening checklist audit completed"
