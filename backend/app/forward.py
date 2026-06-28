"""Forward Earnings & Margin view — scraped from Screener.in, no LLM.

Builds the "Forward View" card for a company:
  * Forward P/E proxy (current Stock P/E from Screener)
  * Revenue growth estimate (latest 3y/5y sales CAGR)
  * EBITDA margin trend (last 3 years of OPM% + a simple projection)
  * Net profit margin trajectory
  * A rule-based 2-line "why this margin may expand/compress" summary derived
    from the margin slope, debt and growth — not an AI generation.

Screener.in is used because it is free and exposes 10y financials in clean
tables. Swap to Moneycontrol/Ticker if you prefer; the card shape is the same.
"""

from __future__ import annotations

import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .models import ForwardView

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _to_float(text):
    if text is None:
        return None
    m = re.search(r"-?\d[\d,]*\.?\d*", str(text).replace(",", ""))
    return float(m.group()) if m else None


def _fetch(ticker: str):
    last = ""
    for path in (f"/company/{ticker}/consolidated/", f"/company/{ticker}/"):
        last = "https://www.screener.in" + path
        try:
            r = httpx.get(last, headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
        except httpx.HTTPError:
            continue
        if r.status_code == 200 and "Compounded" in r.text:
            return last, BeautifulSoup(r.text, "html.parser")
    return last, None


def _top_ratio(soup, label):
    ul = soup.find(id="top-ratios")
    if not ul:
        return None
    for li in ul.find_all("li"):
        name = li.find(class_="name")
        if name and label.lower() in name.get_text(strip=True).lower():
            num = li.find(class_="number")
            return _to_float(num.get_text()) if num else None
    return None


def _section_row(soup, sec_id, label):
    sec = soup.find(id=sec_id)
    if not sec:
        return []
    tbl = sec.find("table")
    if not tbl:
        return []
    for tr in tbl.find_all("tr"):
        head = tr.find(["td", "th"])
        if head and label.lower() in head.get_text(strip=True).lower():
            return [_to_float(c.get_text()) for c in tr.find_all("td")[1:]]
    return []


def _ranges(soup, title):
    out = {}
    for tbl in soup.select("table.ranges-table"):
        th = tbl.find("th")
        if th and title.lower() in th.get_text(strip=True).lower():
            for tr in tbl.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    out[tds[0].get_text(strip=True).replace(":", "")] = _to_float(tds[1].get_text())
            break
    return out


def _last_n(series, n):
    vals = [v for v in series if v is not None]
    return vals[-n:] if vals else []


def _trend_label(series) -> str:
    vals = [v for v in series if v is not None]
    if len(vals) < 2:
        return "Stable"
    delta = vals[-1] - vals[0]
    if delta >= 1.5:
        return "Improving"
    if delta <= -1.5:
        return "Declining"
    return "Stable"


def _summary(opm_trend, sales_growth, de, label) -> str:
    bits = []
    if label == "Improving":
        bits.append("Operating margins have trended up over the last few years")
    elif label == "Declining":
        bits.append("Operating margins have compressed recently")
    else:
        bits.append("Operating margins have held broadly stable")
    if sales_growth and sales_growth >= 15:
        bits.append(
            f"and with ~{sales_growth:.0f}% sales growth, operating leverage can widen margins further"
        )
    elif sales_growth is not None:
        bits.append(f"on modest ~{sales_growth:.0f}% sales growth")
    if de is not None and de > 1:
        bits.append("though high leverage (D/E > 1) keeps interest costs a drag on net margins")
    elif de is not None and de < 0.3:
        bits.append("with low debt supporting clean flow-through to net profit")
    return ". ".join([", ".join(bits[:2])] + bits[2:]) + "."


def forward_view(ticker: str) -> Optional[ForwardView]:
    url, soup = _fetch(ticker)
    if soup is None:
        return None

    name_tag = soup.find("h1")
    name = name_tag.get_text(strip=True) if name_tag else ticker

    pe = _top_ratio(soup, "Stock P/E")
    sales = _ranges(soup, "Compounded Sales Growth")
    sales_growth = sales.get("3 Years") or sales.get("5 Years")

    opm = _section_row(soup, "profit-loss", "OPM %")
    opm3 = _last_n(opm, 3)
    # naive projection: continue the last step
    proj = None
    if len(opm3) >= 2:
        proj = round(opm3[-1] + (opm3[-1] - opm3[-2]) * 0.5, 1)

    # net margin = Net Profit / Sales per year
    net = _section_row(soup, "profit-loss", "Net Profit")
    rev = _section_row(soup, "profit-loss", "Sales")
    npm = []
    for n, r in zip(net, rev):
        npm.append(round(n / r * 100, 1) if (n is not None and r) else None)
    npm3 = _last_n(npm, 3)

    borrowings = _last_n(_section_row(soup, "balance-sheet", "Borrowings"), 1)
    reserves = _last_n(_section_row(soup, "balance-sheet", "Reserves"), 1)
    equity = _last_n(_section_row(soup, "balance-sheet", "Equity Capital"), 1)
    de = None
    if borrowings and reserves:
        denom = reserves[0] + (equity[0] if equity else 0)
        de = round(borrowings[0] / denom, 2) if denom else None

    label = _trend_label(opm3)

    def fmt_series(series, suffix="%"):
        return " → ".join(f"{v:g}{suffix}" for v in series if v is not None) or "n/a"

    ebitda_trend = fmt_series(opm3)
    if proj is not None:
        ebitda_trend += f" → {proj:g}% (proj)"

    return ForwardView(
        company=name,
        ticker=ticker.upper(),
        forward_pe=(f"{pe:g}x (TTM proxy)" if pe else None),
        revenue_growth_est_pct=(f"{sales_growth:g}%" if sales_growth is not None else None),
        ebitda_margin_trend=ebitda_trend,
        net_margin_trajectory=fmt_series(npm3),
        margin_summary=_summary(opm3, sales_growth, de, label),
        margin_trend_label=label,
        sources=[{"title": "Screener.in", "url": url}],
    )
