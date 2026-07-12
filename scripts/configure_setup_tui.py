#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    ("Dashboard auth password", "DASHBOARD_AUTH_PASSWORD", True),
    ("Dashboard upstream", "DASHBOARD_UPSTREAM", False),
    ("Dashboard allowed CIDRs", "DASHBOARD_ALLOWED_CIDRS", False),
)

FIELD_HELP: dict[str, str] = {
    "MINIO_ROOT_USER": "Admin username for MinIO object storage.",
    "MINIO_ROOT_PASSWORD": "Use 16+ chars. This secures your object storage API and console.",
    "MINIO_API_PORT": "MinIO S3 API port. Keep this open only where needed.",
    "MINIO_CONSOLE_PORT": "MinIO web console port for local administration.",
    "WAREHOUSE_BUCKET": "Main object storage bucket name for lakehouse data.",
    "POSTGRES_DB": "PostgreSQL database used for metadata/catalog state.",
    "POSTGRES_USER": "PostgreSQL user for catalog operations.",
    "POSTGRES_PASSWORD": "Use 16+ chars. Rotate before shared or production use.",
    "POSTGRES_PORT": "PostgreSQL service port.",
    "AWS_REGION": "S3-compatible region value, e.g. us-east-1.",
    "DASHBOARD_DOMAIN": "Hostname used by Caddy HTTPS reverse proxy.",
    "DASHBOARD_AUTH_USER": "Basic-auth username for dashboard HTTPS access.",
    "DASHBOARD_AUTH_PASSWORD": "Basic-auth password used to generate the Caddy hash.",
    "DASHBOARD_UPSTREAM": "Loopback address for FastAPI upstream, e.g. 127.0.0.1:8088.",
    "DASHBOARD_ALLOWED_CIDRS": "Space-separated CIDR ranges allowed to reach dashboard via Caddy.",
}

OPTION_SPECS: tuple[tuple[str, str, str], ...] = (
    (
        "Start core stack now",
        "start_stack_now",
        "Run setup_minio.sh to start MinIO/Postgres and wait for health.",
    ),
    (
        "Prepare Python lakehouse env",
        "setup_python_env_now",
        "Run setup_python_env.sh with lakehouse profile and create .venv.",
    ),
    (
        "Run Bronze/Silver/Gold pipeline",
        "run_pipeline_now",
        "Execute all starter pipeline scripts after environment setup.",
    ),
    (
        "Install dashboard systemd service",
        "install_dashboard_service_now",
        "Install and enable nomad-dashboard.service on boot.",
    ),
    (
        "Install Caddy dashboard HTTPS proxy",
        "install_dashboard_proxy_now",
        "Install/reconfigure reverse proxy with auth + LAN CIDR restrictions.",
    ),
    (
        "Enable core stack auto-start",
        "install_core_service_now",
        "Install and enable nomad-lakehouse.service.",
    ),
)

UPSTREAM_RE = re.compile(r"^(?P<host>[A-Za-z0-9.-]+):(?P<port>\d{1,5})$")

