#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import curses
except ModuleNotFoundError:  # pragma: no cover - platform dependent
    curses = None  # type: ignore[assignment]


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_TEMPLATE_PATH = PROJECT_ROOT / ".env.example"
ENV_PATH = PROJECT_ROOT / ".env"

ENV_LINE_RE = re.compile(r"^([A-Z0-9_]+)=(.*)$")
BUCKET_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")
REGION_RE = re.compile(r"^[a-z]{2}-[a-z]+-\d+$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9.-]+(?<!-)$")

FIELD_SPECS: tuple[tuple[str, str, bool], ...] = (
    ("MinIO root user", "MINIO_ROOT_USER", False),
    ("MinIO root password", "MINIO_ROOT_PASSWORD", True),
    ("MinIO API port", "MINIO_API_PORT", False),
    ("MinIO console port", "MINIO_CONSOLE_PORT", False),
    ("Warehouse bucket", "WAREHOUSE_BUCKET", False),
    ("Postgres DB", "POSTGRES_DB", False),
    ("Postgres user", "POSTGRES_USER", False),
    ("Postgres password", "POSTGRES_PASSWORD", True),
    ("Postgres port", "POSTGRES_PORT", False),
    ("AWS region", "AWS_REGION", False),
    ("Dashboard domain", "DASHBOARD_DOMAIN", False),
    ("Dashboard auth user", "DASHBOARD_AUTH_USER", False),
    ("Dashboard allowed CIDRs", "DASHBOARD_ALLOWED_CIDRS", False),
)


@dataclass
class SetupConfig:
    minio_root_user: str
    minio_root_password: str
    minio_api_port: str
    minio_console_port: str
    warehouse_bucket: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_port: str
    aws_region: str
    dashboard_domain: str
    dashboard_auth_user: str
    dashboard_allowed_cidrs: str

    @classmethod
    def from_mapping(cls, values: dict[str, str]) -> SetupConfig:
        return cls(
            minio_root_user=values.get("MINIO_ROOT_USER", "minioadmin"),
            minio_root_password=values.get("MINIO_ROOT_PASSWORD", "change-me-strong-password"),
            minio_api_port=values.get("MINIO_API_PORT", "9000"),
            minio_console_port=values.get("MINIO_CONSOLE_PORT", "9001"),
            warehouse_bucket=values.get("WAREHOUSE_BUCKET", "warehouse"),
            postgres_db=values.get("POSTGRES_DB", "iceberg"),
            postgres_user=values.get("POSTGRES_USER", "iceberg"),
            postgres_password=values.get("POSTGRES_PASSWORD", "change-me-postgres-password"),
            postgres_port=values.get("POSTGRES_PORT", "5432"),
            aws_region=values.get("AWS_REGION", "us-east-1"),
            dashboard_domain=values.get("DASHBOARD_DOMAIN", "dashboard.home.arpa"),
            dashboard_auth_user=values.get("DASHBOARD_AUTH_USER", "admin"),
            dashboard_allowed_cidrs=values.get(
                "DASHBOARD_ALLOWED_CIDRS", "192.168.0.0/16 10.0.0.0/8 172.16.0.0/12"
            ),
        )


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = ENV_LINE_RE.match(line)
        if match is None:
            continue
        key, value = match.groups()
        values[key] = value
    return values


def as_env_mapping(config: SetupConfig) -> dict[str, str]:
    return {
        "MINIO_ROOT_USER": config.minio_root_user,
        "MINIO_ROOT_PASSWORD": config.minio_root_password,
        "MINIO_API_PORT": config.minio_api_port,
        "MINIO_CONSOLE_PORT": config.minio_console_port,
        "WAREHOUSE_BUCKET": config.warehouse_bucket,
        "POSTGRES_DB": config.postgres_db,
        "POSTGRES_USER": config.postgres_user,
        "POSTGRES_PASSWORD": config.postgres_password,
        "POSTGRES_PORT": config.postgres_port,
        "CATALOG_JDBC_URI": build_catalog_jdbc_uri(config.postgres_db, config.postgres_port),
        "AWS_REGION": config.aws_region,
        "DASHBOARD_DOMAIN": config.dashboard_domain,
        "DASHBOARD_AUTH_USER": config.dashboard_auth_user,
        "DASHBOARD_ALLOWED_CIDRS": config.dashboard_allowed_cidrs,
    }


def build_catalog_jdbc_uri(postgres_db: str, postgres_port: str) -> str:
    return f"jdbc:postgresql://localhost:{postgres_port}/{postgres_db}"


