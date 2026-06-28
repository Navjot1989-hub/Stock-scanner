import React from "react";

const trendColor = {
  Improving: "bg-emerald-100 text-emerald-700",
  Stable: "bg-slate-100 text-slate-600",
  Declining: "bg-rose-100 text-rose-700",
};

export default function ForwardCard({ data, onClose, loading }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-semibold text-ink">Forward View</h3>
        <button onClick={onClose} className="text-sm text-slate-400 hover:text-slate-600">
          ✕
        </button>
      </div>

      {loading && <div className="py-6 text-center text-slate-400">Loading fundamentals…</div>}

      {!loading && data?.error && <div className="py-4 text-sm text-rose-600">{data.error}</div>}

      {!loading && data && !data.error && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <span className="font-medium">{data.company}</span>
            {data.margin_trend_label && (
              <span className={`rounded-full px-2 py-0.5 text-xs ${trendColor[data.margin_trend_label]}`}>
                {data.margin_trend_label} margins
              </span>
            )}
          </div>

          <dl className="space-y-2 text-sm">
            <Row k="Forward P/E" v={data.forward_pe} />
            <Row k="Revenue growth est." v={data.revenue_growth_est_pct} />
            <Row k="EBITDA margin trend" v={data.ebitda_margin_trend} />
            <Row k="Net margin trajectory" v={data.net_margin_trajectory} />
          </dl>

          {data.margin_summary && (
            <div className="mt-3 rounded bg-slate-50 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">Why margins may move: </span>
              {data.margin_summary}
            </div>
          )}

          {data.sources?.length > 0 && (
            <div className="mt-2 text-xs text-slate-400">
              Source:{" "}
              {data.sources.map((s, i) => (
                <a key={i} href={s.url} target="_blank" rel="noreferrer" className="text-accent hover:underline">
                  {s.title}
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{k}</dt>
      <dd className="text-right font-medium">{v || "—"}</dd>
    </div>
  );
}
