import pandas as pd
import plotly.express as px
import streamlit as st
from utils.constants import CHAIN_COLORS, CHAIN_NAMES


def render_timeline(df: pd.DataFrame):
    valid_df = df[df["open_date"].notna()].copy()

    if valid_df.empty:
        st.warning("開店日データがありません")
        return

    min_date = valid_df["open_date"].min()
    max_date = valid_df["open_date"].max()

    st.subheader("出店タイムライン")

    # 月次スライダー
    all_months = pd.date_range(
        start=min_date.replace(day=1),
        end=max_date.replace(day=1),
        freq="MS",
    )
    if len(all_months) == 0:
        st.info("データ不足")
        return

    month_labels = [d.strftime("%Y/%m") for d in all_months]
    selected_idx = st.select_slider(
        "表示する期間（この月までの出店を表示）",
        options=list(range(len(month_labels))),
        value=len(month_labels) - 1,
        format_func=lambda i: month_labels[i],
    )
    cutoff = all_months[selected_idx] + pd.offsets.MonthEnd(0)

    filtered = valid_df[valid_df["open_date"] <= cutoff]

    col1, col2, col3 = st.columns(3)
    col1.metric("表示店舗数", len(filtered))
    col2.metric(
        "期間",
        f"{min_date.strftime('%Y/%m')} 〜 {all_months[selected_idx].strftime('%Y/%m')}",
    )
    col3.metric("チェーン数", filtered["chain_id"].nunique())

    # 月次出店数棒グラフ（チェーン別積み上げ）
    st.subheader("月次出店数")
    monthly = (
        valid_df[valid_df["open_date"] <= cutoff]
        .assign(month=lambda x: x["open_date"].dt.to_period("M").dt.to_timestamp())
        .groupby(["month", "chain_id"])
        .size()
        .reset_index(name="count")
    )
    monthly["chain_name"] = monthly["chain_id"].map(CHAIN_NAMES)

    if not monthly.empty:
        fig = px.bar(
            monthly, x="month", y="count",
            color="chain_name",
            color_discrete_map={v: CHAIN_COLORS[k] for k, v in CHAIN_NAMES.items()},
            labels={"month": "年月", "count": "出店数", "chain_name": "チェーン"},
            barmode="stack",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=260)
        st.plotly_chart(fig, use_container_width=True)

    # 出店ヒートマップ（年×月）
    st.subheader("出店ヒートマップ（年×月）")
    heatmap_data = (
        valid_df.assign(
            year=valid_df["open_date"].dt.year,
            month=valid_df["open_date"].dt.month,
        )
        .groupby(["year", "month"])
        .size()
        .reset_index(name="count")
    )
    if not heatmap_data.empty:
        pivot = heatmap_data.pivot(index="year", columns="month", values="count").fillna(0)
        pivot.columns = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"][: len(pivot.columns)]
        import plotly.graph_objects as go
        fig_hm = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=[str(y) for y in pivot.index],
            colorscale="YlOrRd",
            text=pivot.values.astype(int),
            texttemplate="%{text}",
        ))
        fig_hm.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=max(180, len(pivot) * 30),
            xaxis_title="月",
            yaxis_title="年",
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    # チェーン別出店マイルストーン（最初の10店）
    st.subheader("初期出店マイルストーン（チェーン別 最初の10店）")
    milestone_data = []
    for chain_id, group in valid_df.groupby("chain_id"):
        top10 = group.nsmallest(10, "open_date")
        for _, row in top10.iterrows():
            milestone_data.append({
                "chain": CHAIN_NAMES.get(chain_id, chain_id),
                "store_name": row["store_name"],
                "open_date": row["open_date"],
                "open_order": int(row.get("open_order", 0)),
                "prefecture": row.get("prefecture", ""),
            })

    if milestone_data:
        ms_df = pd.DataFrame(milestone_data)
        fig_ms = px.scatter(
            ms_df, x="open_date", y="chain",
            color="chain",
            color_discrete_map={v: CHAIN_COLORS[k] for k, v in CHAIN_NAMES.items()},
            hover_data=["store_name", "prefecture", "open_order"],
            labels={"open_date": "開店日", "chain": "チェーン"},
            size_max=12,
        )
        fig_ms.update_traces(marker=dict(size=10))
        fig_ms.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=250,
            showlegend=False,
        )
        st.plotly_chart(fig_ms, use_container_width=True)
