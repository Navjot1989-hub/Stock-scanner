# StockScan India 🇮🇳

A web app that:

1. **Categorises the BSE/NSE universe by market cap** into six brackets (Nano →
   Mega), each a collapsible, searchable table (Company, Ticker, Exchange,
   Market Cap, Sector, Price, 52W High/Low).
2. **Order Intelligence Scanner** — a natural-language command bar that scans
   recent **order / contract wins** by aggregating live feeds (no AI keys), and
   returns Company · Order Size · Client/Sector · Cap Bracket · Source.
3. **Forward View** — for any matched company, a card with forward P/E, revenue
   growth estimate, EBITDA-margin trend (3y + projection), net-margin
   trajectory, and a rule-based "why margins may move" summary.
4. **Filters** — market-cap bracket, sector, exchange, and minimum order size.

> **Research and information only — not investment advice.** Order sizes and
> company matches are parsed heuristically from public headlines; verify on
> NSE/BSE filings before acting.

## Data sources (no LLM, no paid API)

| Feature | Sources |
|---|---|
| Stock universe & market caps | bundled seed CSV (`backend/seed_stocks.csv`); swap in NSE/BSE/Screener/Ticker/RapidAPI via `STOCK_API_URL` |
| Order Intelligence | **NSE** & **BSE** corporate-announcement APIs, **Moneycontrol** & **Mint** RSS, **Bloomberg / ET / Business Standard via Google News**, **Google web** (News RSS), optional **Dhan** feed |
| Forward View | **Screener.in** company fundamentals |

Every source is wrapped to fail soft — if one is rate-limited or blocked, the
scan still returns whatever the others found. NSE in particular is bot-protected;
the backend warms cookies and sends browser headers, and degrades gracefully.

## Tech stack

- **Frontend:** React + Vite + Tailwind CSS
- **Backend:** Python + FastAPI
- **Scheduler:** GitHub Actions cron (alternate days, 11:00 IST) → email digest
- **Hosting:** Vercel (frontend) + Render/Railway (backend)

## Run locally

**Backend** (port 8000):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend** (port 5173, proxies `/api` → `:8000`):
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

## Configure

Copy `backend/.env.example` → `backend/.env` and set what you need. All values
are optional — the app runs out of the box on the seed universe.

- `STOCK_API_URL` / `STOCK_API_KEY` — live universe provider (else seed CSV)
- `DHAN_FEED_URL` — optional Dhan RSS/Atom feed for the scanner
- `CORS_ORIGINS` — restrict to your frontend URL in production
- `SMTP_USER` / `SMTP_PASS` / `EMAIL_TO` — Gmail digest (see below)

## Scheduled scan + email (alternate days, 11 AM IST)

`.github/workflows/autoscan.yml` runs `backend/autoscan.py` on
`cron: "30 5 */2 * *"` (05:30 UTC = 11:00 IST, every other day) on GitHub's
servers — **so it fires even when your machine is off**. It emails a ranked
digest of order wins.

To enable the email, add repository **secrets** (Settings → Secrets and
variables → Actions):

| Secret | Value |
|---|---|
| `SMTP_USER` | your Gmail address |
| `SMTP_PASS` | a Gmail **App Password** — create at <https://myaccount.google.com/apppasswords> with 2-Step Verification on |
| `EMAIL_TO` | `singh.canavjot@gmail.com` |

Optional repository **variables**: `SCAN_QUERY` (default command),
`DHAN_FEED_URL`. Without the secrets, the workflow still runs and prints the
digest to the Actions log. Test it any time via **Actions → StockScan Autoscan
→ Run workflow**.

## Deploy

**Backend → Render** (blueprint included):
1. Push this repo to GitHub.
2. Render → New → **Blueprint** → pick the repo (`render.yaml` is at the root).
3. After it deploys, note the URL, e.g. `https://stockscan-india-api.onrender.com`.

**Frontend → Vercel:**
1. Vercel → New Project → import the repo, set **Root Directory** to `frontend`.
2. Either set env var `VITE_API_BASE` to your Render URL, **or** edit
   `frontend/vercel.json` and replace `YOUR-BACKEND.onrender.com` with your
   Render host (the rewrite proxies `/api/*` to the backend).
3. Set the backend's `CORS_ORIGINS` to your Vercel URL.

## API

| Endpoint | Description |
|---|---|
| `GET /api/universe` | Stocks grouped into the six market-cap brackets |
| `GET /api/filters` | Available sectors / brackets / exchanges |
| `GET /api/scan?q=…&market_caps=…&sectors=…&exchanges=…&min_order_cr=…` | Order-intelligence scan |
| `GET /api/forward/{ticker}` | Forward earnings & margin card |
