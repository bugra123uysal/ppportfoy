"use client";

import { useState, useTransition } from "react";
import type { FundamentalSnapshot } from "@/lib/api";
import { Panel } from "@/components/panel";
import { SortableTh } from "@/components/sortable-th";
import { fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";
import { runFundamentalScanAction } from "./actions";

type SortKey =
  | "symbol" | "sector" | "pe" | "peg" | "ev_ebitda" | "revenue_growth"
  | "operating_margin" | "roe" | "debt_to_equity" | "verdict";

const VERDICT_RANK: Record<FundamentalSnapshot["verdict"], number> = {
  ucuz: 2, makul: 1, belirsiz: 0, pahali: -1,
};

const ACCESSORS: Record<SortKey, (s: FundamentalSnapshot) => number | string> = {
  symbol: (s) => s.symbol,
  sector: (s) => s.sector,
  pe: (s) => s.pe ?? Number.POSITIVE_INFINITY,
  peg: (s) => s.peg ?? Number.POSITIVE_INFINITY,
  ev_ebitda: (s) => s.ev_ebitda ?? Number.POSITIVE_INFINITY,
  revenue_growth: (s) => s.revenue_growth ?? Number.NEGATIVE_INFINITY,
  operating_margin: (s) => s.operating_margin ?? Number.NEGATIVE_INFINITY,
  roe: (s) => s.roe ?? Number.NEGATIVE_INFINITY,
  debt_to_equity: (s) => s.debt_to_equity ?? Number.POSITIVE_INFINITY,
  verdict: (s) => VERDICT_RANK[s.verdict],
};

const VERDICT_LABEL: Record<FundamentalSnapshot["verdict"], string> = {
  ucuz: "Ucuz", makul: "Makul", pahali: "Pahalı", belirsiz: "Belirsiz",
};

const VERDICT_CLASS: Record<FundamentalSnapshot["verdict"], string> = {
  ucuz: "bg-pos-soft text-pos",
  makul: "bg-surface-2 text-text-dim",
  pahali: "bg-neg-soft text-neg",
  belirsiz: "bg-surface-2 text-text-faint",
};

export function FundamentalPanel() {
  const [pending, startTransition] = useTransition();
  const [signals, setSignals] = useState<FundamentalSnapshot[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleScan() {
    setError(null);
    startTransition(async () => {
      const result = await runFundamentalScanAction();
      if (result.error || !result.data) {
        setError(result.error ?? "Tarama başarısız oldu.");
        return;
      }
      setSignals(result.data.signals);
    });
  }

  const { sorted, sortKey, direction, toggle } = useSort(signals ?? [], ACCESSORS, "peg", "asc");
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <Panel
      title="Fundamental Tarama"
      subtitle="F/K, PEG, FD/FAVÖK, gelir büyümesi, marj, ROE, borç/özkaynak (Yahoo Finance) — değerleme okuması, yatırım tavsiyesi değildir."
    >
      <div className="flex flex-col gap-5">
        <button
          type="button"
          onClick={handleScan}
          disabled={pending}
          className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Taranıyor…" : "Fundamental Taramayı Çalıştır"}
        </button>

        {error && <p className="text-xs text-neg">{error}</p>}

        {signals !== null && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-text-faint">
                  <SortableTh label="Sembol" sortKey="symbol" {...thProps} />
                  <SortableTh label="Sektör" sortKey="sector" {...thProps} />
                  <SortableTh label="F/K" sortKey="pe" align="right" {...thProps} />
                  <SortableTh label="PEG" sortKey="peg" align="right" {...thProps} />
                  <SortableTh label="FD/FAVÖK" sortKey="ev_ebitda" align="right" {...thProps} />
                  <SortableTh label="Gelir Büyümesi" sortKey="revenue_growth" align="right" {...thProps} />
                  <SortableTh label="Faaliyet Marjı" sortKey="operating_margin" align="right" {...thProps} />
                  <SortableTh label="ROE" sortKey="roe" align="right" {...thProps} />
                  <SortableTh label="Borç/Özkaynak" sortKey="debt_to_equity" align="right" {...thProps} />
                  <SortableTh label="Değerleme" sortKey="verdict" last {...thProps} />
                </tr>
              </thead>
              <tbody>
                {sorted.map((s) => (
                  <tr key={s.symbol} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4 font-medium text-text">{s.symbol}</td>
                    <td className="py-2.5 pr-4 text-text-dim">{s.sector}</td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {s.pe !== null ? s.pe.toFixed(1) : "—"}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {s.peg !== null ? s.peg.toFixed(2) : "—"}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {s.ev_ebitda !== null ? s.ev_ebitda.toFixed(1) : "—"}
                    </td>
                    <td
                      className={`tabular py-2.5 pr-4 text-right ${
                        s.revenue_growth === null
                          ? "text-text-faint"
                          : s.revenue_growth >= 0 ? "text-pos" : "text-neg"
                      }`}
                    >
                      {s.revenue_growth !== null ? fmtPct(s.revenue_growth, 1) : "—"}
                    </td>
                    <td
                      className={`tabular py-2.5 pr-4 text-right ${
                        s.operating_margin === null
                          ? "text-text-faint"
                          : s.operating_margin >= 0 ? "text-pos" : "text-neg"
                      }`}
                    >
                      {s.operating_margin !== null ? fmtPct(s.operating_margin, 1) : "—"}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {s.roe !== null ? fmtPct(s.roe, 1) : "—"}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {s.debt_to_equity !== null ? s.debt_to_equity.toFixed(2) : "—"}
                    </td>
                    <td className="py-2.5 text-right">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${VERDICT_CLASS[s.verdict]}`}
                      >
                        {VERDICT_LABEL[s.verdict]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Panel>
  );
}
