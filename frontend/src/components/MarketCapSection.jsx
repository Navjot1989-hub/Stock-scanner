import React, { useState } from "react";

const fmtCr = (v) =>
  v == null ? "—" : v >= 1000 ? `₹${(v / 1000).toFixed(1)}k Cr` : `₹${v} Cr`;
const fmt = (v) => (v == null ? "—" : v);

export default function MarketCapSection({ bracket }) {
  const [open, setOpen] = useState(bracket.count > 0 && bracket.count <= 20);
  const [search, setSearch] = useState("");

  const rows = bracket.stocks.filter((s) => {
    const q = search.toLowerCase();
    return (
      !q ||
      s.name.toLowerCase().includes(q) ||
      s.ticker.toLowerCase().includes(q) ||
      (s.sector || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="mb-3 rounded-lg border border-slate-200 bg-white shadow-sm">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="font-semibold text-ink">
          {bracket.label}
          <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
            {bracket.count}
          </span>
        </span>
        <span className="text-slate-400">{open ? "▾" : "▸"}</span>
      </button>

      {open && (
        <div className="border-t border-slate-100 p-3">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search ${bracket.label}…`}
            className="mb-3 w-full rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-accent focus:outline-none"
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase text-slate-500">
                  <th className="px-2 py-1">Company</th>
                  <th className="px-2 py-1">Ticker</th>
                  <th className="px-2 py-1">Exch</th>
                  <th className="px-2 py-1 text-right">Market Cap</th>
                  <th className="px-2 py-1">Sector</th>
                  <th className="px-2 py-1 text-right">Price</th>
                  <th className="px-2 py-1 text-right">52W H/L</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr key={s.ticker} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="px-2 py-1.5 font-medium">{s.name}</td>
                    <td className="px-2 py-1.5 text-slate-600">{s.ticker}</td>
                    <td className="px-2 py-1.5 text-slate-600">{s.exchange}</td>
                    <td className="px-2 py-1.5 text-right">{fmtCr(s.market_cap_cr)}</td>
                    <td className="px-2 py-1.5 text-slate-600">{fmt(s.sector)}</td>
                    <td className="px-2 py-1.5 text-right">{fmt(s.price)}</td>
                    <td className="px-2 py-1.5 text-right text-xs text-slate-500">
                      {fmt(s.week52_high)} / {fmt(s.week52_low)}
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-2 py-3 text-center text-slate-400">
                      No matches
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
