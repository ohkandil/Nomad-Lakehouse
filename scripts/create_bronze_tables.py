from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class BronzeOrder(BaseModel):
    order_id: int = Field(ge=1)
    customer_id: int = Field(ge=1)
    order_date: date
    amount: Decimal = Field(ge=0)
    status: Literal["Pending", "Completed", "Cancelled"]


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and stage bronze order rows from CSV")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/sample/orders.csv"),
        help="Path to source orders CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input

    orders = read_orders_csv(input_path)
    print(f"[bronze] Validated {len(orders)} rows from {input_path}")
    print("[bronze] Next step: write rows to Iceberg table via JDBC catalog backend")


if __name__ == "__main__":
    main()
