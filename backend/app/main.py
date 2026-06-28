"""StockScan India — FastAPI backend.

Endpoints:
  GET /api/health
  GET /api/universe            -> stocks grouped into 6 market-cap brackets
  GET /api/filters             -> available sectors / brackets / exchanges
  GET /api/scan                -> AI-free order-intelligence scan (live feeds)
  GET /api/forward/{ticker}    -> forward earnings & margin card (Screener)

No Anthropic / paid API keys. Data comes from NSE, BSE, Moneycontrol, Mint,
Bloomberg/ET/BS (via Google News), Screener and (optionally) Dhan.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import BRACKET_LABELS
from .data import get_universe, categorise
from .scanner import scan
from .forward import forward_view

app = FastAPI(title="StockScan India", version="1.0.0")

origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/universe")
def universe(refresh: bool = False):
    stocks = get_universe(force=refresh)
    groups = categorise(stocks)
    return {
        "brackets": [
            {
                "label": label,
                "count": len(groups.get(label, [])),
                "stocks": [s.model_dump() | {"bracket": s.bracket} for s in groups.get(label, [])],
            }
            for label in BRACKET_LABELS
        ],
        "total": len(stocks),
    }


@app.get("/api/filters")
def filters():
    stocks = get_universe()
    sectors = sorted({s.sector for s in stocks if s.sector})
    return {
        "brackets": BRACKET_LABELS,
        "exchanges": ["NSE", "BSE", "NSE/BSE"],
        "sectors": sectors,
        "order_sizes": [100, 500, 1000],
    }


@app.get("/api/scan")
def scan_endpoint(
    q: str = Query("recent large order wins", description="natural-language command"),
    market_caps: Optional[str] = Query(None, description="comma-separated bracket labels"),
    sectors: Optional[str] = Query(None, description="comma-separated sectors"),
    exchanges: Optional[str] = Query(None, description="comma-separated NSE/BSE"),
    min_order_cr: Optional[float] = Query(None, description="minimum order size in INR cr"),
    limit: int = 40,
):
    def split(v):
        return [x.strip() for x in v.split(",")] if v else None

    hits = scan(
        query=q,
        market_caps=split(market_caps),
        sectors=split(sectors),
        exchanges=split(exchanges),
        min_order_cr=min_order_cr,
        limit=limit,
    )
    return {"query": q, "count": len(hits), "results": [h.model_dump() for h in hits]}


@app.get("/api/forward/{ticker}")
def forward_endpoint(ticker: str):
    view = forward_view(ticker)
    if view is None:
        return {"error": f"Could not fetch fundamentals for '{ticker}'. Check the Screener ticker."}
    return view.model_dump()
