from __future__ import annotations
import json
import time
import os
from pathlib import Path

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

CACHE_PATH = Path(__file__).parent.parent / "data" / "geocode_cache.json"
NOMINATIM_USER_AGENT = "restaurant-chain-plotter/1.0"


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode_address(address: str, retries: int = 3) -> tuple[float, float] | tuple[None, None]:
    cache = _load_cache()

    if address in cache:
        cached = cache[address]
        if cached is None:
            return None, None
        return cached["lat"], cached["lng"]

    # Nominatim
    geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT)
    for attempt in range(retries):
        try:
            time.sleep(1.1)
            location = geolocator.geocode(address, language="ja", timeout=10)
            if location:
                cache[address] = {"lat": location.latitude, "lng": location.longitude}
                _save_cache(cache)
                return location.latitude, location.longitude
        except (GeocoderTimedOut, GeocoderServiceError):
            if attempt < retries - 1:
                time.sleep(3)

    # Google Maps APIフォールバック
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if api_key:
        try:
            import requests
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": api_key, "language": "ja"},
                timeout=10,
            )
            data = resp.json()
            if data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                cache[address] = {"lat": loc["lat"], "lng": loc["lng"]}
                _save_cache(cache)
                return loc["lat"], loc["lng"]
        except Exception:
            pass

    cache[address] = None
    _save_cache(cache)
    return None, None


def geocode_dataframe(df):
    import pandas as pd
    from tqdm import tqdm

    lats, lngs = [], []
    for address in tqdm(df["address_raw"], desc="Geocoding"):
        lat, lng = geocode_address(str(address))
        lats.append(lat)
        lngs.append(lng)

    df = df.copy()
    df["lat"] = lats
    df["lng"] = lngs
    return df
