"use client";

import type { SectorRotation } from "@/lib/api";
import { SortableTh } from "@/components/sortable-th";
import { fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";
import { QUADRANT_COLOR } from "@/components/rrg-chart";

// Kadran rozeti: renkli nokta + betimleyici etiket (referans: RRG tablo görünümü).
const QUADRANT_BADGE_TR: Record<string, string> = {
  leading: "Lider & Hızlanan",
  improving: "Geç Kalmış, Dönüyor",
  weakening: "Lider ama Solan",
  lagging: "Zayıf",
};

type SortKey = "symbol" | "quadrant" | "perf_1w" | "perf_1m" | "perf_3m";

const ACCESSORS: Record<SortKey, (p: SectorRotation) => number | string> = {
  symbol: (p) => p.symbol,
  quadrant: (p) => QUADRANT_BADGE_TR[p.quadrant],
  perf_1w: (p) => p.perf_1w,
  perf_1m: (p) => p.perf_1m,
  perf_3m: (p) => p.perf_3m,
};

export function PerformanceTable({ points }: { points: SectorRotation[] }) {
  const { sorted, sortKey, direction, toggle } = useSort(points, ACCESSORS, "perf_1m", "desc");
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-text-faint">
            <SortableTh label="Sektör" sortKey="symbol" {...thProps} />
            <SortableTh label="Kadran" sortKey="quadrant" {...thProps} />
            <SortableTh label="1H" sortKey="perf_1w" align="right" {...thProps} />
            <SortableTh label="1A" sortKey="perf_1m" align="right" {...thProps} />
            <SortableTh label="3A" sortKey="perf_3m" align="right" last {...thProps} />
          </tr>
        </thead>
        <tbody>
          {sorted.map((p) => (
            <tr key={p.symbol} className="border-b border-border/60 last:border-0">
              <td className="py-2.5 pr-4 font-medium text-text">
                {p.symbol} <span className="text-text-faint">· {p.label_tr}</span>
              </td>
              <td className="py-2.5 pr-4">
                <QuadrantBadge quadrant={p.quadrant} />
              </td>
              <PerfCell value={p.perf_1w} />
              <PerfCell value={p.perf_1m} />
              <PerfCell value={p.perf_3m} last />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function QuadrantBadge({ quadrant }: { quadrant: SectorRotation["quadrant"] }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-text-dim">
      <span
        className="h-1.5 w-1.5 shrink-0 rounded-full"
        style={{ backgroundColor: QUADRANT_COLOR[quadrant] }}
        aria-hidden
      />
      {QUADRANT_BADGE_TR[quadrant]}
    </span>
  );
}

function PerfCell({ value, last }: { value: number; last?: boolean }) {
  return (
    <td
      className={`tabular py-2.5 text-right ${last ? "" : "pr-4"} ${value >= 0 ? "text-pos" : "text-neg"}`}
    >
      {fmtPct(value, 1)}
    </td>
  );
}
