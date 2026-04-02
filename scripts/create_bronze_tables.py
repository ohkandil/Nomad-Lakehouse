from __future__ import annotations

import csv
from pathlib import Path

from pydantic import BaseModel, Field


class BronzeOrder(BaseModel):
    order_id: int = Field(ge=1)
    customer_id: int = Field(ge=1)
    order_date: str
    amount: float = Field(ge=0)
    status: str


def read_orders_csv(path: Path) -> list[BronzeOrder]:
    rows: list[BronzeOrder] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                BronzeOrder(
                    order_id=int(row["order_id"]),
                    customer_id=int(row["customer_id"]),
                    order_date=row["order_date"],
                    amount=float(row["amount"]),
                    status=row["status"],
                )
            )
    return rows


def main() -> None:
    sample_path = Path("data/sample/orders.csv")
    orders = read_orders_csv(sample_path)
    print(f"[bronze] Validated {len(orders)} rows from {sample_path}")
    print("[bronze] Next step: write rows to Iceberg REST catalog table")


if __name__ == "__main__":
    main()
