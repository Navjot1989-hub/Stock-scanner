import React from "react";

const bracketColor = {
  "Nano Cap": "bg-purple-100 text-purple-700",
  "Micro Cap": "bg-indigo-100 text-indigo-700",
  "Small Cap": "bg-sky-100 text-sky-700",
  "Mid Cap": "bg-teal-100 text-teal-700",
  "Large Cap": "bg-amber-100 text-amber-700",
  "Mega Cap": "bg-rose-100 text-rose-700",
};

export default function OrderResults({ results, loading, onForward }) {
  if (loading) return <div className="py-8 text-center text-slate-400">Scanning live feeds…</div>;
  if (!results) return null;
  if (results.length === 0)
    return (
      <div className="py-8 text-center text-slate-400">
        No order wins matched. Try a broader command or fewer filters.
      </div>
    );

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-ink text-left text-xs uppercase text-white">
            <th className="px-3 py-2">Company</th>
            <th className="px-3 py-2">Order Size</th>
            <th className="px-3 py-2">Client / Sector</th>
            <th className="px-3 py-2">Cap Bracket</th>
            <th className="px-3 py-2">Source</th>
            <th className="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-2">
                <div className="font-medium">{r.company}</div>
                {r.ticker && <div className="text-xs text-slate-500">{r.ticker} · {r.exchange}</div>}
              </td>
              <td className="px-3 py-2 font-semibold text-ink">{r.order_size || "—"}</td>
              <td className="px-3 py-2 text-slate-600">{r.client_sector || "—"}</td>
              <td className="px-3 py-2">
                {r.market_cap_bracket ? (
                  <span className={`rounded-full px-2 py-0.5 text-xs ${bracketColor[r.market_cap_bracket] || "bg-slate-100"}`}>
                    {r.market_cap_bracket}
                  </span>
                ) : (
                  <span className="text-xs text-slate-400">unmatched</span>
                )}
              </td>
              <td className="px-3 py-2">
                <a href={r.source_url} target="_blank" rel="noreferrer" className="text-accent hover:underline">
                  {r.source_title}
                </a>
              </td>
              <td className="px-3 py-2 text-right">
                {r.ticker && (
                  <button
                    onClick={() => onForward(r.ticker)}
                    className="rounded border border-accent px-2 py-1 text-xs text-accent hover:bg-accent hover:text-white"
                  >
                    Forward View
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
