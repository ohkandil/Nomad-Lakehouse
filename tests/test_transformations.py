from __future__ import annotations

import pandas as pd

from scripts.bronze_to_silver import transform
from scripts.silver_to_gold import aggregate


def test_transform_removes_duplicate_order_ids() -> None:
    df = pd.DataFrame(
        [
            {
                "order_id": 1,
                "customer_id": 10,
                "order_date": "2026-03-01",
                "amount": 1.0,
                "status": "Completed",
            },
            {
                "order_id": 1,
                "customer_id": 10,
                "order_date": "2026-03-01",
                "amount": 1.0,
                "status": "Completed",
            },
        ]
    )
    out = transform(df)
    assert len(out) == 1


def test_aggregate_computes_daily_totals() -> None:
    df = pd.DataFrame(
        [
            {"order_id": 1, "order_date": "2026-03-01", "amount": 10.0},
            {"order_id": 2, "order_date": "2026-03-01", "amount": 5.0},
            {"order_id": 3, "order_date": "2026-03-02", "amount": 7.0},
        ]
    )
    out = aggregate(df)
    assert len(out) == 2
    assert float(out.loc[out["order_date"] == "2026-03-01", "total_revenue"].iloc[0]) == 15.0