CONFIG_ATTRS_BY_KEY: dict[str, str] = {
    "MINIO_ROOT_USER": "minio_root_user",
    "MINIO_ROOT_PASSWORD": "minio_root_password",
    "MINIO_API_PORT": "minio_api_port",
    "MINIO_CONSOLE_PORT": "minio_console_port",
    "WAREHOUSE_BUCKET": "warehouse_bucket",
    "POSTGRES_DB": "postgres_db",
    "POSTGRES_USER": "postgres_user",
    "POSTGRES_PASSWORD": "postgres_password",
    "POSTGRES_PORT": "postgres_port",
    "AWS_REGION": "aws_region",
    "DASHBOARD_DOMAIN": "dashboard_domain",
    "DASHBOARD_AUTH_USER": "dashboard_auth_user",
    "DASHBOARD_AUTH_PASSWORD": "dashboard_auth_password",
    "DASHBOARD_UPSTREAM": "dashboard_upstream",
    "DASHBOARD_ALLOWED_CIDRS": "dashboard_allowed_cidrs",
}


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
    dashboard_auth_password: str = "change-me-dashboard-password"
    dashboard_upstream: str = "127.0.0.1:8088"
    dashboard_allowed_cidrs: str = "192.168.0.0/16 10.0.0.0/8 172.16.0.0/12"

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
            dashboard_auth_password=values.get(
                "DASHBOARD_AUTH_PASSWORD", "change-me-dashboard-password"
            ),
            dashboard_upstream=values.get("DASHBOARD_UPSTREAM", "127.0.0.1:8088"),
            dashboard_allowed_cidrs=values.get(
                "DASHBOARD_ALLOWED_CIDRS", "192.168.0.0/16 10.0.0.0/8 172.16.0.0/12"
            ),
        )


@dataclass
class SetupWorkflowOptions:
    start_stack_now: bool = True
    setup_python_env_now: bool = True
    run_pipeline_now: bool = True
    install_dashboard_service_now: bool = True
    install_dashboard_proxy_now: bool = True
    install_core_service_now: bool = True


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
        "DASHBOARD_AUTH_PASSWORD": config.dashboard_auth_password,
        "DASHBOARD_UPSTREAM": config.dashboard_upstream,
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
    if len(mapping["DASHBOARD_AUTH_PASSWORD"]) < 16:
        errors.append("DASHBOARD_AUTH_PASSWORD must be at least 16 characters")

    if not BUCKET_RE.match(mapping["WAREHOUSE_BUCKET"]):
        errors.append(
            "WAREHOUSE_BUCKET must match S3 naming constraints (lowercase letters, digits, hyphens)"
        )
    if not REGION_RE.match(mapping["AWS_REGION"]):
        errors.append("AWS_REGION must look like us-east-1")
    if not DOMAIN_RE.match(mapping["DASHBOARD_DOMAIN"]):
        errors.append("DASHBOARD_DOMAIN must be a valid hostname")

    upstream_match = UPSTREAM_RE.match(mapping["DASHBOARD_UPSTREAM"])
    if upstream_match is None:
        errors.append("DASHBOARD_UPSTREAM must look like 127.0.0.1:8088")
    else:
        upstream_port = int(upstream_match.group("port"))
        if upstream_port < 1 or upstream_port > 65535:
            errors.append("DASHBOARD_UPSTREAM port must be between 1 and 65535")

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
    return str(getattr(config, CONFIG_ATTRS_BY_KEY[key]))


def _set_cfg_value(config: SetupConfig, key: str, value: str) -> None:
    setattr(config, CONFIG_ATTRS_BY_KEY[key], value)


def _workflow_value(options: SetupWorkflowOptions, key: str) -> bool:
    return bool(getattr(options, key))


def _toggle_workflow_option(options: SetupWorkflowOptions, key: str) -> None:
    setattr(options, key, not _workflow_value(options, key))


