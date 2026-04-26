from __future__ import annotations

import json
from pathlib import Path

from dashboard.models import SecurityStatus

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_REPORTS = [
    ROOT / "data" / "output" / "pip-audit-report.json",
    ROOT / "data" / "output" / "security" / "pip-audit-report.json",
]


def _find_report() -> Path | None:
    for path in CANDIDATE_REPORTS:
        if path.exists():
            return path
    return None


def _display_report_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def collect_security_status() -> SecurityStatus:
    report = _find_report()
    if report is None:
        guidance = (
            "No security report file detected. Generate one with: "
            "python3 -m pip_audit --skip-editable --ignore-vuln CVE-2026-3219 "
            "--format json --output data/output/pip-audit-report.json"
        )
        return SecurityStatus(
            status="unknown",
            detail=guidance,
        )

    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return SecurityStatus(
            status="warn",
            detail=f"Report exists but could not be parsed: {exc}",
            report_path=_display_report_path(report),
        )

    vulnerabilities = payload.get("vulnerabilities", [])
    high_count = 0
    critical_count = 0

    for item in vulnerabilities:
        severity = str(item.get("severity", "")).lower()
        if severity == "high":
            high_count += 1
        elif severity == "critical":
            critical_count += 1

    status = "ok"
    if critical_count > 0:
        status = "fail"
    elif high_count > 0:
        status = "warn"

    return SecurityStatus(
        status=status,
        detail=f"Parsed {len(vulnerabilities)} vulnerability entries",
        report_path=_display_report_path(report),
        high_count=high_count,
        critical_count=critical_count,
    )
