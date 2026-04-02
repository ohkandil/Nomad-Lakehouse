from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SilverConfig:
    input_csv: Path = Path("data/sample/orders.csv")
    output_csv: Path = Path("data/output/silver_orders.csv")


def transform(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned = cleaned.drop_duplicates(subset=["order_id"])
    cleaned["status"] = cleaned["status"].str.lower().str.strip()
    cleaned = cleaned[cleaned["amount"] >= 0]
    return cleaned


def main() -> None:
    config = SilverConfig()
    config.output_csv.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(config.input_csv)
    silver_df = transform(df)
    silver_df.to_csv(config.output_csv, index=False)

    print(f"[silver] Wrote {len(silver_df)} rows to {config.output_csv}")


if __name__ == "__main__":
    main()
