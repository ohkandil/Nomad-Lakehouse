from __future__ import annotations

from pathlib import Path

from scripts.configure_setup_tui import (
    SetupConfig,
    as_env_mapping,
    parse_env_file,
    validate_config,
    write_env_file,
)


def test_parse_env_file_ignores_comments_and_invalid_lines(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\nMINIO_ROOT_USER=admin\ninvalid-line\nPOSTGRES_PORT=5432\n",
        encoding="utf-8",
    )

    values = parse_env_file(env_file)

    assert values == {"MINIO_ROOT_USER": "admin", "POSTGRES_PORT": "5432"}


def test_as_env_mapping_sets_catalog_uri_from_postgres_db_and_port() -> None:
    config = SetupConfig(
        minio_root_user="admin",
        minio_root_password="0123456789abcdef",
        minio_api_port="9000",
        minio_console_port="9001",
        warehouse_bucket="warehouse",
        postgres_db="catalog",
        postgres_user="iceberg",
        postgres_password="abcdefghijklmnop",
        postgres_port="15432",
        aws_region="us-east-1",
        dashboard_domain="dashboard.home.arpa",
        dashboard_auth_user="admin",
        dashboard_allowed_cidrs="192.168.0.0/16 10.0.0.0/8",
    )

    values = as_env_mapping(config)

    assert values["CATALOG_JDBC_URI"] == "jdbc:postgresql://localhost:15432/catalog"


def test_validate_config_rejects_invalid_port_and_weak_password() -> None:
    config = SetupConfig(
        minio_root_user="admin",
        minio_root_password="short",
        minio_api_port="70000",
        minio_console_port="9001",
        warehouse_bucket="warehouse",
        postgres_db="iceberg",
        postgres_user="iceberg",
        postgres_password="short",
        postgres_port="5432",
        aws_region="us-east-1",
        dashboard_domain="dashboard.home.arpa",
        dashboard_auth_user="admin",
        dashboard_allowed_cidrs="192.168.0.0/16",
    )

    errors = validate_config(config)

    assert "MINIO_ROOT_PASSWORD must be at least 16 characters" in errors
    assert "MINIO_API_PORT must be between 1 and 65535" in errors
    assert "POSTGRES_PASSWORD must be at least 16 characters" in errors


def test_write_env_file_preserves_comments_and_updates_values(tmp_path: Path) -> None:
    template_file = tmp_path / ".env.example"
    env_file = tmp_path / ".env"
    template_file.write_text(
        (
            "# MinIO\n"
            "MINIO_ROOT_USER=minioadmin\n"
            "POSTGRES_DB=iceberg\n"
            "DASHBOARD_DOMAIN=dashboard.home.arpa\n"
        ),
        encoding="utf-8",
    )
    env_file.write_text(
        "UNMANAGED_FLAG=enabled\nDASHBOARD_DOMAIN=old.home.arpa\n",
        encoding="utf-8",
    )

    write_env_file(
        env_file,
        template_file,
        {
            "MINIO_ROOT_USER": "new-admin",
            "POSTGRES_DB": "catalog",
            "AWS_REGION": "us-east-1",
            "DASHBOARD_DOMAIN": "dashboard.example.local",
        },
    )

    content = env_file.read_text(encoding="utf-8")
    assert "# MinIO" in content
    assert "MINIO_ROOT_USER=new-admin" in content
    assert "POSTGRES_DB=catalog" in content
    assert "AWS_REGION=us-east-1" in content
    assert "DASHBOARD_DOMAIN=dashboard.example.local" in content
    assert "UNMANAGED_FLAG=enabled" in content
