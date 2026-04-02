from __future__ import annotations
import pandas as pd
from pathlib import Path
from utils.constants import AREA_MAP, CSV_COLUMNS

DATA_PATH = Path(__file__).parent.parent / "data" / "stores.csv"


def load_stores() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)

    df = pd.read_csv(DATA_PATH, dtype={"store_id": str})

    df["open_date"] = pd.to_datetime(df["open_date"], errors="coerce")
    df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")

    if "prefecture" in df.columns:
        df["area"] = df["prefecture"].map(AREA_MAP).fillna("その他")
    else:
        df["area"] = "その他"

    # 出店順（チェーン内）
    df = df.sort_values("open_date")
    df["open_order"] = df.groupby("chain_id").cumcount() + 1

    return df


def filter_stores(
    df: pd.DataFrame,
    selected_chains: list[str] | None = None,
    date_range: tuple | None = None,
    prefectures: list[str] | None = None,
    exclude_closed: bool = True,
) -> pd.DataFrame:
    result = df.copy()

    if selected_chains:
        result = result[result["chain_id"].isin(selected_chains)]

    if date_range and date_range[0] and date_range[1]:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        result = result[
            result["open_date"].isna() | (
                (result["open_date"] >= start) & (result["open_date"] <= end)
            )
        ]

    if prefectures:
        result = result[result["prefecture"].isin(prefectures)]

    if exclude_closed:
        result = result[result["close_date"].isna()]

    result = result.dropna(subset=["lat", "lng"])

    return result