def validate_config(config: SetupConfig) -> list[str]:
    errors: list[str] = []
    mapping = as_env_mapping(config)

    for key in (
        "MINIO_ROOT_USER",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "AWS_REGION",
        "WAREHOUSE_BUCKET",
        "DASHBOARD_DOMAIN",
        "DASHBOARD_AUTH_USER",
        "DASHBOARD_ALLOWED_CIDRS",
    ):
        if not mapping[key].strip():
            errors.append(f"{key} cannot be empty")

    if len(mapping["MINIO_ROOT_PASSWORD"]) < 16:
        errors.append("MINIO_ROOT_PASSWORD must be at least 16 characters")
    if len(mapping["POSTGRES_PASSWORD"]) < 16:
        errors.append("POSTGRES_PASSWORD must be at least 16 characters")

    if not BUCKET_RE.match(mapping["WAREHOUSE_BUCKET"]):
        errors.append(
            "WAREHOUSE_BUCKET must match S3 naming constraints (lowercase letters, digits, hyphens)"
        )
    if not REGION_RE.match(mapping["AWS_REGION"]):
        errors.append("AWS_REGION must look like us-east-1")
    if not DOMAIN_RE.match(mapping["DASHBOARD_DOMAIN"]):
        errors.append("DASHBOARD_DOMAIN must be a valid hostname")

    used_ports: set[int] = set()
    for key in ("MINIO_API_PORT", "MINIO_CONSOLE_PORT", "POSTGRES_PORT"):
        value = mapping[key]
        if not value.isdigit():
            errors.append(f"{key} must be a number")
            continue
        port = int(value)
        if port < 1 or port > 65535:
            errors.append(f"{key} must be between 1 and 65535")
            continue
        if port in used_ports:
            errors.append(f"{key} cannot reuse a port already assigned")
            continue
        used_ports.add(port)

    return errors


def load_initial_config() -> SetupConfig:
    merged = parse_env_file(ENV_TEMPLATE_PATH)
    merged.update(parse_env_file(ENV_PATH))
    return SetupConfig.from_mapping(merged)


def write_env_file(path: Path, template_path: Path, values: dict[str, str]) -> None:
    template_lines = template_path.read_text(encoding="utf-8").splitlines()
    merged_values = parse_env_file(path)
    merged_values.update(values)
    output_lines: list[str] = []
    written_keys: set[str] = set()

    for line in template_lines:
        match = ENV_LINE_RE.match(line.strip())
        if match is None:
            output_lines.append(line)
            continue
        key, _ = match.groups()
        if key in merged_values:
            output_lines.append(f"{key}={merged_values[key]}")
            written_keys.add(key)
        else:
            output_lines.append(line)

    for key in sorted(merged_values.keys() - written_keys):
        output_lines.append(f"{key}={merged_values[key]}")

    path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


def _display_value(value: str, is_secret: bool) -> str:
    if not is_secret:
        return value
    return "*" * len(value) if value else "(empty)"


def _safe_addstr(stdscr: Any, row: int, col: int, text: str) -> None:
    max_y, max_x = stdscr.getmaxyx()
    if row < 0 or row >= max_y or col >= max_x:
        return
    allowed = max_x - col - 1
    if allowed <= 0:
        return
    stdscr.addstr(row, col, text[:allowed])


def _cfg_value(config: SetupConfig, key: str) -> str:
    return {
        "MINIO_ROOT_USER": config.minio_root_user,
        "MINIO_ROOT_PASSWORD": config.minio_root_password,
        "MINIO_API_PORT": config.minio_api_port,
        "MINIO_CONSOLE_PORT": config.minio_console_port,
        "WAREHOUSE_BUCKET": config.warehouse_bucket,
        "POSTGRES_DB": config.postgres_db,
        "POSTGRES_USER": config.postgres_user,
        "POSTGRES_PASSWORD": config.postgres_password,
        "POSTGRES_PORT": config.postgres_port,
        "AWS_REGION": config.aws_region,
        "DASHBOARD_DOMAIN": config.dashboard_domain,
        "DASHBOARD_AUTH_USER": config.dashboard_auth_user,
        "DASHBOARD_ALLOWED_CIDRS": config.dashboard_allowed_cidrs,
    }[key]


