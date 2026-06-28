"""Pydantic models and the market-cap bracket definitions for StockScan India."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


# Market-cap brackets in INR Crore. Order matters: evaluated low → high.
# (label, lower_inclusive_cr, upper_exclusive_cr or None for open-ended)
BRACKETS = [
    ("Nano Cap", 0, 500),
    ("Micro Cap", 500, 5_000),
    ("Small Cap", 5_000, 20_000),
    ("Mid Cap", 20_000, 50_000),
    ("Large Cap", 50_000, 1_00_000),
    ("Mega Cap", 1_00_000, None),
]

BRACKET_LABELS = [b[0] for b in BRACKETS]


def bracket_for(mcap_cr: Optional[float]) -> str:
    """Return the market-cap bracket label for a market cap in INR Crore."""
    if mcap_cr is None:
        return "Unknown"
    for label, lo, hi in BRACKETS:
        if mcap_cr >= lo and (hi is None or mcap_cr < hi):
            return label
    return "Unknown"


class Stock(BaseModel):
    name: str
    ticker: str
    exchange: str                 # "NSE", "BSE", or "NSE/BSE"
    market_cap_cr: Optional[float] = None
    sector: Optional[str] = None
    price: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None

    @property
    def bracket(self) -> str:
        return bracket_for(self.market_cap_cr)


class OrderHit(BaseModel):
    """One company that recently won an order (from the AI scanner)."""
    company: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    order_size: Optional[str] = None          # e.g. "₹1,250 Cr"
    order_size_cr: Optional[float] = None      # numeric, for filtering
    client_sector: Optional[str] = None
    revenue_impact: Optional[str] = None
    delivery_timeline: Optional[str] = None
    market_cap_cr: Optional[float] = None
    market_cap_bracket: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None


class ForwardView(BaseModel):
    """Forward earnings / margin card for a single company."""
    company: str
    ticker: Optional[str] = None
    forward_pe: Optional[str] = None
    revenue_growth_est_pct: Optional[str] = None
    ebitda_margin_trend: Optional[str] = None     # e.g. "FY23 18% → FY24 20% → FY25E 22%"
    net_margin_trajectory: Optional[str] = None
    margin_summary: Optional[str] = None          # AI 2-line "why margin may expand"
    margin_trend_label: Optional[str] = None      # Improving / Stable / Declining
    sources: list[dict] = []
