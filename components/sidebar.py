import pandas as pd
import streamlit as st
from utils.constants import CHAIN_NAMES, CHAIN_COLORS, PREFECTURES
from pathlib import Path


def render_sidebar(df: pd.DataFrame) -> dict:
    st.sidebar.title("フィルター")

    # チェーン選択
    st.sidebar.subheader("チェーン")
    available_chains = df["chain_id"].unique().tolist() if not df.empty else []
    selected_chains = []
    for chain_id in available_chains:
        color = CHAIN_COLORS.get(chain_id, "#888")
        name = CHAIN_NAMES.get(chain_id, chain_id)
        count = len(df[df["chain_id"] == chain_id])
        checked = st.sidebar.checkbox(
            f"● {name} ({count}店)",
            value=True,
            key=f"chain_{chain_id}",
        )
        if checked:
            selected_chains.append(chain_id)

    st.sidebar.divider()

    # 日付フィルター
    st.sidebar.subheader("出店期間")
    valid_dates = df[df["open_date"].notna()]
    if not valid_dates.empty:
        min_year = int(valid_dates["open_date"].dt.year.min())
        max_year = int(valid_dates["open_date"].dt.year.max())
    else:
        min_year, max_year = 2010, 2026

    year_range = st.sidebar.slider(
        "開店年",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
    )
    date_range = (f"{year_range[0]}-01-01", f"{year_range[1]}-12-31")

    st.sidebar.divider()

    # 都道府県フィルター
    st.sidebar.subheader("都道府県")
    available_prefs = sorted(df["prefecture"].dropna().unique().tolist())
    available_prefs = [p for p in available_prefs if p]

    select_all = st.sidebar.checkbox("すべて選択", value=True, key="pref_all")
    if select_all:
        selected_prefs = available_prefs
    else:
        selected_prefs = st.sidebar.multiselect(
            "都道府県を選択",
            options=available_prefs,
            default=available_prefs[:5] if available_prefs else [],
        )

    st.sidebar.divider()

    # 現存店舗のみ
    exclude_closed = st.sidebar.checkbox("閉店店舗を除外", value=True)

    st.sidebar.divider()

    # 地図オプション
    st.sidebar.subheader("地図オプション")
    use_cluster = st.sidebar.checkbox("マーカークラスタ", value=True)
    show_number = st.sidebar.checkbox("出店番号を表示", value=True)

    st.sidebar.divider()

    # データ更新情報
    scraped_dates = df["scraped_at"].dropna() if "scraped_at" in df.columns else pd.Series()
    if not scraped_dates.empty:
        latest = pd.to_datetime(scraped_dates).max()
        st.sidebar.caption(f"データ更新: {latest.strftime('%Y-%m-%d')}")
    else:
        st.sidebar.caption("データ未取得")

    # データ更新ボタン（ローカル実行時のみ有効）
    if st.sidebar.button("データを再取得", help="ローカル環境でのみ実行可能"):
        st.sidebar.warning("ターミナルで `python -m pipeline.build_dataset` を実行してください")

    return {
        "selected_chains": selected_chains,
        "date_range": date_range,
        "selected_prefs": selected_prefs if not select_all else None,
        "exclude_closed": exclude_closed,
        "use_cluster": use_cluster,
        "show_number": show_number,
    }
