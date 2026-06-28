// API base: in production set VITE_API_BASE to your backend URL (Render/Railway).
// In local dev it's empty and Vite proxies /api to localhost:8000.
const BASE = import.meta.env.VITE_API_BASE || "";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const getUniverse = () => get("/api/universe");
export const getFilters = () => get("/api/filters");

export const runScan = ({ q, marketCaps, sectors, exchanges, minOrderCr }) => {
  const p = new URLSearchParams();
  if (q) p.set("q", q);
  if (marketCaps?.length) p.set("market_caps", marketCaps.join(","));
  if (sectors?.length) p.set("sectors", sectors.join(","));
  if (exchanges?.length) p.set("exchanges", exchanges.join(","));
  if (minOrderCr) p.set("min_order_cr", String(minOrderCr));
  return get(`/api/scan?${p.toString()}`);
};

export const getForward = (ticker) => get(`/api/forward/${encodeURIComponent(ticker)}`);