def build_setup_guide(config: SetupConfig, options: SetupWorkflowOptions) -> list[str]:
    lines: list[str] = [
        "Setup complete! Follow this guided checklist:",
        "",
        "1) Core stack",
        "   - Start services: sudo ./scripts/setup_minio.sh",
        "   - Health check: sudo ./scripts/healthcheck.sh",
    ]

    if options.install_core_service_now:
        lines.append(
            "   - Enable boot auto-start: sudo ./scripts/install_systemd_service.sh"
        )
    else:
        lines.append(
            "   - Optional auto-start later: sudo ./scripts/install_systemd_service.sh"
        )

    lines.extend(
        [
            "",
            "2) Python + pipelines",
            "   - Create environment: INSTALL_PROFILE=lakehouse ./scripts/setup_python_env.sh",
            "   - Activate: source .venv/bin/activate",
            "   - Bronze: python3 scripts/create_bronze_tables.py",
            "   - Silver: python3 scripts/bronze_to_silver.py",
            "   - Gold: python3 scripts/silver_to_gold.py",
            "",
            "3) Dashboard",
            (
                "   - Local dashboard: python3 -m uvicorn dashboard.app:app "
                "--host 127.0.0.1 --port 8088"
            ),
        ]
    )

    if options.install_dashboard_service_now:
        lines.append("   - Install dashboard service: sudo ./scripts/install_dashboard_service.sh")

    if options.install_dashboard_proxy_now:
        lines.extend(
            [
                "   - Configure HTTPS proxy from saved .env values:",
                (
                    "     set -a; source .env; set +a; "
                    "sudo -E ./scripts/install_dashboard_reverse_proxy.sh"
                ),
                f"   - Secure URL: https://{config.dashboard_domain}",
                f"   - Dashboard auth user: {config.dashboard_auth_user}",
                "   - Dashboard auth password: read DASHBOARD_AUTH_PASSWORD from .env",
            ]
        )
    else:
        lines.append(
            "   - Optional HTTPS proxy later: "
            "sudo ./scripts/install_dashboard_reverse_proxy.sh"
        )

    lines.extend(
        [
            "",
            "4) Access",
            f"   - MinIO API health: http://127.0.0.1:{config.minio_api_port}/minio/health/live",
            f"   - MinIO console: http://127.0.0.1:{config.minio_console_port}",
            "   - Dashboard local: http://127.0.0.1:8088",
        ]
    )
    if options.install_dashboard_proxy_now:
        lines.append(f"   - Dashboard HTTPS: https://{config.dashboard_domain}")

    lines.extend(
        [
            "",
            "Selected first-setup automation preferences:",
            f"   - Start core stack now: {'yes' if options.start_stack_now else 'no'}",
            f"   - Prepare Python env now: {'yes' if options.setup_python_env_now else 'no'}",
            f"   - Run pipeline now: {'yes' if options.run_pipeline_now else 'no'}",
        ]
    )
    return lines


def _draw_tui(
    stdscr: Any,
    config: SetupConfig,
    options: SetupWorkflowOptions,
    active_section: str,
    selected_field: int,
    selected_option: int,
    message: str,
) -> None:
    stdscr.clear()
    _safe_addstr(stdscr, 0, 0, "Nomad Lakehouse First-Setup Wizard")
    _safe_addstr(
        stdscr, 1, 0, "Tab switch section  ↑/↓ move  Enter edit  Space toggle  S save  Q quit"
    )
    section_name = "Credentials & services" if active_section == "fields" else "Setup preferences"
    _safe_addstr(stdscr, 2, 0, f"Section: {section_name}")
    fields_start = 4

    for idx, (label, key, is_secret) in enumerate(FIELD_SPECS):
        marker = ">" if active_section == "fields" and idx == selected_field else " "
        value = _display_value(_cfg_value(config, key), is_secret)
        _safe_addstr(stdscr, fields_start + idx, 0, f"{marker} {label:<25} : {value}")

    options_header = fields_start + len(FIELD_SPECS) + 1
    _safe_addstr(stdscr, options_header, 0, "Setup actions")
    for idx, (label, key, _) in enumerate(OPTION_SPECS):
        marker = ">" if active_section == "options" and idx == selected_option else " "
        checked = "x" if _workflow_value(options, key) else " "
        _safe_addstr(stdscr, options_header + 1 + idx, 0, f"{marker} [{checked}] {label}")

    info_row = options_header + len(OPTION_SPECS) + 2
    jdbc_uri = build_catalog_jdbc_uri(config.postgres_db, config.postgres_port)
    _safe_addstr(stdscr, info_row, 0, f"CATALOG_JDBC_URI (auto): {jdbc_uri}")
    if active_section == "fields":
        help_key = FIELD_SPECS[selected_field][1]
        _safe_addstr(stdscr, info_row + 1, 0, f"Hint: {FIELD_HELP[help_key]}")
    else:
        _safe_addstr(stdscr, info_row + 1, 0, f"Hint: {OPTION_SPECS[selected_option][2]}")
    if message:
        _safe_addstr(stdscr, info_row + 3, 0, message)

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


