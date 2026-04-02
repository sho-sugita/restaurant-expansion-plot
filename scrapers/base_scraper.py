import time
import random
from abc import ABC, abstractmethod
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class BaseScraper(ABC):
    chain_id: str
    chain_name: str

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.scraped_at = datetime.utcnow().isoformat()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get(self, url: str, **kwargs) -> requests.Response:
        time.sleep(random.uniform(0.5, 1.5))
        resp = self.session.get(url, timeout=15, **kwargs)
        resp.raise_for_status()
        return resp

    @abstractmethod
    def fetch_store_list(self) -> list[dict]:
        """
        Returns list of dicts with keys:
          store_id, store_name, address_raw, prefecture, city,
          open_date, close_date, floor, building, source_url
        """
        ...

    def to_rows(self) -> list[dict]:
        stores = self.fetch_store_list()
        rows = []
        for s in stores:
            rows.append({
                "chain_id": self.chain_id,
                "chain_name": self.chain_name,
                "store_id": s.get("store_id", ""),
                "store_name": s.get("store_name", ""),
                "address_raw": s.get("address_raw", ""),
                "prefecture": s.get("prefecture", ""),
                "city": s.get("city", ""),
                "open_date": s.get("open_date", ""),
                "close_date": s.get("close_date", ""),
                "lat": s.get("lat", ""),
                "lng": s.get("lng", ""),
                "floor": s.get("floor", ""),
                "building": s.get("building", ""),
                "source_url": s.get("source_url", ""),
                "scraped_at": self.scraped_at,
            })
        return rows
