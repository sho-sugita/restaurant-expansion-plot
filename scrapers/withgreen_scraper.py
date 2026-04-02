from __future__ import annotations
"""
withgreen 店舗スクレイパー
公式: https://store.withgreen.club/
Next.js製 SPA - map.json から全店舗データ取得
"""
import json
import re
import asyncio
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from scrapers.utils import extract_prefecture, normalize_date

BASE_URL = "https://store.withgreen.club"


class WithgreenScraper(BaseScraper):
    chain_id = "withgreen"
    chain_name = "withgreen"

    def fetch_store_list(self) -> list[dict]:
        # buildId を取得
        try:
            resp = self.get(BASE_URL + "/")
            soup = BeautifulSoup(resp.text, "lxml")
            build_id = self._get_build_id(soup)
            if build_id:
                # map.json に allShopsData.shops が含まれる
                stores = self._fetch_map_json(build_id)
                if stores:
                    return stores
        except Exception as e:
            print(f"[withgreen] HTTPエラー: {e}")

        # フォールバック: Playwright
        return asyncio.run(self._async_fetch())

    def _get_build_id(self, soup: BeautifulSoup) -> str | None:
        script = soup.find("script", id="__NEXT_DATA__")
        if script:
            try:
                data = json.loads(script.string)
                return data.get("buildId")
            except Exception:
                pass
        for script in soup.find_all("script"):
            if script.string and '"buildId"' in (script.string or ""):
                m = re.search(r'"buildId"\s*:\s*"([^"]+)"', script.string)
                if m:
                    return m.group(1)
        return None

    def _fetch_map_json(self, build_id: str) -> list[dict]:
        url = f"{BASE_URL}/_next/data/{build_id}/map.json"
        resp = self.get(url)
        data = resp.json()

        shops = (
            data.get("pageProps", {})
            .get("allShopsData", {})
            .get("shops", [])
        )
        if shops:
            return self._parse_shops(shops)

        # フォールバック: index.json
        url2 = f"{BASE_URL}/_next/data/{build_id}/index.json"
        resp2 = self.get(url2)
        data2 = resp2.json()
        shops2 = (
            data2.get("pageProps", {})
            .get("allShopsData", {})
            .get("shops", [])
        )
        return self._parse_shops(shops2)

    def _parse_shops(self, shops: list) -> list[dict]:
        stores = []
        for item in shops:
            name = item.get("nameKanji") or item.get("name") or ""
            addr = item.get("address") or ""
            lat = item.get("latitude") or ""
            lng = item.get("longitude") or ""
            open_raw = item.get("openingDate") or ""

            # businessStatus が CLOSED の場合
            close_date = ""
            if item.get("businessStatus") == "CLOSED":
                close_date = "closed"

            stores.append({
                "store_id": str(item.get("id", item.get("storeId", ""))),
                "store_name": str(name).strip(),
                "address_raw": str(addr).strip(),
                "prefecture": extract_prefecture(str(addr)),
                "city": "",
                "open_date": normalize_date(str(open_raw)),
                "close_date": close_date,
                "lat": float(lat) if lat else "",
                "lng": float(lng) if lng else "",
                "floor": "",
                "building": "",
                "source_url": BASE_URL,
            })
        return stores

    async def _async_fetch(self) -> list[dict]:
        from playwright.async_api import async_playwright
        stores = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            api_data = []

            async def handle_response(response):
                url = response.url
                if "map.json" in url or "allShopsData" in url:
                    try:
                        body = await response.json()
                        api_data.append(body)
                    except Exception:
                        pass

            page.on("response", handle_response)
            await page.goto(BASE_URL + "/map", wait_until="networkidle", timeout=30000)

            for data in api_data:
                shops = (
                    data.get("pageProps", {})
                    .get("allShopsData", {})
                    .get("shops", [])
                )
                if shops:
                    stores = self._parse_shops(shops)
                    break

            await browser.close()
        return stores