def _run_curses_tui(config: SetupConfig, options: SetupWorkflowOptions) -> int:
    if curses is None:
        return 2

    save_message = ""
    saved = False

    def _main(stdscr: Any) -> None:
        nonlocal save_message
        nonlocal saved
        active_section = "fields"
        selected_field = 0
        selected_option = 0
        curses.curs_set(0)

        while True:
            _draw_tui(
                stdscr,
                config,
                options,
                active_section,
                selected_field,
                selected_option,
                save_message,
            )
            key = stdscr.getch()

            if key in (ord("q"), ord("Q")):
                return
            if key in (9, curses.KEY_BTAB):
                active_section = "options" if active_section == "fields" else "fields"
                continue
            if key in (curses.KEY_UP, ord("k"), ord("K")):
                if active_section == "fields":
                    selected_field = (selected_field - 1) % len(FIELD_SPECS)
                else:
                    selected_option = (selected_option - 1) % len(OPTION_SPECS)
                continue
            if key in (curses.KEY_DOWN, ord("j"), ord("J")):
                if active_section == "fields":
                    selected_field = (selected_field + 1) % len(FIELD_SPECS)
                else:
                    selected_option = (selected_option + 1) % len(OPTION_SPECS)
                continue
            if key in (10, 13, curses.KEY_ENTER):
                if active_section == "fields":
                    save_message = _edit_selected(stdscr, config, selected_field)
                else:
                    _, option_key, _ = OPTION_SPECS[selected_option]
                    _toggle_workflow_option(options, option_key)
                    save_message = f"Toggled: {OPTION_SPECS[selected_option][0]}"
                continue
            if key in (ord(" "),):
                if active_section == "options":
                    _, option_key, _ = OPTION_SPECS[selected_option]
                    _toggle_workflow_option(options, option_key)
                    save_message = f"Toggled: {OPTION_SPECS[selected_option][0]}"
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
    options = SetupWorkflowOptions()
    print("curses is unavailable; using prompt wizard mode instead.")
    print("Press Enter to keep current value.")

    for label, key, _ in FIELD_SPECS:
        current = _cfg_value(config, key)
        entered = input(f"{label} [{current}]: ").strip()
        if entered:
            _set_cfg_value(config, key, entered)

    print("\nChoose first-setup actions:")
    for label, key, _ in OPTION_SPECS:
        default_enabled = _workflow_value(options, key)
        default_marker = "Y/n" if default_enabled else "y/N"
        raw = input(f"{label}? [{default_marker}]: ").strip().lower()
        if raw in {"y", "yes"}:
            setattr(options, key, True)
        elif raw in {"n", "no"}:
            setattr(options, key, False)

    errors = validate_config(config)
    if errors:
        print(f"Cannot save configuration: {errors[0]}")
        return 1

    write_env_file(ENV_PATH, ENV_TEMPLATE_PATH, as_env_mapping(config))
    print(f"Saved configuration to {ENV_PATH}")
    print("")
    print("\n".join(build_setup_guide(config, options)))
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive first-setup wizard for Nomad Lakehouse credentials and services."
    )
    parser.add_argument(
        "--prompt",
        action="store_true",
        help="Use prompt-mode wizard even when curses is available.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = load_initial_config()
    options = SetupWorkflowOptions()
    if curses is None or args.prompt:
        return _run_prompt_fallback(config)
    status = _run_curses_tui(config, options)
    if status == 0:
        print("")
        print("\n".join(build_setup_guide(config, options)))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
