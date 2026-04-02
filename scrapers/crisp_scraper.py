from __future__ import annotations
"""
クリスプサラダワークス店舗スクレイパー
公式: https://crisp.co.jp/location
Next.js SSG - location.json から緯度経度付き全店舗データを取得
"""
import json
import re
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from scrapers.utils import extract_prefecture, normalize_date

BASE_URL = "https://crisp.co.jp"
LOCATION_URL = f"{BASE_URL}/location"


class CrispScraper(BaseScraper):
    chain_id = "crisp"
    chain_name = "クリスプサラダワークス"

    def fetch_store_list(self) -> list[dict]:
        # buildId 取得
        resp = self.get(LOCATION_URL)
        soup = BeautifulSoup(resp.text, "lxml")

        build_id = self._get_build_id(soup)
        if build_id:
            stores = self._fetch_via_next_api(build_id)
            if stores:
                return stores

        # フォールバック: HTMLパース
        return self._parse_html(soup)

    def _get_build_id(self, soup: BeautifulSoup) -> str | None:
        script = soup.find("script", id="__NEXT_DATA__")
        if script:
            try:
                data = json.loads(script.string)
                return data.get("buildId")
            except Exception:
                pass
        return None

    def _fetch_via_next_api(self, build_id: str) -> list[dict]:
        url = f"{BASE_URL}/_next/data/{build_id}/location.json"
        try:
            resp = self.get(url)
            data = resp.json()
            shops = _find_shops(data)
            if shops:
                return self._parse_shops(shops)
        except Exception:
            pass
        return []

    def _parse_shops(self, shops: list) -> list[dict]:
        stores = []
        for i, item in enumerate(shops):
            name = item.get("name") or item.get("storeName") or ""
            addr = item.get("address") or item.get("addr") or ""
            position = item.get("position") or {}
            lat = position.get("lat") or item.get("latitude") or item.get("lat") or ""
            lng = position.get("lng") or item.get("longitude") or item.get("lng") or ""
            open_raw = item.get("openDate") or item.get("open_date") or ""

            stores.append({
                "store_id": str(item.get("id", i)),
                "store_name": f"クリスプサラダワークス {name}".strip(),
                "address_raw": str(addr).strip(),
                "prefecture": extract_prefecture(str(addr)),
                "city": "",
                "open_date": normalize_date(str(open_raw)),
                "close_date": "",
                "lat": float(lat) if lat else "",
                "lng": float(lng) if lng else "",
                "floor": "",
                "building": "",
                "source_url": LOCATION_URL,
            })
        return stores

    def _parse_html(self, soup: BeautifulSoup) -> list[dict]:
        stores = []
        for i, item in enumerate(soup.select(".store-item, .location-item, [class*='store']")):
            name_el = item.select_one("h2,h3,.name,[class*='name']")
            addr_el = item.select_one(".address,[class*='addr']")
            name = name_el.get_text(strip=True) if name_el else ""
            addr = addr_el.get_text(strip=True) if addr_el else ""
            if not name:
                continue
            stores.append({
                "store_id": str(i),
                "store_name": f"クリスプサラダワークス {name}",
                "address_raw": addr,
                "prefecture": extract_prefecture(addr),
                "city": "",
                "open_date": "",
                "close_date": "",
                "lat": "",
                "lng": "",
                "floor": "",
                "building": "",
                "source_url": LOCATION_URL,
            })
        return stores


def _find_shops(obj, depth=0) -> list | None:
    if depth > 8:
        return None
    if isinstance(obj, list) and len(obj) > 3 and isinstance(obj[0], dict):
        keys = set(obj[0].keys())
        if {"name", "address"} & keys or {"latitude", "longitude"} & keys:
            return obj
    if isinstance(obj, dict):
        for v in obj.values():
            result = _find_shops(v, depth + 1)
            if result:
                return result
    return None
