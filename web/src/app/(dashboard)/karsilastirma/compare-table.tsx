"use client";

import type { SeriesResult } from "@/lib/api";
import { SortableTh } from "@/components/sortable-th";
import { fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";

type SortKey = "label" | "return_pct" | "vs";

export function CompareTable({ results, minePct }: { results: SeriesResult[]; minePct: number }) {
  const accessors: Record<SortKey, (r: SeriesResult) => number | string> = {
    label: (r) => (r.key === "portfolio" ? "Portföyüm" : r.label_tr),
    return_pct: (r) => r.return_pct,
    vs: (r) => r.return_pct - minePct,
  };
  const { sorted, sortKey, direction, toggle } = useSort(results, accessors, "return_pct", "desc");
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[420px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-text-faint">
            <th className="py-2 pr-4 font-medium">Sıra</th>
            <SortableTh label="Varlık" sortKey="label" {...thProps} />
            <SortableTh label="Getiri" sortKey="return_pct" align="right" {...thProps} />
            <SortableTh label="Portföye Fark" sortKey="vs" align="right" last {...thProps} />
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => {
            const vs = r.return_pct - minePct;
            return (
              <tr key={r.key} className="border-b border-border/60 last:border-0">
                <td className="py-2.5 pr-4 text-text-faint">{i + 1}</td>
                <td className="py-2.5 pr-4 font-medium text-text">
                  {r.key === "portfolio" ? "Portföyüm" : r.label_tr}
                </td>
                <td
                  className={`tabular py-2.5 pr-4 text-right ${r.return_pct >= 0 ? "text-pos" : "text-neg"}`}
                >
                  {fmtPct(r.return_pct, 2)}
                </td>
                <td className={`tabular py-2.5 text-right ${vs >= 0 ? "text-pos" : "text-neg"}`}>
                  {fmtPct(vs, 2)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