def _set_cfg_value(config: SetupConfig, key: str, value: str) -> None:
    if key == "MINIO_ROOT_USER":
        config.minio_root_user = value
    elif key == "MINIO_ROOT_PASSWORD":
        config.minio_root_password = value
    elif key == "MINIO_API_PORT":
        config.minio_api_port = value
    elif key == "MINIO_CONSOLE_PORT":
        config.minio_console_port = value
    elif key == "WAREHOUSE_BUCKET":
        config.warehouse_bucket = value
    elif key == "POSTGRES_DB":
        config.postgres_db = value
    elif key == "POSTGRES_USER":
        config.postgres_user = value
    elif key == "POSTGRES_PASSWORD":
        config.postgres_password = value
    elif key == "POSTGRES_PORT":
        config.postgres_port = value
    elif key == "AWS_REGION":
        config.aws_region = value
    elif key == "DASHBOARD_DOMAIN":
        config.dashboard_domain = value
    elif key == "DASHBOARD_AUTH_USER":
        config.dashboard_auth_user = value
    elif key == "DASHBOARD_ALLOWED_CIDRS":
        config.dashboard_allowed_cidrs = value


def _draw_tui(stdscr: Any, config: SetupConfig, selected: int, message: str) -> None:
    stdscr.clear()
    _safe_addstr(stdscr, 0, 0, "Nomad Lakehouse Admin Setup TUI")
    _safe_addstr(stdscr, 1, 0, "↑/↓ move  Enter edit  S save  Q quit")
    fields_start = 3

    for idx, (label, key, is_secret) in enumerate(FIELD_SPECS):
        marker = ">" if idx == selected else " "
        value = _display_value(_cfg_value(config, key), is_secret)
        _safe_addstr(stdscr, fields_start + idx, 0, f"{marker} {label:<22} : {value}")

    info_row = fields_start + len(FIELD_SPECS) + 1
    jdbc_uri = build_catalog_jdbc_uri(config.postgres_db, config.postgres_port)
    _safe_addstr(stdscr, info_row, 0, f"CATALOG_JDBC_URI (auto): {jdbc_uri}")
    if message:
        _safe_addstr(stdscr, info_row + 2, 0, message)

    stdscr.refresh()


def _edit_selected(stdscr: Any, config: SetupConfig, selected: int) -> str:
    label, key, _ = FIELD_SPECS[selected]
    current = _cfg_value(config, key)
    max_y, max_x = stdscr.getmaxyx()
    prompt = f"{label} [{current}]: "

    stdscr.move(max_y - 1, 0)
    stdscr.clrtoeol()
    _safe_addstr(stdscr, max_y - 1, 0, prompt)
    stdscr.refresh()

    curses.echo()
    curses.curs_set(1)
    input_col = min(len(prompt), max(0, max_x - 2))
    input_len = max(1, max_x - input_col - 1)
    raw = stdscr.getstr(max_y - 1, input_col, input_len)
    curses.curs_set(0)
    curses.noecho()

    value = raw.decode("utf-8").strip()
    if value:
        _set_cfg_value(config, key, value)
        return f"Updated {label}"
    return "No change"


def _run_curses_tui(config: SetupConfig) -> int:
    if curses is None:
        return 2

    save_message = ""
    saved = False

    def _main(stdscr: Any) -> None:
        nonlocal save_message
        nonlocal saved
        selected = 0
        curses.curs_set(0)

        while True:
            _draw_tui(stdscr, config, selected, save_message)
            key = stdscr.getch()

            if key in (ord("q"), ord("Q")):
                return
            if key in (curses.KEY_UP, ord("k"), ord("K")):
                selected = (selected - 1) % len(FIELD_SPECS)
                continue
            if key in (curses.KEY_DOWN, ord("j"), ord("J")):
                selected = (selected + 1) % len(FIELD_SPECS)
                continue
            if key in (10, 13, curses.KEY_ENTER):
                save_message = _edit_selected(stdscr, config, selected)
                continue
            if key in (ord("s"), ord("S")):
                errors = validate_config(config)
                if errors:
                    save_message = f"Cannot save: {errors[0]}"
                    continue
                write_env_file(ENV_PATH, ENV_TEMPLATE_PATH, as_env_mapping(config))
                save_message = f"Saved configuration to {ENV_PATH}"
                saved = True
                return

    curses.wrapper(_main)
    return 0 if saved else 1


def _run_prompt_fallback(config: SetupConfig) -> int:
    print("curses is unavailable; using prompt mode instead.")
    print("Press Enter to keep current value.")

    for label, key, _ in FIELD_SPECS:
        current = _cfg_value(config, key)
        entered = input(f"{label} [{current}]: ").strip()
        if entered:
            _set_cfg_value(config, key, entered)

    errors = validate_config(config)
    if errors:
        print(f"Cannot save configuration: {errors[0]}")
        return 1

    write_env_file(ENV_PATH, ENV_TEMPLATE_PATH, as_env_mapping(config))
    print(f"Saved configuration to {ENV_PATH}")
    return 0


def main() -> int:
    config = load_initial_config()
    if curses is None:
        return _run_prompt_fallback(config)
    return _run_curses_tui(config)


if __name__ == "__main__":
    raise SystemExit(main())
