"""
スクレイプ → ジオコーディング → stores.csv 出力パイプライン

使い方:
  python -m pipeline.build_dataset            # 全チェーン
  python -m pipeline.build_dataset --chain gongcha crisp
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
STORES_CSV = DATA_DIR / "stores.csv"

SCRAPER_MAP = {
    "gongcha": "scrapers.gongcha_scraper.GonchaScraper",
    "crisp": "scrapers.crisp_scraper.CrispScraper",
    "withgreen": "scrapers.withgreen_scraper.WithgreenScraper",
    "deandeluca": "scrapers.deandeluca_scraper.DeanDelucaScraper",
}


def load_scraper(chain_id: str):
    module_path, class_name = SCRAPER_MAP[chain_id].rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()


def run_pipeline(chain_ids: list[str] | None = None, skip_geocode: bool = False):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if chain_ids is None:
        chain_ids = list(SCRAPER_MAP.keys())

    all_rows = []

    # 既存CSVがあれば読み込む（更新対象外のチェーンを保持）
    if STORES_CSV.exists():
        existing_df = pd.read_csv(STORES_CSV, dtype={"store_id": str})
        existing_chains = set(existing_df["chain_id"].unique())
        keep_chains = existing_chains - set(chain_ids)
        if keep_chains:
            keep_df = existing_df[existing_df["chain_id"].isin(keep_chains)]
            all_rows.extend(keep_df.to_dict("records"))

    for chain_id in chain_ids:
        print(f"\n{'='*50}")
        print(f"[{chain_id}] スクレイピング開始...")
        try:
            scraper = load_scraper(chain_id)
            rows = scraper.to_rows()
            print(f"[{chain_id}] {len(rows)} 件取得")

            # rawデータ保存
            raw_path = RAW_DIR / f"{chain_id}_raw.json"
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)

            all_rows.extend(rows)
        except Exception as e:
            print(f"[{chain_id}] エラー: {e}")

    if not all_rows:
        print("取得データなし")
        return

    df = pd.DataFrame(all_rows)

    # ジオコーディング
    if not skip_geocode:
        needs_geocode = df["lat"].isna() | (df["lat"] == "") | (df["lat"] == 0)
        if needs_geocode.any():
            print(f"\nジオコーディング: {needs_geocode.sum()} 件")
            from geocoding.geocoder import geocode_dataframe
            subset = df[needs_geocode].copy()
            subset = geocode_dataframe(subset)
            df.loc[needs_geocode, "lat"] = subset["lat"].values
            df.loc[needs_geocode, "lng"] = subset["lng"].values

    # CSV保存
    df.to_csv(STORES_CSV, index=False, encoding="utf-8-sig")
    print(f"\n✓ stores.csv 保存完了: {len(df)} 件")
    print(f"  保存先: {STORES_CSV}")

    # サマリー表示
    print("\n--- チェーン別件数 ---")
    for chain_id, count in df.groupby("chain_id").size().items():
        geo_ok = df[(df["chain_id"] == chain_id) & df["lat"].notna() & (df["lat"] != "")].shape[0]
        print(f"  {chain_id}: {count} 件 (ジオコード済: {geo_ok})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chain", nargs="+", choices=list(SCRAPER_MAP.keys()))
    parser.add_argument("--skip-geocode", action="store_true")
    args = parser.parse_args()
    run_pipeline(chain_ids=args.chain, skip_geocode=args.skip_geocode)
