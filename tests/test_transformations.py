from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[1]
bronze_module = _load_module("bronze_to_silver", ROOT / "scripts" / "bronze_to_silver.py")
gold_module = _load_module("silver_to_gold", ROOT / "scripts" / "silver_to_gold.py")

transform = bronze_module.transform
aggregate = gold_module.aggregate


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
