"use client";

import type { StageAnalysis } from "@/lib/api";
import { SortableTh } from "@/components/sortable-th";
import { fmtMoney, fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";

type SortKey =
  | "symbol" | "severity" | "price" | "sma30w" | "sma30w_slope_pct"
  | "price_vs_sma_pct" | "weeks_in_stage" | "pct_from_52w_high";

// Lower = more urgent (Evre 4 first) -- matches the backend's own
// STAGE_SEVERITY_RANK ordering in portfoy/stage_analysis.py.
const SEVERITY_RANK: Record<number, number> = { 4: 0, 3: 1, 1: 2, 2: 3 };

const ACCESSORS: Record<SortKey, (s: StageAnalysis) => number | string> = {
  symbol: (s) => s.symbol,
  severity: (s) => SEVERITY_RANK[s.stage],
  price: (s) => s.price,
  sma30w: (s) => s.sma30w,
  sma30w_slope_pct: (s) => s.sma30w_slope_pct,
  price_vs_sma_pct: (s) => s.price_vs_sma_pct,
  weeks_in_stage: (s) => s.weeks_in_stage,
  pct_from_52w_high: (s) => s.pct_from_52w_high ?? Number.NEGATIVE_INFINITY,
};

const STAGE_BADGE_CLASS: Record<number, string> = {
  1: "bg-surface-2 text-text-dim",
  2: "bg-pos-soft text-pos",
  3: "bg-accent-soft text-accent",
  4: "bg-neg-soft text-neg",
};

const TREND_ARROW: Record<StageAnalysis["trend"], string> = {
  yukselis: "▲",
  dusus: "▼",
  yatay: "→",
};

const TREND_CLASS: Record<StageAnalysis["trend"], string> = {
  yukselis: "text-pos",
  dusus: "text-neg",
  yatay: "text-text-faint",
};

const RS_LABEL: Record<string, string> = {
  yukselis: "Güçleniyor",
  dusus: "Zayıflıyor",
  yatay: "Yatay",
};

export function StageTable({ stages }: { stages: StageAnalysis[] }) {
  const { sorted, sortKey, direction, toggle } = useSort(stages, ACCESSORS, "severity", "asc");
  const thProps = { activeKey: sortKey, direction, onSort: toggle };
  const currency = (s: StageAnalysis) => (s.symbol.endsWith(".IS") ? "TRY" : "USD") as "TRY" | "USD";

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[900px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-text-faint">
            <SortableTh label="Sembol" sortKey="symbol" {...thProps} />
            <SortableTh label="Evre" sortKey="severity" {...thProps} />
            <SortableTh label="Fiyat" sortKey="price" align="right" {...thProps} />
            <SortableTh label="30H SMA" sortKey="sma30w" align="right" {...thProps} />
            <SortableTh label="SMA Eğim" sortKey="sma30w_slope_pct" align="right" {...thProps} />
            <SortableTh label="Fiyat/SMA" sortKey="price_vs_sma_pct" align="right" {...thProps} />
            <SortableTh label="Bu Evrede" sortKey="weeks_in_stage" align="right" {...thProps} />
            <th className="py-2 pr-4 text-left font-medium">Göreli Güç</th>
            <SortableTh
              label="52H Zirveden" sortKey="pct_from_52w_high" align="right" last {...thProps}
            />
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => (
            <tr
              key={s.symbol}
              className="border-b border-border/60 transition-colors last:border-0 hover:bg-surface-2/60"
            >
              <td className="py-2.5 pr-4 font-medium text-text">{s.symbol}</td>
              <td className="py-2.5 pr-4">
                <span
                  title={s.summary_tr}
                  className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium ${STAGE_BADGE_CLASS[s.stage]}`}
                >
                  <span className={TREND_CLASS[s.trend]}>{TREND_ARROW[s.trend]}</span>
                  Evre {s.stage}
                  {s.stage_changed && (
                    <span className="ml-1 rounded bg-accent-soft px-1 py-0.5 text-[9px] font-semibold text-accent">
                      YENİ
                    </span>
                  )}
                </span>
              </td>
              <td className="tabular py-2.5 pr-4 text-right text-text">
                {fmtMoney(s.price, currency(s))}
              </td>
              <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                {fmtMoney(s.sma30w, currency(s))}
              </td>
              <td
                className={`tabular py-2.5 pr-4 text-right ${s.sma30w_slope_pct >= 0 ? "text-pos" : "text-neg"}`}
              >
                {fmtPct(s.sma30w_slope_pct)}
              </td>
              <td
                className={`tabular py-2.5 pr-4 text-right ${s.price_vs_sma_pct >= 0 ? "text-pos" : "text-neg"}`}
              >
                {fmtPct(s.price_vs_sma_pct)}
              </td>
              <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                {s.weeks_in_stage}h
              </td>
              <td className="py-2.5 pr-4 text-xs text-text-dim">
                {s.relative_strength_trend ? RS_LABEL[s.relative_strength_trend] : "—"}
              </td>
              <td className="tabular py-2.5 text-right text-text-dim">
                {s.pct_from_52w_high !== null ? fmtPct(s.pct_from_52w_high) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
