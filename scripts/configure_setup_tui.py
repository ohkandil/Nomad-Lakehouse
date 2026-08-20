#!/usr/bin/env python3
# mypy: disable-error-code="no-any-return"
from __future__ import annotations

import argparse
import asyncio
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opentui import (
    Box,
    Input,
    Signal,
    Text,
    component,
    render,
    use_keyboard,
    use_renderer,
)
from opentui.events import KeyEvent

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_TEMPLATE_PATH = PROJECT_ROOT / ".env.example"
ENV_PATH = PROJECT_ROOT / ".env"

ENV_LINE_RE = re.compile(r"^([A-Z0-9_]+)=(.*)$")
BUCKET_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")
REGION_RE = re.compile(r"^[a-z]{2}-[a-z]+-\d+$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9.-]+(?<!-)$")

FIELD_SPECS: tuple[tuple[str, str, bool, bool], ...] = (
    ("MinIO root user", "MINIO_ROOT_USER", False, False),
    ("MinIO root password", "MINIO_ROOT_PASSWORD", True, False),
    ("MinIO API port", "MINIO_API_PORT", False, True),
    ("MinIO console port", "MINIO_CONSOLE_PORT", False, True),
    ("Warehouse bucket", "WAREHOUSE_BUCKET", False, True),
    ("Postgres DB", "POSTGRES_DB", False, True),
    ("Postgres user", "POSTGRES_USER", False, True),
    ("Postgres password", "POSTGRES_PASSWORD", True, False),
    ("Postgres port", "POSTGRES_PORT", False, True),
    ("AWS region", "AWS_REGION", False, True),
    ("Dashboard domain", "DASHBOARD_DOMAIN", False, True),
    ("Dashboard auth user", "DASHBOARD_AUTH_USER", False, False),
    ("Dashboard auth password", "DASHBOARD_AUTH_PASSWORD", True, False),
    ("Dashboard upstream", "DASHBOARD_UPSTREAM", False, True),
    ("Dashboard allowed CIDRs", "DASHBOARD_ALLOWED_CIDRS", False, True),
)

