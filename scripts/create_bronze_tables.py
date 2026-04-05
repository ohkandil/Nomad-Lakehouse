from __future__ import annotations

import argparse
import csv
import json
import os
import re
import socket
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError


class BronzeOrder(BaseModel):
    order_id: int = Field(ge=1)
    customer_id: int = Field(ge=1)
    order_date: date
    amount: Decimal = Field(ge=0)
    status: Literal["Pending", "Completed", "Cancelled"]


class JdbcTarget(BaseModel):
    host: str
    port: int = Field(ge=1, le=65535)
    database: str


def read_orders_csv(path: Path) -> list[BronzeOrder]:
    required_columns = {"order_id", "customer_id", "order_date", "amount", "status"}

    rows: list[BronzeOrder] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header row: {path}")

        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV is missing required columns ({missing}): {path}")

        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(BronzeOrder.model_validate(row))
            except ValidationError as exc:
                raise ValueError(
                    f"Invalid data at row {row_number} in {path}: {exc.errors()}"
                ) from exc
            except KeyError as exc:
                raise ValueError(
                    f"Missing column {exc!s} at row {row_number} in {path}"
                ) from exc
    return rows


def parse_jdbc_target(jdbc_uri: str) -> JdbcTarget:
    pattern = r"^jdbc:postgresql://(?P<host>[^:/]+):(?P<port>\d+)/(?P<database>[A-Za-z0-9_\-]+)$"
    match = re.match(pattern, jdbc_uri)
    if match is None:
        raise ValueError(
            "CATALOG_JDBC_URI must match jdbc:postgresql://<host>:<port>/<database>"
        )

    return JdbcTarget(
        host=match.group("host"),
        port=int(match.group("port")),
        database=match.group("database"),
    )


def validate_catalog_connectivity(jdbc_uri: str, timeout_seconds: float = 2.0) -> tuple[str, int]:
    target = parse_jdbc_target(jdbc_uri)
    host_candidates = [target.host]
    if target.host == "postgres":
        host_candidates.append("localhost")

    for host in host_candidates:
        try:
            with socket.create_connection((host, target.port), timeout=timeout_seconds):
                return host, target.port
        except OSError:
            continue

    raise ConnectionError(
        f"Unable to connect to PostgreSQL catalog backend on {target.host}:{target.port}"
    )


def write_ingestion_contract(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    contract_payload = {
        "dataset": "orders",
        "layer": "bronze",
        "version": "1.0.0",
        "required_columns": [
            {"name": "order_id", "type": "int", "constraints": ["required", "min=1"]},
            {"name": "customer_id", "type": "int", "constraints": ["required", "min=1"]},
            {"name": "order_date", "type": "date", "constraints": ["required", "iso-8601"]},
            {"name": "amount", "type": "decimal", "constraints": ["required", "min=0"]},
            {
                "name": "status",
                "type": "enum",
                "constraints": ["required", "Pending|Completed|Cancelled"],
            },
        ],
        "idempotency": "Bronze load uses CREATE OR REPLACE semantics in DuckDB",
    }
    path.write_text(json.dumps(contract_payload, indent=2), encoding="utf-8")


def materialize_bronze_table(orders: list[BronzeOrder], database_path: Path) -> int:
    try:
        import duckdb  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "DuckDB is required for Bronze table materialization. Install with: "
            "python3 -m pip install -e '.[lakehouse]'"
        ) from exc

    database_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "order_date": order.order_date.isoformat(),
            "amount": str(order.amount),
            "status": order.status,
        }
        for order in orders
    ]
    df = pd.DataFrame(rows)

    with duckdb.connect(str(database_path)) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS bronze")
        conn.register("incoming_orders", df)
        conn.execute(
            """
            CREATE OR REPLACE TABLE bronze.orders AS
            SELECT
              CAST(order_id AS BIGINT) AS order_id,
              CAST(customer_id AS BIGINT) AS customer_id,
              CAST(order_date AS DATE) AS order_date,
              CAST(amount AS DECIMAL(18,2)) AS amount,
              CAST(status AS VARCHAR) AS status
            FROM incoming_orders
            """
        )
        row_count = conn.execute("SELECT COUNT(*) FROM bronze.orders").fetchone()
        if row_count is None:
            raise RuntimeError("Could not read row count from bronze.orders")
        return int(row_count[0])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and stage bronze order rows from CSV")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/sample/orders.csv"),
        help="Path to source orders CSV",
    )
    parser.add_argument(
        "--duckdb-db",
        type=Path,
        default=Path("data/output/lakehouse.duckdb"),
        help="Path to DuckDB database file for Bronze table materialization",
    )
    parser.add_argument(
        "--contract-output",
        type=Path,
        default=Path("data/contracts/bronze_orders_contract.json"),
        help="Path to generated Bronze ingestion contract JSON",
    )
    parser.add_argument(
        "--jdbc-uri",
        type=str,
        default=os.getenv("CATALOG_JDBC_URI", "jdbc:postgresql://postgres:5432/iceberg"),
        help="JDBC URI for PostgreSQL catalog backend connectivity validation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path: Path = args.input
    duckdb_db_path: Path = args.duckdb_db
    contract_output_path: Path = args.contract_output
    jdbc_uri: str = args.jdbc_uri

    orders = read_orders_csv(input_path)
    connected_host, connected_port = validate_catalog_connectivity(jdbc_uri)
    write_ingestion_contract(contract_output_path)
    row_count = materialize_bronze_table(orders, duckdb_db_path)

    print(f"[bronze] Validated {len(orders)} rows from {input_path}")
    print(
        f"[bronze] JDBC catalog backend reachable at {connected_host}:{connected_port} "
        f"(source URI: {jdbc_uri})"
    )
    print(f"[bronze] Wrote ingestion contract to {contract_output_path}")
    print(f"[bronze] Bronze table ready: bronze.orders ({row_count} rows) in {duckdb_db_path}")


if __name__ == "__main__":
    main()
