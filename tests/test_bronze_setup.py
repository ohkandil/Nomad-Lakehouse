from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.create_bronze_tables import (
    parse_jdbc_target,
    read_orders_csv,
    write_ingestion_contract,
)


def test_parse_jdbc_target_valid_uri() -> None:
    target = parse_jdbc_target("jdbc:postgresql://postgres:5432/iceberg")

    assert target.host == "postgres"
    assert target.port == 5432
    assert target.database == "iceberg"


def test_parse_jdbc_target_rejects_invalid_uri() -> None:
    with pytest.raises(ValueError, match="CATALOG_JDBC_URI"):
        parse_jdbc_target("postgres://localhost:5432/iceberg")


def test_read_orders_csv_rejects_missing_columns(tmp_path: Path) -> None:
    bad_csv = tmp_path / "orders.csv"
    bad_csv.write_text(
        "order_id,customer_id,order_date,amount\n1,2,2026-04-01,10.0\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required columns"):
        read_orders_csv(bad_csv)


def test_write_ingestion_contract_creates_expected_payload(tmp_path: Path) -> None:
    contract_path = tmp_path / "contracts" / "bronze_orders_contract.json"

    write_ingestion_contract(contract_path)

    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    assert payload["dataset"] == "orders"
    assert payload["layer"] == "bronze"
    assert payload["version"] == "1.0.0"
    assert isinstance(payload["required_columns"], list)
    assert len(payload["required_columns"]) == 5
