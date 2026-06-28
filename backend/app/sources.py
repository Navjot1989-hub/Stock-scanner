"""Live data sources for StockScan India — no LLM, no paid API keys.

Pulls recent corporate news / order-win announcements straight from public
feeds and exchange endpoints:

  * Google News RSS  — surfaces Bloomberg, Mint, Moneycontrol, Business Standard,
                       Economic Times etc. via a single search query (and site: filters)
  * NSE India        — corporate announcements API
  * BSE India        — corporate announcements API
  * Moneycontrol     — business-news RSS
  * Mint (LiveMint)  — markets RSS
  * Screener.in      — per-company fundamentals (used by forward.py)
  * Dhan             — optional; set DHAN_FEED_URL to an accessible feed

Every fetcher is wrapped so a blocked/over-rate-limited source returns an empty
list instead of breaking the whole scan. Exchange sites (NSE especially) are
bot-protected; we send browser-like headers and warm cookies, and degrade
gracefully when they refuse.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TIMEOUT = httpx.Timeout(20.0)
DHAN_FEED_URL = os.environ.get("DHAN_FEED_URL")  # optional

# News sites we want to weight the Google query toward.
PREFERRED_SITES = [
    "bloomberg.com", "livemint.com", "moneycontrol.com",
    "economictimes.indiatimes.com", "business-standard.com",
]


def _parse_feed(text: str):
    """Lazy feedparser import so the rest of the app works without it installed."""
    try:
        import feedparser  # noqa: PLC0415
    except ImportError:
        print("[sources] feedparser not installed — RSS sources disabled")
        return None
    return feedparser.parse(text)


def _item(title, link, source, published=None, summary=""):
    return {
        "title": (title or "").strip(),
        "link": link,
        "source": source,
        "published": published,
        "summary": (summary or "").strip(),
    }


# --------------------------------------------------------------------------- #
# Google News RSS  (covers Bloomberg / Mint / Moneycontrol / ET / BS / Google web)
# --------------------------------------------------------------------------- #
def google_news(query: str, limit: int = 40, prefer_sites: bool = True) -> list[dict]:
    q = query.strip()
    if prefer_sites:
        sites = " OR ".join(f"site:{s}" for s in PREFERRED_SITES)
        q = f"{q} ({sites} OR India)"
    url = (
        "https://news.google.com/rss/search?q="
        + quote_plus(q)
        + "&hl=en-IN&gl=IN&ceid=IN:en"
    )
    out: list[dict] = []
    try:
        r = httpx.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, follow_redirects=True)
        feed = _parse_feed(r.text)
        if feed is None:
            return out
        for e in feed.entries[:limit]:
            src = (e.get("source", {}) or {}).get("title") or "Google News"
            out.append(_item(e.get("title"), e.get("link"), src,
                             e.get("published"), e.get("summary", "")))
    except Exception as exc:  # noqa: BLE001
        print(f"[sources] google_news failed: {exc}")
    return out


def rss(url: str, source: str, limit: int = 30) -> list[dict]:
    out: list[dict] = []
    try:
        r = httpx.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, follow_redirects=True)
        feed = _parse_feed(r.text)
        if feed is None:
            return out
        for e in feed.entries[:limit]:
            out.append(_item(e.get("title"), e.get("link"), source,
                             e.get("published"), e.get("summary", "")))
    except Exception as exc:  # noqa: BLE001
        print(f"[sources] rss {source} failed: {exc}")
    return out


def moneycontrol_news(limit: int = 30) -> list[dict]:
    return rss("https://www.moneycontrol.com/rss/business.xml", "Moneycontrol", limit)


def mint_news(limit: int = 30) -> list[dict]:
    return rss("https://www.livemint.com/rss/markets", "Mint", limit)


def dhan_feed(limit: int = 30) -> list[dict]:
    if not DHAN_FEED_URL:
        return []
    return rss(DHAN_FEED_URL, "Dhan", limit)


# --------------------------------------------------------------------------- #
# NSE / BSE corporate announcements
# --------------------------------------------------------------------------- #
def _nse_client() -> httpx.Client:
    client = httpx.Client(
        headers={
            "User-Agent": UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
        },
        timeout=TIMEOUT,
        follow_redirects=True,
    )
    try:  # warm cookies — NSE rejects API calls without a prior homepage visit
        client.get("https://www.nseindia.com/")
    except Exception:  # noqa: BLE001
        pass
    return client


def nse_announcements(limit: int = 50) -> list[dict]:
    out: list[dict] = []
    try:
        with _nse_client() as client:
            r = client.get(
                "https://www.nseindia.com/api/corporate-announcements?index=equities"
            )
            data = r.json()
            rows = data if isinstance(data, list) else data.get("data", [])
            for row in rows[:limit]:
                sym = row.get("symbol", "")
                subject = row.get("subject") or row.get("desc") or ""
                attach = row.get("attchmntFile") or row.get("attchmntText") or ""
                out.append(_item(
                    f"{sym}: {subject}",
                    attach or "https://www.nseindia.com",
                    "NSE",
                    row.get("an_dt") or row.get("dt"),
                    subject,
                ))
    except Exception as exc:  # noqa: BLE001
        print(f"[sources] nse_announcements failed: {exc}")
    return out


def bse_announcements(limit: int = 50) -> list[dict]:
    out: list[dict] = []
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    url = (
        "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
        f"?pageno=1&strCat=-1&strPrevDate={today}&strScrip=&strSearch=P"
        f"&strToDate={today}&strType=C&subcategory=-1"
    )
    try:
        r = httpx.get(
            url,
            headers={
                "User-Agent": UA,
                "Referer": "https://www.bseindia.com/corporates/ann.html",
                "Accept": "application/json, text/plain, */*",
            },
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        rows = (r.json() or {}).get("Table", [])
        for row in rows[:limit]:
            name = row.get("SLONGNAME") or row.get("Scrip_Cd") or ""
            head = row.get("NEWSSUB") or row.get("HEADLINE") or row.get("MORE") or ""
            attach = row.get("ATTACHMENTNAME") or ""
            link = (
                f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{attach}"
                if attach else "https://www.bseindia.com/corporates/ann.html"
            )
            out.append(_item(f"{name}: {head}", link, "BSE",
                             row.get("News_submission_dt") or row.get("DT_TM"), head))
    except Exception as exc:  # noqa: BLE001
        print(f"[sources] bse_announcements failed: {exc}")
    return out


# --------------------------------------------------------------------------- #
# Order-size parsing
# --------------------------------------------------------------------------- #
_AMT = re.compile(
    r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*"
    r"(crore|cr\b|lakh|billion|bn\b|million|mn\b|trillion)?",
    re.IGNORECASE,
)
_MULT_TO_CR = {
    "crore": 1.0, "cr": 1.0, "": 1.0,
    "lakh": 0.01, "million": 0.1, "mn": 0.1,
    "billion": 100.0, "bn": 100.0, "trillion": 100000.0,
}


def parse_order_size_cr(text: str) -> Optional[float]:
    """Best-effort: return the largest INR amount found, in crore."""
    best = None
    for m in _AMT.finditer(text or ""):
        try:
            val = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        unit = (m.group(2) or "").lower().strip()
        val_cr = val * _MULT_TO_CR.get(unit, 1.0)
        if best is None or val_cr > best:
            best = val_cr
    return round(best, 2) if best is not None else None
