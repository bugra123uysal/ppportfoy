import type { MacroRow } from "@/lib/api";
import { fmtPct } from "@/lib/format";

export function MacroStrip({ rows }: { rows: MacroRow[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-text-faint">Piyasa verisi alınamadı.</p>;
  }

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
      {rows.map((row) => (
        <div
          key={row.symbol}
          className="flex flex-col gap-1 rounded-lg border border-border bg-surface px-4 py-3"
        >
          <p className="text-[11px] text-text-faint">{row.label}</p>
          <p className="tabular text-sm font-medium text-text">
            {row.price.toLocaleString("tr-TR", { maximumFractionDigits: 2 })}
          </p>
          <p className={`tabular text-xs ${row.change_pct >= 0 ? "text-pos" : "text-neg"}`}>
            {fmtPct(row.change_pct)}
          </p>
        </div>
      ))}
    </div>
  );
}
