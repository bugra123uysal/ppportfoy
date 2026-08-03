"use client";

import type { OptionActivity } from "@/lib/api";
import { SortableTh } from "@/components/sortable-th";
import { useSort } from "@/lib/use-sort";
import { MOOD_LABEL, MOOD_TONE, pcrMood, putCallRatio, totalVolume } from "./mood";

type SortKey = "symbol" | "expiry" | "call" | "put" | "total" | "pcr";

const ACCESSORS: Record<SortKey, (a: OptionActivity) => number | string> = {
  symbol: (a) => a.symbol,
  expiry: (a) => a.expiry,
  call: (a) => a.call_volume,
  put: (a) => a.put_volume,
  total: (a) => totalVolume(a),
  pcr: (a) => putCallRatio(a) ?? 0,
};

export function OptionsTable({ activities }: { activities: OptionActivity[] }) {
  const { sorted, sortKey, direction, toggle } = useSort(activities, ACCESSORS, "total", "desc");
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-text-faint">
            <SortableTh label="Sembol" sortKey="symbol" {...thProps} />
            <SortableTh label="Vade" sortKey="expiry" {...thProps} />
            <SortableTh label="Call" sortKey="call" align="right" {...thProps} />
            <SortableTh label="Put" sortKey="put" align="right" {...thProps} />
            <SortableTh label="Toplam" sortKey="total" align="right" {...thProps} />
            <SortableTh label="PCR" sortKey="pcr" align="right" {...thProps} />
            <th className="py-2 text-right font-medium">Eğilim</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((a) => {
            const ratio = putCallRatio(a);
            const mood = pcrMood(ratio);
            return (
              <tr key={a.symbol} className="border-b border-border/60 last:border-0">
                <td className="py-2.5 pr-4 font-medium text-text">{a.symbol}</td>
                <td className="py-2.5 pr-4 text-text-dim">{a.expiry}</td>
                <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                  {a.call_volume.toLocaleString("tr-TR")}
                </td>
                <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                  {a.put_volume.toLocaleString("tr-TR")}
                </td>
                <td className="tabular py-2.5 pr-4 text-right text-text">
                  {totalVolume(a).toLocaleString("tr-TR")}
                </td>
                <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                  {ratio !== null ? ratio.toFixed(2) : "—"}
                </td>
                <td className={`py-2.5 text-right text-xs font-medium ${MOOD_TONE[mood]}`}>
                  {MOOD_LABEL[mood]}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
