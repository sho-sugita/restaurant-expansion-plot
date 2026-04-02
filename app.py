import streamlit as st
from streamlit_folium import st_folium

from utils.data_loader import load_stores, filter_stores
from components.sidebar import render_sidebar
from components.map_view import build_map
from components.timeline_view import render_timeline
from components.report_view import render_report, render_comparison

st.set_page_config(
    page_title="飲食チェーン 出店マップ",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カスタムCSS
st.markdown("""
<style>
    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1A1A1A;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #666;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stMetric"] {
        background: #f9f9f9;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #eee;
    }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🗺️ 飲食チェーン 出店マップ & 分析ダッシュボード</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">競合チェーンの出店エリア・出店順・出店ペースを可視化し、立地戦略に活用する</p>', unsafe_allow_html=True)

# データ読み込み
@st.cache_data(ttl=3600)
def get_data():
    return load_stores()

df = get_data()

if df.empty:
    st.error("""
    **データがありません**

    以下のコマンドでデータを取得してください：
    ```bash
    # 依存関係のインストール
    pip install -r requirements.txt
    playwright install chromium

    # データ取得
    python -m pipeline.build_dataset
    ```
    """)
    st.stop()

# サイドバー
filters = render_sidebar(df)
filtered_df = filter_stores(
    df,
    selected_chains=filters["selected_chains"],
    date_range=filters["date_range"],
    prefectures=filters["selected_prefs"],
    exclude_closed=filters["exclude_closed"],
)

# タブ
tab_map, tab_timeline, tab_report, tab_compare = st.tabs([
    "📍 地図", "📅 タイムライン", "📊 チェーンレポート", "⚖️ 比較"
])

# ── 地図タブ ──────────────────────────────────────────
with tab_map:
    col_info, col_opt = st.columns([3, 1])
    with col_info:
        total = len(df[df["close_date"].isna()])
        st.caption(
            f"表示: **{len(filtered_df)}店舗** / 全{total}店舗（現存）"
        )
    with col_opt:
        pass  # サイドバーでオプション設定済み

    if filtered_df.empty:
        st.warning("条件に該当する店舗がありません")
    else:
        m = build_map(
            filtered_df,
            use_cluster=filters["use_cluster"],
            show_number=filters["show_number"],
        )
        st_folium(m, width="100%", height=580, returned_objects=[])

# ── タイムラインタブ ──────────────────────────────────
with tab_timeline:
    render_timeline(filtered_df)

# ── チェーンレポートタブ ─────────────────────────────
with tab_report:
    available_chains = filtered_df["chain_id"].unique().tolist()
    if not available_chains:
        st.warning("データがありません")
    else:
        from utils.constants import CHAIN_NAMES
        chain_options = {CHAIN_NAMES.get(c, c): c for c in available_chains}
        selected_chain_name = st.selectbox(
            "チェーンを選択",
            options=list(chain_options.keys()),
        )
        selected_chain_id = chain_options[selected_chain_name]
        render_report(df, selected_chain_id)

# ── 比較タブ ──────────────────────────────────────────
with tab_compare:
    render_comparison(df)

# フッター
st.divider()
st.caption("データは各チェーン公式サイトから取得。開店日不明の店舗は一部除外される場合があります。")
