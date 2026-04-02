import folium
from folium.plugins import MarkerCluster, MiniMap
import pandas as pd
from utils.constants import CHAIN_COLORS, CHAIN_NAMES


def build_map(
    df: pd.DataFrame,
    use_cluster: bool = True,
    show_number: bool = True,
    zoom_start: int = 6,
) -> folium.Map:
    center = [35.68, 139.76]  # 東京
    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles="CartoDB positron",
        control_scale=True,
    )

    MiniMap(toggle_display=True).add_to(m)

    if df.empty:
        return m

    # チェーン別レイヤー
    for chain_id in df["chain_id"].unique():
        chain_df = df[df["chain_id"] == chain_id].copy()
        chain_name = CHAIN_NAMES.get(chain_id, chain_id)
        color = CHAIN_COLORS.get(chain_id, "#888888")

        layer = folium.FeatureGroup(name=chain_name, show=True)

        if use_cluster:
            cluster = MarkerCluster(
                name=chain_name,
                options={"maxClusterRadius": 40},
            )
        else:
            cluster = layer

        for _, row in chain_df.iterrows():
            if pd.isna(row.get("lat")) or pd.isna(row.get("lng")):
                continue

            open_date_str = (
                row["open_date"].strftime("%Y年%m月%d日")
                if pd.notna(row.get("open_date"))
                else "不明"
            )
            order_num = int(row.get("open_order", 0)) if pd.notna(row.get("open_order")) else ""

            popup_html = _build_popup(row, chain_name, open_date_str)

            if show_number and order_num:
                icon = folium.DivIcon(
                    html=f"""
                    <div style="
                        background-color:{color};
                        color:white;
                        border-radius:50%;
                        width:24px;height:24px;
                        display:flex;align-items:center;justify-content:center;
                        font-size:10px;font-weight:bold;
                        border:2px solid white;
                        box-shadow:0 1px 3px rgba(0,0,0,0.4);
                    ">{order_num}</div>
                    """,
                    icon_size=(24, 24),
                    icon_anchor=(12, 12),
                )
            else:
                icon = folium.Icon(color=_folium_color(color), icon="circle", prefix="fa")

            marker = folium.Marker(
                location=[row["lat"], row["lng"]],
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{chain_name} {row['store_name']}",
                icon=icon,
            )
            marker.add_to(cluster)

        if use_cluster:
            cluster.add_to(layer)
        layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _build_popup(row: pd.Series, chain_name: str, open_date_str: str) -> str:
    store_name = row.get("store_name", "")
    address = row.get("address_raw", "")
    order = row.get("open_order", "")
    building = row.get("building", "")
    floor_info = row.get("floor", "")
    close_date = row.get("close_date")
    source_url = row.get("source_url", "")

    close_html = ""
    if pd.notna(close_date):
        close_html = f'<p style="color:#e53935;font-size:11px;">閉店: {close_date}</p>'

    detail_html = ""
    if building:
        detail_html += f'<span style="color:#666;font-size:11px;">{building}'
        if floor_info:
            detail_html += f" {floor_info}"
        detail_html += "</span><br>"

    link_html = ""
    if source_url:
        link_html = f'<a href="{source_url}" target="_blank" style="font-size:11px;color:#1976d2;">詳細ページ →</a>'

    return f"""
    <div style="font-family:'Helvetica Neue',Arial,sans-serif;min-width:200px;">
        <div style="background:#f5f5f5;padding:6px 10px;margin:-1px -1px 8px;border-radius:3px 3px 0 0;">
            <strong style="font-size:13px;">{store_name}</strong>
            <span style="float:right;background:#666;color:white;padding:1px 6px;border-radius:10px;font-size:11px;">#{order}</span>
        </div>
        <div style="padding:0 4px;">
            <p style="font-size:12px;margin:0 0 4px;color:#333;">
                <strong>{chain_name}</strong>
            </p>
            {detail_html}
            <p style="font-size:12px;color:#555;margin:0 0 4px;">{address}</p>
            <p style="font-size:12px;color:#1976d2;margin:0 0 4px;">開店: {open_date_str}</p>
            {close_html}
            {link_html}
        </div>
    </div>
    """


_COLOR_MAP = {
    "#E85D27": "orange",
    "#4CAF50": "green",
    "#2196F3": "blue",
    "#9C27B0": "purple",
}


def _folium_color(hex_color: str) -> str:
    return _COLOR_MAP.get(hex_color, "gray")
