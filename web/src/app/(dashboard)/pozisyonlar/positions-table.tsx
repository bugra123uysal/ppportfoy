"use client";

import type { PositionMetrics } from "@/lib/api";
import { SortableTh } from "@/components/sortable-th";
import { fmtMoney, fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";
import { DeletePositionButton } from "./delete-position-button";

type SortKey =
  | "symbol" | "quantity" | "avg_cost" | "price" | "change_pct"
  | "value" | "pnl" | "pnl_pct" | "weight";

const ACCESSORS: Record<SortKey, (m: PositionMetrics) => number | string> = {
  symbol: (m) => m.symbol,
  quantity: (m) => m.quantity,
  avg_cost: (m) => m.avg_cost,
  price: (m) => m.price,
  change_pct: (m) => m.change_pct,
  value: (m) => m.value,
  pnl: (m) => m.pnl,
  pnl_pct: (m) => m.pnl_pct,
  weight: (m) => m.weight,
};

export function PositionsTable({ metrics }: { metrics: PositionMetrics[] }) {
  const { sorted, sortKey, direction, toggle } = useSort(metrics, ACCESSORS, "value", "desc");
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-text-faint">
            <SortableTh label="Sembol" sortKey="symbol" {...thProps} />
            <SortableTh label="Adet" sortKey="quantity" align="right" {...thProps} />
            <SortableTh label="Ort. Maliyet" sortKey="avg_cost" align="right" {...thProps} />
            <SortableTh label="Fiyat" sortKey="price" align="right" {...thProps} />
            <SortableTh label="Günlük %" sortKey="change_pct" align="right" {...thProps} />
            <SortableTh label="Değer" sortKey="value" align="right" {...thProps} />
            <SortableTh label="K/Z" sortKey="pnl" align="right" {...thProps} />
            <SortableTh label="K/Z %" sortKey="pnl_pct" align="right" {...thProps} />
            <SortableTh label="Ağırlık" sortKey="weight" align="right" {...thProps} />
            <th className="py-2 text-right font-medium"></th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((m) => (
            <tr key={m.symbol} className="border-b border-border/60 last:border-0">
              <td className="py-2.5 pr-4 font-medium text-text">{m.symbol}</td>
              <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                {m.quantity.toLocaleString("tr-TR", { maximumFractionDigits: 2 })}
              </td>
              <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                {m.avg_cost.toLocaleString("tr-TR", { maximumFractionDigits: 2 })}
              </td>
              <td className="tabular py-2.5 pr-4 text-right text-text">
                {m.price.toLocaleString("tr-TR", { maximumFractionDigits: 2 })}
              </td>
              <td
                className={`tabular py-2.5 pr-4 text-right ${m.change_pct >= 0 ? "text-pos" : "text-neg"}`}
              >
                {fmtPct(m.change_pct)}
              </td>
              <td className="tabular py-2.5 pr-4 text-right text-text">
                {fmtMoney(m.value, m.currency)}
              </td>
              <td className={`tabular py-2.5 pr-4 text-right ${m.pnl >= 0 ? "text-pos" : "text-neg"}`}>
                {fmtMoney(m.pnl, m.currency)}
              </td>
              <td
                className={`tabular py-2.5 pr-4 text-right ${m.pnl_pct >= 0 ? "text-pos" : "text-neg"}`}
              >
                {fmtPct(m.pnl_pct)}
              </td>
              <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                %{(m.weight * 100).toFixed(1)}
              </td>
              <td className="py-2.5 text-right">
                <DeletePositionButton symbol={m.symbol} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
