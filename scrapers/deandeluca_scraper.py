from __future__ import annotations
"""
ディーン&デルーカ 店舗スクレイパー
recovery-ub.jp API (ZE Store Search) 経由で全店舗取得
API KEY: 87deeade34654f9395340e5b5c30d714
"""
import time
from scrapers.base_scraper import BaseScraper
from scrapers.utils import extract_prefecture, normalize_date

SEARCH_API = "https://recovery-ub.jp/search"
AREA_API = "https://recovery-ub.jp/areaList"
API_KEY = "87deeade34654f9395340e5b5c30d714"

# 網羅的に取得するための主要都市の座標
SEARCH_CENTERS = [
    ("東京", 35.6999984, 139.8240293),
    ("大阪", 34.6937, 135.5023),
    ("名古屋", 35.1709, 136.8815),
    ("福岡", 33.5904, 130.4017),
    ("札幌", 43.0642, 141.3469),
    ("仙台", 38.2682, 140.8694),
    ("広島", 34.3853, 132.4553),
]


class DeanDelucaScraper(BaseScraper):
    chain_id = "deandeluca"
    chain_name = "ディーン&デルーカ"

    def fetch_store_list(self) -> list[dict]:
        all_stores = {}

        for city_name, lat, lng in SEARCH_CENTERS:
            page = 1
            while True:
                try:
                    resp = self.session.get(
                        SEARCH_API,
                        params={
                            "key": API_KEY,
                            "lat": lat, "lng": lng,
                            "language": "ja",
                            "page": page,
                            "pageSize": 100,
                        },
                        timeout=15,
                    )
                    data = resp.json()
                    response = data.get("response", {})
                    locations = response.get("locations", [])

                    for loc in locations:
                        ident = loc["identifier"]
                        if ident not in all_stores:
                            all_stores[ident] = loc

                    if not response.get("hasNextPage"):
                        break
                    page += 1
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[deandeluca] {city_name} page{page} エラー: {e}")
                    break

        return self._parse_locations(list(all_stores.values()))

    def _parse_locations(self, locations: list) -> list[dict]:
        stores = []
        for loc in locations:
            name = loc.get("name", "")
            pref = loc.get("addressProvince", "")
            city = loc.get("addressLocality", "")
            street = loc.get("streetAddress", "")
            extra = loc.get("addressExtra", "")

            # 住所組み立て
            addr_parts = [p for p in [pref, city, street, extra] if p]
            address = "".join(addr_parts)

            # 閉店判定
            close_date = "" if loc.get("isOpening", True) else "closed"

            stores.append({
                "store_id": str(loc.get("identifier", "")),
                "store_name": name,
                "address_raw": address,
                "prefecture": pref or extract_prefecture(address),
                "city": city,
                "open_date": "",  # APIに開店日なし → ニュースページで補完
                "close_date": close_date,
                "lat": "",  # APIに緯度経度なし → ジオコーディングで取得
                "lng": "",
                "floor": extra,
                "building": extra,
                "source_url": "https://www.deandeluca.co.jp/shop/pages/stores.aspx",
            })
        return stores
