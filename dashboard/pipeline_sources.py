from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from dashboard.models import PipelineStageStatus, PipelineStatus, QualityCheck, QualityStatus

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "output"
CONTRACT_DIR = ROOT / "data" / "contracts"
CONTRACT_PATH = CONTRACT_DIR / "bronze_orders_contract.json"
DUCKDB_PATH = OUTPUT_DIR / "lakehouse.duckdb"
SILVER_PATH = OUTPUT_DIR / "silver_orders.csv"
GOLD_PATH = OUTPUT_DIR / "gold_daily_revenue.csv"


def _iso_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return pd.Timestamp(path.stat().st_mtime_ns, unit="ns", tz="UTC").isoformat()


def _bronze_row_count() -> tuple[int | None, str]:
    if not DUCKDB_PATH.exists():
        return None, "DuckDB database not found"

    try:
        import duckdb
    except ImportError:
        return None, "duckdb package not installed; cannot query bronze table"

    try:
        with duckdb.connect(str(DUCKDB_PATH)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM bronze.orders").fetchone()
            if row is None:
                return None, "bronze.orders returned no row count"
            return int(row[0]), "bronze.orders row count loaded"
    except Exception as exc:  # pragma: no cover - defensive path for local runtime variance
        return None, f"Unable to query bronze.orders: {exc}"


def _csv_stage(layer: str, path: Path) -> PipelineStageStatus:
    if not path.exists():
        return PipelineStageStatus(
            layer=layer,
            status="fail",
            row_count=None,
            last_updated=None,
            detail=f"Missing artifact: {path.relative_to(ROOT)}",
        )

    df = pd.read_csv(path)
    return PipelineStageStatus(
        layer=layer,
        status="ok",
        row_count=len(df),
        last_updated=_iso_mtime(path),
        detail=f"Loaded {len(df)} rows from {path.relative_to(ROOT)}",
    )


def collect_pipeline_status() -> PipelineStatus:
    bronze_row_count, bronze_detail = _bronze_row_count()
    contract_exists = CONTRACT_PATH.exists()

    bronze_status: Literal["ok", "warn", "fail"]
    if contract_exists and bronze_row_count is not None:
        bronze_status = "ok"
    elif contract_exists:
        bronze_status = "warn"
    else:
        bronze_status = "fail"

    contract_message = (
        f"contract={CONTRACT_PATH.relative_to(ROOT)} present"
        if contract_exists
        else f"contract={CONTRACT_PATH.relative_to(ROOT)} missing"
    )
    bronze = PipelineStageStatus(
        layer="bronze",
        status=bronze_status,
        row_count=bronze_row_count,
        last_updated=_iso_mtime(CONTRACT_PATH) if contract_exists else None,
        detail=f"{contract_message}; {bronze_detail}",
    )

    silver = _csv_stage("silver", SILVER_PATH)
    gold = _csv_stage("gold", GOLD_PATH)

    return PipelineStatus(stages=[bronze, silver, gold])


def _freshness_check(name: str, path: Path, threshold_hours: float = 24.0) -> QualityCheck:
    if not path.exists():
        return QualityCheck(name=name, status="fail", value="missing", detail="Artifact missing")

    modified = pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC")
    age = pd.Timestamp.now(tz="UTC") - modified
    age_hours = age.total_seconds() / 3600

    if age_hours <= threshold_hours:
        return QualityCheck(
            name=f"{name} freshness",
            status="ok",
            value=f"{age_hours:.1f}h",
            detail="Within freshness target",
        )

    return QualityCheck(
        name=f"{name} freshness",
        status="warn",
        value=f"{age_hours:.1f}h",
        detail=f"Older than freshness target ({threshold_hours:.0f}h)",
    )


def collect_quality_status() -> QualityStatus:
    checks: list[QualityCheck] = []

    checks.append(_freshness_check("silver", SILVER_PATH))
    checks.append(_freshness_check("gold", GOLD_PATH))

    if SILVER_PATH.exists():
        silver_df = pd.read_csv(SILVER_PATH)
        duplicate_orders = int(silver_df.duplicated(subset=["order_id"]).sum())
        null_amount = int(silver_df["amount"].isna().sum()) if "amount" in silver_df.columns else -1

        checks.append(
            QualityCheck(
                name="silver duplicate order_id",
                status="ok" if duplicate_orders == 0 else "warn",
                value=str(duplicate_orders),
                detail="Expected 0 duplicates",
            )
        )
        checks.append(
            QualityCheck(
                name="silver null amount",
                status="ok" if null_amount == 0 else "warn",
                value=str(null_amount),
                detail="Expected 0 null amount values",
            )
        )

    if GOLD_PATH.exists():
        gold_df = pd.read_csv(GOLD_PATH)
        if "total_revenue" in gold_df.columns:
            negative_revenue = int((gold_df["total_revenue"] < 0).sum())
        else:
            negative_revenue = -1
        checks.append(
            QualityCheck(
                name="gold negative revenue rows",
                status="ok" if negative_revenue == 0 else "fail",
                value=str(negative_revenue),
                detail="Expected 0 negative revenue rows",
            )
        )

    return QualityStatus(checks=checks)
