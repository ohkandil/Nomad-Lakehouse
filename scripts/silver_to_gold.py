from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class GoldConfig:
    input_csv: Path = Path("data/output/silver_orders.csv")
    output_csv: Path = Path("data/output/gold_daily_revenue.csv")


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby("order_date", as_index=False)
        .agg(total_revenue=("amount", "sum"), order_count=("order_id", "count"))
        .sort_values("order_date")
    )
    return grouped


def main() -> None:
    config = GoldConfig()
    config.output_csv.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(config.input_csv)
    gold_df = aggregate(df)
    gold_df.to_csv(config.output_csv, index=False)

    print(f"[gold] Wrote {len(gold_df)} rows to {config.output_csv}")


if __name__ == "__main__":
    main()