FIELD_HELP: dict[str, str] = {
    "MINIO_ROOT_USER": "Admin username for MinIO object storage.",
    "MINIO_ROOT_PASSWORD": "Use 16+ chars. This secures your object storage API and console.",  # nosec
    "MINIO_API_PORT": "MinIO S3 API port. Keep this open only on trusted networks.",
    "MINIO_CONSOLE_PORT": "MinIO web console port.",
    "WAREHOUSE_BUCKET": "S3 bucket name (lowercase, digits, hyphens only).",
    "POSTGRES_DB": "PostgreSQL database for Iceberg catalog.",
    "POSTGRES_USER": "PostgreSQL user for catalog operations.",
    "POSTGRES_PASSWORD": "Use 16+ chars. Rotate before shared or production use.",  # nosec
    "POSTGRES_PORT": "PostgreSQL service port.",
    "AWS_REGION": "S3-compatible region value, e.g. us-east-1.",
    "DASHBOARD_DOMAIN": "Hostname used by Caddy HTTPS reverse proxy.",
    "DASHBOARD_AUTH_USER": "Basic-auth username for dashboard HTTPS access.",
    "DASHBOARD_AUTH_PASSWORD": "Basic-auth password used to generate the Caddy hash.",  # nosec
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
    "MINIO_ROOT_PASSWORD": "minio_root_password",  # nosec
    "MINIO_API_PORT": "minio_api_port",
    "MINIO_CONSOLE_PORT": "minio_console_port",
    "WAREHOUSE_BUCKET": "warehouse_bucket",
    "POSTGRES_DB": "postgres_db",
    "POSTGRES_USER": "postgres_user",
    "POSTGRES_PASSWORD": "postgres_password",  # nosec
    "POSTGRES_PORT": "postgres_port",
    "AWS_REGION": "aws_region",
    "DASHBOARD_DOMAIN": "dashboard_domain",
    "DASHBOARD_AUTH_USER": "dashboard_auth_user",
    "DASHBOARD_AUTH_PASSWORD": "dashboard_auth_password",  # nosec
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


# ==============================================================================
# OpenTUI Components & State
# ==============================================================================

FIELD_KEYS: tuple[str, ...] = tuple(key for _, key, _, _ in FIELD_SPECS)
OPTION_KEYS: tuple[str, ...] = tuple(key for _, key, _ in OPTION_SPECS)

# User experience mode: "basic" (guided, fewer fields) or "advanced" (full control)
user_mode = Signal("basic", name="user_mode")
active_section = Signal("fields", name="active_section")
selected_idx = Signal(0, name="selected_idx")
mode = Signal("navigate", name="mode")
editing_field = Signal(-1, name="editing_field")
editing_original_value = Signal("", name="editing_original_value")
status_message = Signal(
    "Welcome! Configure your lakehouse. Press ? for help, M to switch mode, S to save.",
    name="status_message",
)
status_kind = Signal("info", name="status_kind")
show_help = Signal(False, name="show_help")
show_review = Signal(False, name="show_review")

field_values: dict[str, Any] = {}
option_values: dict[str, Any] = {}


def _field_values_from_config(config: SetupConfig) -> dict[str, str]:
    return {key: str(getattr(config, CONFIG_ATTRS_BY_KEY[key])) for key in FIELD_KEYS}


def _option_values_from_options(options: SetupWorkflowOptions) -> dict[str, bool]:
    return {key: bool(getattr(options, key)) for key in OPTION_KEYS}


def _apply_field_values(config: SetupConfig, values: Mapping[str, str]) -> None:
    for key in FIELD_KEYS:
        setattr(config, CONFIG_ATTRS_BY_KEY[key], values[key])


def _apply_option_values(options: SetupWorkflowOptions, values: Mapping[str, bool]) -> None:
    for key in OPTION_KEYS:
        setattr(options, key, values[key])


def _status_color() -> str:
    return {
        "error": "red",
        "success": "green",
        "info": "yellow",
        "idle": "white",
    }.get(status_kind(), "white")


def _set_status(message: str, kind: str = "idle") -> None:
    status_message.set(message)
    status_kind.set(kind)


def _reactive(value: object) -> Any:
    return value


def _display_field_value(key: str, value: str, is_secret: bool) -> str:
    if not is_secret:
        return value
    return "*" * len(value) if value else "(empty)"


def visible_field_specs() -> list[tuple[str, str, bool, bool]]:
    """Return the field specs visible for the current user mode.

    In ``basic`` mode, advanced-only fields are hidden and keep their defaults.
    In ``advanced`` mode every field is shown.
    """
    if user_mode() == "advanced":
        return list(FIELD_SPECS)
    return [spec for spec in FIELD_SPECS if not spec[3]]


def field_error(key: str, value: str) -> str | None:
    """Return a human-readable validation error for ``key`` given ``value``."""
    if key in {
        "MINIO_ROOT_USER",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "AWS_REGION",
        "WAREHOUSE_BUCKET",
        "DASHBOARD_DOMAIN",
        "DASHBOARD_AUTH_USER",
        "DASHBOARD_ALLOWED_CIDRS",
    }:
        if not value.strip():
            return f"{key} cannot be empty"
    if key in {"MINIO_ROOT_PASSWORD", "POSTGRES_PASSWORD", "DASHBOARD_AUTH_PASSWORD"}:
        if len(value) < 16:
            return "must be at least 16 characters"
    if key == "WAREHOUSE_BUCKET" and value and not BUCKET_RE.match(value):
        return "must match S3 naming (lowercase, digits, hyphens)"
    if key == "AWS_REGION" and value and not REGION_RE.match(value):
        return "must look like us-east-1"
    if key == "DASHBOARD_DOMAIN" and value and not DOMAIN_RE.match(value):
        return "must be a valid hostname"
    if key == "DASHBOARD_UPSTREAM" and value:
        match = UPSTREAM_RE.match(value)
        if match is None:
            return "must look like 127.0.0.1:8088"
        port = int(match.group("port"))
        if port < 1 or port > 65535:
            return "port must be between 1 and 65535"
    if key in {"MINIO_API_PORT", "MINIO_CONSOLE_PORT", "POSTGRES_PORT"} and value:
        if not value.isdigit():
            return "must be a number"
        port = int(value)
        if port < 1 or port > 65535:
            return "must be between 1 and 65535"
    return None


def _configured_count() -> int:
    specs = visible_field_specs()
    count = 0
    for label, key, is_secret, _ in specs:
        value = field_values.get(key)
        raw = value() if value is not None else ""
        if field_error(key, raw) is None and raw.strip():
            count += 1
    return count


@component
def TitleBar() -> Any:
    return Box(
        Text(
            " NOMAD LAKEHOUSE FIRST-SETUP WIZARD ",
            fg="black",
            bg="cyan",
            bold=True,
        ),
        border_bottom=True,
        border_color="cyan",
        padding_bottom=1,
    )


@component
def ModeBar() -> Any:
    def mode_label() -> str:
        return "BASIC" if user_mode() == "basic" else "ADVANCED"

    def mode_color() -> str:
        return "green" if user_mode() == "basic" else "magenta"

    def mode_hint() -> str:
        return (
            "Guided setup — only key credentials shown"
            if user_mode() == "basic"
            else "Full control — every setting is editable"
        )

    total = len(visible_field_specs())
    configured = _configured_count()

    def progress_text() -> str:
        pct = int((configured / total) * 100) if total else 100
        return f" {configured}/{total} fields ready ({pct}%)"

    return Box(
        Text(
            lambda: f" MODE: [{mode_label()}] ",
            fg="black",
            bg=_reactive(mode_color),
            bold=True,
        ),
        Text(lambda: f"  {mode_hint()}", fg="gray"),
        Text(lambda: progress_text(), fg="yellow", bold=True),
        flex_direction="row",
        align_items="center",
        gap=2,
        border_bottom=True,
        border_color=_reactive(mode_color),
        padding_top=1,
        padding_bottom=1,
    )


@component
def Tabs() -> Any:
    def tab(section: str, label: str) -> Any:
        is_active = active_section() == section
        return Box(
            Text(
                lambda: f" {label} " if is_active else f"  {label}  ",
                fg="black" if is_active else "cyan",
                bg="cyan" if is_active else "black",
                bold=True,
            ),
            padding_left=2,
            padding_right=2,
        )

    return Box(
        tab("fields", "Credentials & Services"),
        tab("options", "Setup Preferences"),
        flex_direction="row",
        align_items="center",
        gap=1,
    )


@component
def FieldRow(index: int, label: str, key: str, is_secret: bool) -> Any:
    def is_selected() -> bool:
        return active_section() == "fields" and selected_idx() == index

    def is_editing() -> bool:
        return mode() == "edit" and editing_field() == index

    def row_background() -> str:
        if is_editing():
            return "cyan"
        if is_selected():
            return "blue"
        return "black"

    def row_foreground() -> str:
        if is_editing():
            return "black"
        if is_selected():
            return "white"
        return "cyan"

    def marker() -> str:
        return "▶" if is_selected() or is_editing() else " "

    def validity_mark() -> str:
        if is_editing():
            return " "
        err = field_error(key, field_values[key]())
        if err is None and field_values[key]().strip():
            return "✓"
        return "✗"

    def validity_color() -> str:
        if is_editing():
            return "black"
        err = field_error(key, field_values[key]())
        if err is None and field_values[key]().strip():
            return "green"
        return "red"

    def display_value() -> str:
        return _display_field_value(key, field_values[key](), is_secret)

    def render_display_row() -> Any:
        return Box(
            Text(
                lambda: f" {marker()} {validity_mark()} {label:<21} : {display_value()}",
                fg=_reactive(row_foreground),
                bg=_reactive(row_background),
                bold=True,
            ),
            flex_direction="row",
            align_items="center",
            bg=_reactive(row_background),
            padding_left=1,
            padding_right=1,
        )

    def render_edit_row() -> Any:
        widget_holder: dict[str, Input] = {}

        def commit_value() -> None:
            widget = widget_holder["input"]
            field_values[key].set(widget.value)

        def finish_edit(message: str) -> None:
            commit_value()
            editing_field.set(-1)
            mode.set("navigate")
            editing_original_value.set("")
            _set_status(message, "success")

        def cancel_edit() -> None:
            original = editing_original_value()
            field_values[key].set(original)
            editing_field.set(-1)
            mode.set("navigate")
            editing_original_value.set("")
            _set_status(f"Canceled edit for {label}", "idle")

        def move_to_next_field() -> None:
            commit_value()
            specs = visible_field_specs()
            next_idx = (index + 1) % len(specs)
            next_key = specs[next_idx][1]
            selected_idx.set(next_idx)
            active_section.set("fields")
            editing_field.set(next_idx)
            editing_original_value.set(field_values[next_key]())
            mode.set("edit")
            _set_status(f"Editing {specs[next_idx][0]}", "info")

        def on_key_down(event: KeyEvent) -> None:
            key_name = event.name.lower()
            if key_name == "tab":
                move_to_next_field()
                event.stop_propagation()
                return
            if key_name in {"return", "enter", "linefeed"}:
                finish_edit(f"Updated {label}")
                event.stop_propagation()
                return
            if key_name == "escape":
                cancel_edit()
                event.stop_propagation()
                return

            widget = widget_holder["input"]
            if widget.handle_key(event):
                field_values[key].set(widget.value)
            event.stop_propagation()

        input_widget = Input(
            value=field_values[key](),
            focused=True,
            show_cursor=True,
            background_color="cyan",
            fg="black",
            cursor_color="black",
            on_key_down=on_key_down,
            key=key,
        )
        widget_holder["input"] = input_widget
        return Box(
            Text(
                lambda: f" {marker()} {validity_mark()} {label:<21} : ",
                fg="black",
                bg="cyan",
                bold=True,
            ),
            input_widget,
            flex_direction="row",
            align_items="center",
            bg="cyan",
            padding_left=1,
            padding_right=1,
        )

    return Box(lambda: render_edit_row() if is_editing() else render_display_row(), key=key)


@component
def CredentialsPanel() -> Any:
    return Box(
        *[
            FieldRow(i, label, key, is_secret)
            for i, (label, key, is_secret, _) in enumerate(visible_field_specs())
        ],
        title=" Credentials & Services ",
        border=True,
        border_color="cyan",
        border_style="rounded",
        flex_grow=2,
        gap=1,
        padding=1,
    )


@component
def OptionRow(index: int, label: str, key: str, description: str) -> Any:
    def is_selected() -> bool:
        return active_section() == "options" and selected_idx() == index

    def row_background() -> str:
        return "blue" if is_selected() else "black"

    def row_foreground() -> str:
        return "white" if is_selected() else "cyan"

    def marker() -> str:
        return ">" if is_selected() else " "

    def checked() -> str:
        return "[x]" if option_values[key]() else "[ ]"

    def description_color() -> str:
        return "white" if is_selected() else "gray"

    return Box(
        Text(
            lambda: f" {marker()} {checked()} {label}",
            fg=_reactive(row_foreground),
            bg=_reactive(row_background),
            bold=True,
        ),
        Text(
            lambda: f"   {description}",
            fg=_reactive(description_color),
            bg=_reactive(row_background),
        ),
        flex_direction="column",
        bg=_reactive(row_background),
        padding_left=1,
        padding_right=1,
        padding_top=0,
        padding_bottom=0,
    )


@component
def SetupActionsPanel() -> Any:
    return Box(
        *[
            OptionRow(i, label, key, description)
            for i, (label, key, description) in enumerate(OPTION_SPECS)
        ],
        title=" Setup Actions ",
        border=True,
        border_color="cyan",
        border_style="rounded",
        flex_grow=1,
        gap=1,
        padding=1,
    )


@component
def InfoBar() -> Any:
    def jdbc_uri() -> str:
        db = field_values["POSTGRES_DB"]()
        port = field_values["POSTGRES_PORT"]()
        return build_catalog_jdbc_uri(db, port)

    def hint() -> str:
        if mode() == "edit":
            return "Esc cancels the current field. Enter saves it. Tab advances to the next field."
        if active_section() == "fields":
            idx = selected_idx()
            specs = visible_field_specs()
            if 0 <= idx < len(specs):
                return FIELD_HELP[specs[idx][1]]
        else:
            idx = selected_idx()
            if 0 <= idx < len(OPTION_SPECS):
                return OPTION_SPECS[idx][2]
        return ""

    return Box(
        Text(lambda: f" CATALOG_JDBC_URI (auto): {jdbc_uri()}", fg="yellow"),
        Text(lambda: f" Hint: {hint()}", fg="yellow"),
        flex_direction="column",
        padding_left=1,
        padding_top=1,
    )


@component
def StatusBar() -> Any:
    def is_status_bold() -> bool:
        return status_kind() in {"error", "success"}

    return Box(
        Text(" Status: ", fg="white", bg="black", bold=True),
        Text(
            lambda: status_message(),
            fg=_reactive(_status_color),
            bg="black",
            bold=_reactive(is_status_bold),
        ),
        flex_direction="row",
        bg="black",
        padding_left=1,
    )


@component
def HelpOverlay() -> Any:
    rows = [
        ("↑/k  ↓/j", "Move selection", "cyan"),
        ("Tab", "Switch Credentials / Preferences", "cyan"),
        ("Enter / Space", "Edit field / toggle option", "cyan"),
        ("Esc", "Cancel edit / close overlay", "cyan"),
        ("M", "Toggle Basic ⇄ Advanced mode", "magenta"),
        ("R", "Review configuration", "yellow"),
        ("?", "Show / hide this help", "yellow"),
        ("S", "Save to .env", "green"),
        ("Q", "Quit without saving", "red"),
    ]
    return Box(
        Text(" Keyboard Shortcuts & Modes ", fg="black", bg="cyan", bold=True),
        *[
            Box(
                Text(f" {key:<14}", fg=color, bold=True),
                Text(descr, fg="white"),
                flex_direction="row",
                gap=1,
            )
            for key, descr, color in rows
        ],
        Text(""),
        Text(
            " Basic mode shows only key credentials with secure defaults.",
            fg="green",
        ),
        Text(
            " Advanced mode exposes every port, CIDR and upstream setting.",
            fg="magenta",
        ),
        title=" Help ",
        border=True,
        border_color="cyan",
        border_style="rounded",
        flex_grow=1,
        padding=2,
        gap=0,
    )


@component
def ReviewOverlay() -> Any:
    def config_lines() -> list[Any]:
        lines: list[Any] = []
        for label, key, is_secret, _ in visible_field_specs():
            val = field_values[key]()
            display = _display_field_value(key, val, is_secret)
            err = field_error(key, val)
            mark = "✓" if err is None and val.strip() else "✗"
            color = "green" if err is None and val.strip() else "red"
            lines.append(
                Box(
                    Text(f" {mark} {label:<22} : ", fg="white"),
                    Text(display, fg=color, bold=True),
                    flex_direction="row",
                )
            )
        return lines

    def option_lines() -> list[Any]:
        lines: list[Any] = []
        for label, key, _ in OPTION_SPECS:
            checked = "[x]" if option_values[key]() else "[ ]"
            lines.append(
                Box(
                    Text(f" {checked} {label}", fg="white"),
                    flex_direction="row",
                )
            )
        return lines

    return Box(
        Text(" Configuration Review ", fg="black", bg="cyan", bold=True),
        Text(" Credentials & Services ", fg="cyan", bold=True),
        *config_lines(),
        Text(""),
        Text(" Setup Preferences ", fg="magenta", bold=True),
        *option_lines(),
        Text(""),
        Text(" Press R or Esc to return. Press S to save. ", fg="yellow", bold=True),
        title=" Review ",
        border=True,
        border_color="cyan",
        border_style="rounded",
        flex_grow=1,
        padding=2,
        gap=0,
    )


@component
def App() -> Any:
    def body() -> Any:
        if show_help():
            return HelpOverlay()
        if show_review():
            return ReviewOverlay()
        return Box(
            CredentialsPanel(),
            SetupActionsPanel(),
            flex_direction="row",
            align_items="stretch",
            gap=2,
            flex_grow=1,
        )

    return Box(
        TitleBar(),
        ModeBar(),
        Tabs(),
        body(),
        InfoBar(),
        StatusBar(),
        flex_direction="column",
        gap=1,
        flex_grow=1,
        bg="black",
        padding=1,
    )


def _reset_tui_state() -> None:
    active_section.set("fields")
    selected_idx.set(0)
    mode.set("navigate")
    editing_field.set(-1)
    editing_original_value.set("")
    _set_status("Idle - navigate fields or press S to save", "idle")
    field_values.clear()
    option_values.clear()


def _initialise_tui_state(config: SetupConfig, options: SetupWorkflowOptions) -> None:
    _reset_tui_state()
    for _, key, _, _ in FIELD_SPECS:
        field_values[key] = Signal(
            str(getattr(config, CONFIG_ATTRS_BY_KEY[key])),
            name=f"field_{key}",
        )
    for _, key, _ in OPTION_SPECS:
        option_values[key] = Signal(bool(getattr(options, key)), name=f"opt_{key}")


async def _run_tui(config: SetupConfig, options: SetupWorkflowOptions) -> int:
    _initialise_tui_state(config, options)
    saved = False
    pending_tasks: set[asyncio.Task[Any]] = set()

    def _schedule_stop(delay: float = 0.6) -> None:
        renderer = use_renderer()

        async def _stop_later() -> None:
            await asyncio.sleep(delay)
            renderer.stop()

        task = asyncio.create_task(_stop_later())
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)

    def _commit_state() -> None:
        _apply_field_values(
            config,
            {key: field_values[key]() for key in FIELD_KEYS},
        )
        _apply_option_values(
            options,
            {key: option_values[key]() for key in OPTION_KEYS},
        )

    def on_key(event: KeyEvent) -> None:
        nonlocal saved

        if saved:
            return

        key_name = event.name.lower()

        if mode() == "edit":
            return

        # Overlay handling
        if show_help() or show_review():
            if key_name == "s":
                _commit_state()
                errors = validate_config(config)
                if errors:
                    _set_status(f"Cannot save: {errors[0]}", "error")
                    return
                write_env_file(ENV_PATH, ENV_TEMPLATE_PATH, as_env_mapping(config))
                _set_status(f"Saved configuration to {ENV_PATH}", "success")
                saved = True
                _schedule_stop()
                return
            if key_name in {"escape", "q"}:
                show_help.set(False)
                show_review.set(False)
                _set_status("Resumed editing", "idle")
            elif key_name in {"?", "h"}:
                show_help.set(not show_help())
            elif key_name == "r":
                show_review.set(not show_review())
                show_help.set(False)
            return

        if key_name == "m":
            new_mode = "advanced" if user_mode() == "basic" else "basic"
            user_mode.set(new_mode)
            selected_idx.set(0)
            _set_status(
                "Switched to "
                + ("Basic (guided) mode" if new_mode == "basic" else "Advanced mode"),
                "info",
            )
            return

        if key_name in {"?", "h"}:
            show_help.set(True)
            _set_status("Showing keyboard help. Press ? or Esc to close.", "info")
            return

        if key_name == "r":
            show_review.set(True)
            _set_status("Review your configuration. Press S to save, R/Esc to close.", "info")
            return

        if key_name == "q":
            use_renderer().stop()
            return

        if key_name == "tab":
            if active_section() == "fields":
                active_section.set("options")
            else:
                active_section.set("fields")
            selected_idx.set(0)
            _set_status(
                "Switched to "
                + ("credentials" if active_section() == "fields" else "setup preferences"),
                "idle",
            )
            return

        if key_name in {"up", "k"}:
            if active_section() == "fields":
                selected_idx.set((selected_idx() - 1) % len(visible_field_specs()))
            else:
                selected_idx.set((selected_idx() - 1) % len(OPTION_SPECS))
            return

        if key_name in {"down", "j"}:
            if active_section() == "fields":
                selected_idx.set((selected_idx() + 1) % len(visible_field_specs()))
            else:
                selected_idx.set((selected_idx() + 1) % len(OPTION_SPECS))
            return

        if key_name in {"return", "enter", "linefeed"}:
            if active_section() == "fields":
                specs = visible_field_specs()
                idx = selected_idx()
                editing_field.set(idx)
                editing_original_value.set(field_values[specs[idx][1]]())
                mode.set("edit")
                _set_status(f"Editing {specs[idx][0]}", "info")
            else:
                label, key, _ = OPTION_SPECS[selected_idx()]
                option_values[key].set(not option_values[key]())
                _set_status(f"Toggled {label}", "success")
            return

        if key_name in {" ", "space"}:
            if active_section() == "options":
                label, key, _ = OPTION_SPECS[selected_idx()]
                option_values[key].set(not option_values[key]())
                _set_status(f"Toggled {label}", "success")
            return

        if key_name == "s":
            _commit_state()
            errors = validate_config(config)
            if errors:
                _set_status(f"Cannot save: {errors[0]}", "error")
                return

            write_env_file(ENV_PATH, ENV_TEMPLATE_PATH, as_env_mapping(config))
            _set_status(f"Saved configuration to {ENV_PATH}", "success")
            saved = True
            _schedule_stop()
            return

    use_keyboard(on_key)
    await render(App)
    return 0 if saved else 1


def _run_prompt_fallback(config: SetupConfig) -> int:
    options = SetupWorkflowOptions()
    print("Using prompt wizard mode instead.")
    print("Press Enter to keep the current value.")

    for label, key, _, _ in FIELD_SPECS:
        current = getattr(config, CONFIG_ATTRS_BY_KEY[key])
        entered = input(f"{label} [{current}]: ").strip()
        if entered:
            setattr(config, CONFIG_ATTRS_BY_KEY[key], entered)

    print("\nChoose first-setup actions:")
    for label, key, _ in OPTION_SPECS:
        default_enabled = bool(getattr(options, key))
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
        help="Use prompt-mode wizard even when OpenTUI is available.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = load_initial_config()
    options = SetupWorkflowOptions()
    import sys

    if args.prompt or not sys.stdout.isatty():
        return _run_prompt_fallback(config)

    status = asyncio.run(_run_tui(config, options))
    if status == 0:
        print("")
        print("\n".join(build_setup_guide(config, options)))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
