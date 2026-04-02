from __future__ import annotations
"""
ゴンチャ 店舗スクレイパー
fashion-press.net からページネーションで全店舗を収集
公式サイト(store.gongcha.co.jp)はZE Store Search系だが環境によりアクセス不可
"""
import re
import time
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from scrapers.utils import extract_prefecture, normalize_date

FASHION_PRESS_BASE = "https://www.fashion-press.net/maps/bline_6297"
PRTIMES_BASE = "https://prtimes.jp/main/html/searchrlp/company_id/48503"

# PRTimesから取得した既知の開店日
KNOWN_DATES: dict[str, str] = {
    "ゴンチャ 原宿神宮前店": "2025-03-14",
    "ゴンチャ 秋葉原中央通り店": "2025-05-30",
    "ゴンチャ 錦糸町テルミナ店": "2025-11-13",
    "ゴンチャ ルクア大阪": "2024-03-01",
    "ゴンチャ イオンモール名古屋ノリタケガーデン": "2024-07-12",
    "ゴンチャ イオンモール名古屋ノリタケガーデン（則武新町店）": "2024-07-12",
    "ゴンチャ 横須賀中央店": "2024-11-14",
    "ゴンチャ 駒沢大学駅前店": "2024-12-20",
    "ゴンチャ ビバシティ彦根店": "2024-10-10",
}


class GonchaScraper(BaseScraper):
    chain_id = "gongcha"
    chain_name = "ゴンチャ"

    def fetch_store_list(self) -> list[dict]:
        stores = []
        seen = set()
        page = 1

        while True:
            url = FASHION_PRESS_BASE if page == 1 else f"{FASHION_PRESS_BASE}?page={page}"
            try:
                resp = self.get(url)
                soup = BeautifulSoup(resp.text, "lxml")

                # 店舗リスト要素を探す
                items = (
                    soup.select(".map-list-item")
                    or soup.select(".spot-item")
                    or soup.select("[class*='map-item']")
                    or soup.select("[class*='spot']")
                )

                if not items:
                    # ページ内のリンクから店舗名を取得
                    items = soup.select("a[href*='/maps/bline_6297/']")

                found_any = False
                for item in items:
                    name_el = item.select_one("h2,h3,.name,[class*='name'],span") or item
                    pref_el = item.select_one(".pref,[class*='pref'],span.area")

                    name = name_el.get_text(strip=True)
                    pref = pref_el.get_text(strip=True) if pref_el else ""

                    if not name or "ゴンチャ" not in name:
                        # リンクテキストから取得
                        link_text = item.get_text(strip=True)
                        if "ゴンチャ" in link_text:
                            name = link_text
                        else:
                            continue

                    if name in seen:
                        continue
                    seen.add(name)
                    found_any = True

                    if not pref:
                        pref = extract_prefecture(name)

                    # ジオコーディング用: 都道府県 + ビル名
                    building = name.replace("ゴンチャ ", "").replace("店", "").strip()
                    geocode_query = f"{pref} {building}" if pref else building

                    stores.append({
                        "store_id": f"gc_{len(stores):04d}",
                        "store_name": name,
                        "address_raw": geocode_query,
                        "prefecture": pref,
                        "city": "",
                        "open_date": KNOWN_DATES.get(name, ""),
                        "close_date": "",
                        "lat": "",
                        "lng": "",
                        "floor": "",
                        "building": building,
                        "source_url": FASHION_PRESS_BASE,
                    })

                # ページネーション確認
                next_link = soup.select_one("a[rel='next'], .pagination .next, a.next")
                total_text = soup.get_text()
                total_match = re.search(r"全(\d+)件", total_text)
                total = int(total_match.group(1)) if total_match else 999

                print(f"  page {page}: {len(items)} items, total seen: {len(stores)}/{total}")

                if not found_any or len(stores) >= total:
                    break
                page += 1
                time.sleep(1.5)

            except Exception as e:
                print(f"  page {page} エラー: {e}")
                break

        return stores
