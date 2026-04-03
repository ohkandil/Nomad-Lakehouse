from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SilverConfig:
    input_csv: Path = Path("data/sample/orders.csv")
    output_csv: Path = Path("data/output/silver_orders.csv")


REQUIRED_COLUMNS = {"order_id", "customer_id", "order_date", "amount", "status"}
ALLOWED_STATUSES = {"pending", "completed", "cancelled"}


def validate_input_schema(df: pd.DataFrame) -> None:
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Input CSV is missing required columns: {missing}")


def transform(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    validate_input_schema(cleaned)

    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce")
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")
    cleaned["status"] = cleaned["status"].astype("string").str.lower().str.strip()

    cleaned = cleaned.dropna(subset=["order_id", "order_date", "amount", "status"])
    cleaned = cleaned[cleaned["amount"] >= 0]
    cleaned = cleaned[cleaned["status"].isin(ALLOWED_STATUSES)]

    # Keep the most recent record for each order_id after date normalization.
    cleaned = cleaned.sort_values("order_date").drop_duplicates(subset=["order_id"], keep="last")

    cleaned["order_date"] = cleaned["order_date"].dt.strftime("%Y-%m-%d")
    return cleaned


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean bronze orders CSV into silver output")
    parser.add_argument(
        "--input",
        type=Path,
        default=SilverConfig.input_csv,
        help="Path to source bronze orders CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=SilverConfig.output_csv,
        help="Path to target silver orders CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = SilverConfig(input_csv=args.input, output_csv=args.output)
    config.output_csv.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(config.input_csv)
    silver_df = transform(df)
    silver_df.to_csv(config.output_csv, index=False)

    dropped_rows = len(df) - len(silver_df)
    print(f"[silver] Wrote {len(silver_df)} rows to {config.output_csv} (dropped {dropped_rows})")


if __name__ == "__main__":
    main()
