from __future__ import annotations

import pandas as pd
import pytest

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
                "order_date": "2026-03-02",
                "amount": 2.0,
                "status": "Completed",
            },
        ]
    )
    out = transform(df)
    assert len(out) == 1
    assert float(out.iloc[0]["amount"]) == 2.0
    assert str(out.iloc[0]["order_date"]) == "2026-03-02"


def test_transform_cleans_and_filters_invalid_rows() -> None:
    df = pd.DataFrame(
        [
            {
                "order_id": 1,
                "customer_id": 10,
                "order_date": "2026-03-01",
                "amount": "10.5",
                "status": " Completed ",
            },
            {
                "order_id": 2,
                "customer_id": 11,
                "order_date": "not-a-date",
                "amount": 5,
                "status": "pending",
            },
            {
                "order_id": 3,
                "customer_id": 12,
                "order_date": "2026-03-02",
                "amount": -1,
                "status": "pending",
            },
            {
                "order_id": 4,
                "customer_id": 13,
                "order_date": "2026-03-03",
                "amount": 7,
                "status": "unknown",
            },
        ]
    )

    out = transform(df)

    assert len(out) == 1
    assert str(out.iloc[0]["status"]) == "completed"
    assert str(out.iloc[0]["order_date"]) == "2026-03-01"


def test_transform_raises_on_missing_required_columns() -> None:
    df = pd.DataFrame(
        [
            {
                "order_id": 1,
                "customer_id": 10,
                "order_date": "2026-03-01",
                "amount": 10.0,
            }
        ]
    )

    with pytest.raises(ValueError, match="missing required columns"):
        transform(df)


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
