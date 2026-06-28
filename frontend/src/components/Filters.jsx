import React from "react";

function Chip({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-xs ${
        active
          ? "border-accent bg-accent text-white"
          : "border-slate-300 bg-white text-slate-600 hover:border-accent"
      }`}
    >
      {children}
    </button>
  );
}

export default function Filters({ filters, value, onChange }) {
  if (!filters) return null;
  const toggle = (key, item) => {
    const set = new Set(value[key]);
    set.has(item) ? set.delete(item) : set.add(item);
    onChange({ ...value, [key]: [...set] });
  };

  return (
    <div className="mb-4 space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Market Cap</div>
        <div className="flex flex-wrap gap-2">
          {filters.brackets.map((b) => (
            <Chip key={b} active={value.marketCaps.includes(b)} onClick={() => toggle("marketCaps", b)}>
              {b}
            </Chip>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-6">
        <div>
          <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Exchange</div>
          <div className="flex flex-wrap gap-2">
            {filters.exchanges.map((e) => (
              <Chip key={e} active={value.exchanges.includes(e)} onClick={() => toggle("exchanges", e)}>
                {e}
              </Chip>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Min Order Size</div>
          <select
            value={value.minOrderCr || ""}
            onChange={(e) => onChange({ ...value, minOrderCr: e.target.value ? Number(e.target.value) : null })}
            className="rounded border border-slate-300 px-2 py-1 text-sm"
          >
            <option value="">Any</option>
            {filters.order_sizes.map((o) => (
              <option key={o} value={o}>{`> ₹${o} Cr`}</option>
            ))}
          </select>
        </div>

        <div className="min-w-[180px] flex-1">
          <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Sector</div>
          <select
            value={value.sectors[0] || ""}
            onChange={(e) => onChange({ ...value, sectors: e.target.value ? [e.target.value] : [] })}
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
          >
            <option value="">All sectors</option>
            {filters.sectors.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
