"""Stock-universe loading and market-cap categorisation.

Data strategy (in priority order):
  1. If a NSE/BSE or provider API is configured (STOCK_API_URL), fetch from it.
  2. Otherwise load the bundled seed CSV (seed_stocks.csv) so the app runs
     out of the box with a representative universe.

The seed set is intentionally small and illustrative. Swap in a real provider
(NSE bhavcopy, BSE, Screener.in, Ticker.in, RapidAPI Indian Stocks) by setting
STOCK_API_URL and adapting `fetch_from_api`. Market caps are in INR Crore.
"""

from __future__ import annotations

import csv
import os
import time
from typing import Optional

import httpx

from .models import Stock, BRACKET_LABELS, bracket_for

SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "seed_stocks.csv")
STOCK_API_URL = os.environ.get("STOCK_API_URL")          # optional live source
STOCK_API_KEY = os.environ.get("STOCK_API_KEY")
CACHE_TTL = int(os.environ.get("UNIVERSE_TTL_SECONDS", "3600"))

_cache: dict = {"ts": 0.0, "stocks": []}


def _to_float(v) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def load_seed() -> list[Stock]:
    stocks: list[Stock] = []
    with open(SEED_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stocks.append(
                Stock(
                    name=row["name"].strip(),
                    ticker=row["ticker"].strip(),
                    exchange=row["exchange"].strip(),
                    market_cap_cr=_to_float(row.get("market_cap_cr")),
                    sector=(row.get("sector") or "").strip() or None,
                    price=_to_float(row.get("price")),
                    week52_high=_to_float(row.get("week52_high")),
                    week52_low=_to_float(row.get("week52_low")),
                )
            )
    return stocks


def fetch_from_api() -> list[Stock]:
    """Adapt this to your chosen provider's response shape."""
    headers = {}
    if STOCK_API_KEY:
        headers["Authorization"] = f"Bearer {STOCK_API_KEY}"
    resp = httpx.get(STOCK_API_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    out: list[Stock] = []
    for r in rows:
        out.append(
            Stock(
                name=r.get("name") or r.get("companyName"),
                ticker=r.get("ticker") or r.get("symbol"),
                exchange=r.get("exchange", "NSE"),
                market_cap_cr=_to_float(r.get("market_cap_cr") or r.get("marketCap")),
                sector=r.get("sector"),
                price=_to_float(r.get("price") or r.get("lastPrice")),
                week52_high=_to_float(r.get("week52_high") or r.get("yearHigh")),
                week52_low=_to_float(r.get("week52_low") or r.get("yearLow")),
            )
        )
    return out


def get_universe(force: bool = False) -> list[Stock]:
    """Return the full stock universe, cached for CACHE_TTL seconds."""
    now = time.time()
    if not force and _cache["stocks"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["stocks"]
    try:
        stocks = fetch_from_api() if STOCK_API_URL else load_seed()
    except Exception as exc:  # noqa: BLE001 - fall back to seed on any provider error
        print(f"[data] live fetch failed ({exc}); using seed universe")
        stocks = load_seed()
    _cache.update(ts=now, stocks=stocks)
    return stocks


def categorise(stocks: list[Stock]) -> dict[str, list[Stock]]:
    """Group stocks into the six market-cap brackets (sorted by mcap desc)."""
    groups: dict[str, list[Stock]] = {label: [] for label in BRACKET_LABELS}
    groups["Unknown"] = []
    for s in stocks:
        groups[s.bracket].append(s)
    for label in groups:
        groups[label].sort(key=lambda x: x.market_cap_cr or 0, reverse=True)
    return groups


def find_market_cap(name_or_ticker: str) -> Optional[float]:
    """Best-effort lookup of a company's market cap from the universe."""
    q = name_or_ticker.strip().lower()
    for s in get_universe():
        if q == s.ticker.lower() or q in s.name.lower():
            return s.market_cap_cr
    return None


def tag_bracket(mcap_cr: Optional[float]) -> str:
    return bracket_for(mcap_cr)
