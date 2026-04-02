import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.constants import CHAIN_COLORS, CHAIN_NAMES


def render_report(df: pd.DataFrame, selected_chain_id: str):
    chain_df = df[df["chain_id"] == selected_chain_id].copy()
    chain_name = CHAIN_NAMES.get(selected_chain_id, selected_chain_id)
    color = CHAIN_COLORS.get(selected_chain_id, "#888888")

    if chain_df.empty:
        st.warning(f"{chain_name} のデータがありません")
        return

    valid_dates = chain_df[chain_df["open_date"].notna()]
    total = len(chain_df)
    prefs = chain_df["prefecture"].nunique()
    closed = chain_df["close_date"].notna().sum()
    active = total - closed

    if not valid_dates.empty:
        first_open = valid_dates["open_date"].min().strftime("%Y年%m月")
        latest_open = valid_dates["open_date"].max().strftime("%Y年%m月")
        months_active = (
            (valid_dates["open_date"].max() - valid_dates["open_date"].min()).days / 30
        )
        pace = round(total / months_active, 1) if months_active > 0 else "-"
    else:
        first_open = "不明"
        latest_open = "不明"
        pace = "-"

    # KPIカード
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("総店舗数", total)
    col2.metric("現存店舗", active)
    col3.metric("出店都道府県数", prefs)
    col4.metric("初出店", first_open)
    col5.metric("出店ペース", f"{pace} 店/月" if pace != "-" else "-")

    st.divider()

    col_left, col_right = st.columns(2)

    # 累計出店数推移
    with col_left:
        st.subheader("累計出店数推移")
        if not valid_dates.empty:
            ts = (
                valid_dates.set_index("open_date")
                .resample("ME")
                .size()
                .cumsum()
                .reset_index()
            )
            ts.columns = ["date", "cumulative"]
            fig = px.line(
                ts, x="date", y="cumulative",
                color_discrete_sequence=[color],
                labels={"date": "年月", "cumulative": "累計店舗数"},
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("開店日データなし")

    # 月次出店数
    with col_right:
        st.subheader("月次出店数")
        if not valid_dates.empty:
            monthly = (
                valid_dates.set_index("open_date")
                .resample("ME")
                .size()
                .reset_index()
            )
            monthly.columns = ["date", "count"]
            fig = px.bar(
                monthly, x="date", y="count",
                color_discrete_sequence=[color],
                labels={"date": "年月", "count": "出店数"},
            )
            # 12ヶ月移動平均
            monthly["ma12"] = monthly["count"].rolling(12, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=monthly["date"], y=monthly["ma12"],
                mode="lines", name="12ヶ月移動平均",
                line=dict(color="gray", dash="dash"),
            ))
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("開店日データなし")

    col_left2, col_right2 = st.columns(2)

    # 都道府県別店舗数
    with col_left2:
        st.subheader("都道府県別店舗数")
        pref_df = (
            chain_df[chain_df["prefecture"] != ""]
            .groupby("prefecture")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=True)
        )
        if not pref_df.empty:
            fig = px.bar(
                pref_df, x="count", y="prefecture",
                orientation="h",
                color_discrete_sequence=[color],
                labels={"prefecture": "都道府県", "count": "店舗数"},
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=max(200, len(pref_df) * 22))
            st.plotly_chart(fig, use_container_width=True)

    # エリア別円グラフ
    with col_right2:
        st.subheader("エリア別分布")
        area_df = (
            chain_df[chain_df["area"] != "その他"]
            .groupby("area")
            .size()
            .reset_index(name="count")
        )
        if not area_df.empty:
            fig = px.pie(
                area_df, names="area", values="count",
                hole=0.4,
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280)
            st.plotly_chart(fig, use_container_width=True)

    # 店舗一覧テーブル
    st.subheader("店舗一覧")
    show_cols = ["store_name", "prefecture", "city", "address_raw", "open_date", "open_order"]
    show_cols = [c for c in show_cols if c in chain_df.columns]
    display_df = chain_df[show_cols].copy()
    display_df.columns = [
        {"store_name": "店舗名", "prefecture": "都道府県", "city": "市区町村",
         "address_raw": "住所", "open_date": "開店日", "open_order": "出店順"}
        .get(c, c)
        for c in show_cols
    ]
    st.dataframe(display_df, use_container_width=True, height=400)


def render_comparison(df: pd.DataFrame):
    st.subheader("チェーン比較")

    rows = []
    for chain_id, group in df.groupby("chain_id"):
        valid = group[group["open_date"].notna()]
        closed = group["close_date"].notna().sum()
        months = (
            ((valid["open_date"].max() - valid["open_date"].min()).days / 30)
            if len(valid) > 1 else 0
        )
        rows.append({
            "チェーン": CHAIN_NAMES.get(chain_id, chain_id),
            "総店舗数": len(group),
            "現存": len(group) - int(closed),
            "都道府県数": group["prefecture"].nunique(),
            "初出店": valid["open_date"].min().strftime("%Y年%m月") if not valid.empty else "不明",
            "最新出店": valid["open_date"].max().strftime("%Y年%m月") if not valid.empty else "不明",
            "出店ペース(店/月)": round(len(group) / months, 1) if months > 0 else "-",
        })

    comp_df = pd.DataFrame(rows)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    # 累計出店数比較
    st.subheader("累計出店数比較")
    plot_data = []
    colors = []
    for chain_id, group in df.groupby("chain_id"):
        valid = group[group["open_date"].notna()].copy()
        if valid.empty:
            continue
        ts = (
            valid.set_index("open_date")
            .resample("ME")
            .size()
            .cumsum()
            .reset_index()
        )
        ts.columns = ["date", "cumulative"]
        ts["chain"] = CHAIN_NAMES.get(chain_id, chain_id)
        plot_data.append(ts)
        colors.append(CHAIN_COLORS.get(chain_id, "#888"))

    if plot_data:
        import pandas as pd
        combined = pd.concat(plot_data, ignore_index=True)
        fig = px.line(
            combined, x="date", y="cumulative",
            color="chain",
            color_discrete_sequence=list(CHAIN_COLORS.values()),
            labels={"date": "年月", "cumulative": "累計店舗数", "chain": "チェーン"},
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320)
        st.plotly_chart(fig, use_container_width=True)
