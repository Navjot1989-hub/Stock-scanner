"""Order Intelligence Scanner — no LLM.

Turns a natural-language command ("mid-cap companies that won government
contracts this quarter") into a structured list of recent order wins by
aggregating the live feeds in sources.py, filtering them, parsing order sizes,
and tagging each result with its market-cap bracket from the universe.

The "natural language" is handled with lightweight keyword parsing:
  * market-cap words  -> bracket filter   (nano/micro/small/mid/large/mega cap)
  * exchange words    -> NSE / BSE filter
  * the remaining text -> the Google News search query (free text)
plus an order-keyword gate so we only keep genuine order/contract news.
"""

from __future__ import annotations

import re
from typing import Optional

from .models import OrderHit, BRACKET_LABELS
from . import sources
from .data import get_universe, tag_bracket

ORDER_KEYWORDS = [
    "order", "orders", "contract", "contracts", "bagged", "bags", "won", "wins",
    "secured", "awarded", "award", "letter of award", "loa", "work order",
    "purchase order", "deal", "tender", "supply order", "EPC", "project win",
]
_ORDER_RE = re.compile("|".join(rf"\b{re.escape(k)}\b" for k in ORDER_KEYWORDS), re.IGNORECASE)

_CAP_WORDS = {
    "nano": "Nano Cap", "micro": "Micro Cap", "small": "Small Cap",
    "mid": "Mid Cap", "large": "Large Cap", "mega": "Mega Cap",
}


def parse_command(q: str) -> dict:
    """Extract bracket / exchange hints and a cleaned search query from text."""
    ql = (q or "").lower()
    brackets = {label for word, label in _CAP_WORDS.items()
                if re.search(rf"\b{word}[- ]?cap", ql)}
    exchanges = set()
    if "nse" in ql:
        exchanges.add("NSE")
    if "bse" in ql:
        exchanges.add("BSE")
    return {"brackets": brackets, "exchanges": exchanges, "query": q.strip()}


def _build_company_index():
    """Map lowercased name tokens -> Stock for matching news headlines."""
    idx = []
    for s in get_universe():
        idx.append((s.name.lower(), s))
        # also index the first significant word of the company name
    return idx


def _match_company(text: str, index) -> Optional[object]:
    t = (text or "").lower()
    best = None
    best_len = 0
    for name, stock in index:
        # require the core name (drop common suffixes) to appear in the headline
        core = re.sub(r"\b(ltd|limited|industries|india|corp|corporation|company)\b",
                      "", name).strip()
        needle = core if len(core) >= 4 else name
        if needle and needle in t and len(needle) > best_len:
            best, best_len = stock, len(needle)
    return best


def scan(
    query: str = "recent large order wins",
    market_caps: Optional[list[str]] = None,
    sectors: Optional[list[str]] = None,
    exchanges: Optional[list[str]] = None,
    min_order_cr: Optional[float] = None,
    limit: int = 40,
) -> list[OrderHit]:
    parsed = parse_command(query)
    brackets = set(market_caps or []) | parsed["brackets"]
    want_exchanges = set(exchanges or []) | parsed["exchanges"]
    sectors = set(s.lower() for s in (sectors or []))

    # 1. Gather candidate items from all sources.
    search_q = f'{parsed["query"]} order OR contract OR bagged India NSE BSE'
    items: list[dict] = []
    items += sources.google_news(search_q, limit=50)
    items += sources.nse_announcements(limit=60)
    items += sources.bse_announcements(limit=60)
    items += sources.moneycontrol_news(limit=30)
    items += sources.mint_news(limit=30)
    items += sources.dhan_feed(limit=30)

    index = _build_company_index()
    hits: list[OrderHit] = []
    seen = set()

    for it in items:
        blob = f"{it['title']} {it['summary']}"
        if not _ORDER_RE.search(blob):
            continue  # only genuine order/contract news

        stock = _match_company(blob, index)
        order_cr = sources.parse_order_size_cr(blob)

        company = stock.name if stock else it["title"][:80]
        ticker = stock.ticker if stock else None
        exch = stock.exchange if stock else it["source"]
        mcap = stock.market_cap_cr if stock else None
        bracket = tag_bracket(mcap) if mcap is not None else None
        sector = stock.sector if stock else None

        # de-dupe on (company, rounded order size)
        key = (company.lower(), int(order_cr or 0))
        if key in seen:
            continue
        seen.add(key)

        # 2. Apply filters.
        if brackets and bracket not in brackets:
            continue
        if want_exchanges and exch not in want_exchanges and exch not in ("NSE/BSE",):
            continue
        if sectors and (not sector or sector.lower() not in sectors):
            continue
        if min_order_cr is not None and (order_cr is None or order_cr < min_order_cr):
            continue

        hits.append(OrderHit(
            company=company,
            ticker=ticker,
            exchange=exch,
            order_size=(f"₹{order_cr:,.0f} Cr" if order_cr else None),
            order_size_cr=order_cr,
            client_sector=sector,
            revenue_impact=None,
            delivery_timeline=None,
            market_cap_cr=mcap,
            market_cap_bracket=bracket,
            source_url=it["link"],
            source_title=it["source"],
        ))

    # Largest known orders first, then the rest.
    hits.sort(key=lambda h: (h.order_size_cr or 0), reverse=True)
    return hits[:limit]
