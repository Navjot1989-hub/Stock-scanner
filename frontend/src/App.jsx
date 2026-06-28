import React, { useEffect, useState } from "react";
import { getUniverse, getFilters, runScan, getForward } from "./api";
import MarketCapSection from "./components/MarketCapSection";
import Filters from "./components/Filters";
import OrderResults from "./components/OrderResults";
import ForwardCard from "./components/ForwardCard";

const EXAMPLES = [
  "Companies that recently received large orders",
  "Mid-cap companies that got government contracts this quarter",
  "Defence small-caps with new order wins on NSE",
];

export default function App() {
  const [tab, setTab] = useState("scanner");
  const [universe, setUniverse] = useState(null);
  const [filters, setFilters] = useState(null);

  const [command, setCommand] = useState(EXAMPLES[0]);
  const [filterState, setFilterState] = useState({
    marketCaps: [],
    sectors: [],
    exchanges: [],
    minOrderCr: null,
  });
  const [results, setResults] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);

  const [forward, setForward] = useState(null);
  const [forwardLoading, setForwardLoading] = useState(false);

  useEffect(() => {
    getFilters().then(setFilters).catch(() => {});
    getUniverse().then(setUniverse).catch((e) => setError(String(e)));
  }, []);

  const scan = async () => {
    setScanning(true);
    setError(null);
    try {
      const data = await runScan({ q: command, ...filterState });
      setResults(data.results);
    } catch (e) {
      setError(String(e));
      setResults([]);
    } finally {
      setScanning(false);
    }
  };

  const loadForward = async (ticker) => {
    setForward({});
    setForwardLoading(true);
    try {
      setForward(await getForward(ticker));
    } catch (e) {
      setForward({ error: String(e) });
    } finally {
      setForwardLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <header className="mb-5">
        <h1 className="text-2xl font-bold text-ink">
          StockScan India <span className="text-accent">🇮🇳</span>
        </h1>
        <p className="text-sm text-slate-500">
          NSE/BSE universe by market-cap, live order-intelligence, and forward margin views —
          aggregated from NSE, BSE, Moneycontrol, Mint, Bloomberg, Screener &amp; Google. No AI keys.
        </p>
      </header>

      {/* Command bar */}
      <div className="mb-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex gap-2">
          <input
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && scan()}
            placeholder="Ask: companies that recently received large orders…"
            className="flex-1 rounded border border-slate-300 px-3 py-2 text-sm focus:border-accent focus:outline-none"
          />
          <button
            onClick={scan}
            className="rounded bg-ink px-5 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            Scan
          </button>
        </div>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setCommand(ex)}
              className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-600 hover:bg-slate-200"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-4 flex gap-2">
        {["scanner", "universe"].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded px-4 py-1.5 text-sm font-medium ${
              tab === t ? "bg-accent text-white" : "bg-white text-slate-600 border border-slate-200"
            }`}
          >
            {t === "scanner" ? "Order Scanner" : "Stock Universe"}
          </button>
        ))}
      </div>

      {error && <div className="mb-3 rounded bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {tab === "scanner" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Filters filters={filters} value={filterState} onChange={setFilterState} />
            <OrderResults results={results} loading={scanning} onForward={loadForward} />
          </div>
          <div>
            {forward !== null && (
              <ForwardCard data={forward} loading={forwardLoading} onClose={() => setForward(null)} />
            )}
            {forward === null && (
              <div className="rounded-lg border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-400">
                Click <span className="font-medium text-slate-600">Forward View</span> on any result to
                see forward P/E, revenue growth, and EBITDA/net-margin trajectory.
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "universe" && (
        <div>
          {!universe && <div className="py-8 text-center text-slate-400">Loading universe…</div>}
          {universe && (
            <>
              <div className="mb-3 text-sm text-slate-500">{universe.total} listed companies</div>
              {universe.brackets.map((b) => (
                <MarketCapSection key={b.label} bracket={b} />
              ))}
            </>
          )}
        </div>
      )}

      <footer className="mt-8 border-t border-slate-200 pt-4 text-xs text-slate-400">
        Research and information only — not investment advice. Verify filings on NSE/BSE before acting.
        Order sizes and market-cap matches are parsed heuristically from public headlines.
      </footer>
    </div>
  );
}
