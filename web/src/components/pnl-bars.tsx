import type { PositionMetrics } from "@/lib/api";
import { fmtPct } from "@/lib/format";

export function PnlBars({ metrics }: { metrics: PositionMetrics[] }) {
  if (metrics.length === 0) {
    return <p className="text-sm text-text-faint">Pozisyon yok.</p>;
  }
  const sorted = [...metrics].sort((a, b) => b.pnl_pct - a.pnl_pct);
  const maxAbs = Math.max(...sorted.map((m) => Math.abs(m.pnl_pct)), 1);

  return (
    <div className="flex flex-col gap-2.5">
      {sorted.map((m) => {
        const pct = (Math.abs(m.pnl_pct) / maxAbs) * 100;
        const isPos = m.pnl_pct >= 0;
        return (
          <div
            key={m.symbol}
            className="grid grid-cols-[72px_1fr_1px_1fr_64px] items-center gap-2"
          >
            <span className="truncate text-xs text-text-dim">{m.symbol}</span>
            <div className="flex h-6 justify-end">
              {!isPos && (
                <div
                  className="h-5 rounded-l-[4px] bg-neg"
                  style={{ width: `${pct}%` }}
                />
              )}
            </div>
            <div className="h-6 w-px bg-border-strong" />
            <div className="flex h-6 justify-start">
              {isPos && (
                <div
                  className="h-5 rounded-r-[4px] bg-pos"
                  style={{ width: `${pct}%` }}
                />
              )}
            </div>
            <span className={`tabular text-right text-xs font-medium ${isPos ? "text-pos" : "text-neg"}`}>
              {fmtPct(m.pnl_pct)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
