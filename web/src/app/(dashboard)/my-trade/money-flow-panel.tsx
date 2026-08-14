"use client";

import { useState, useTransition } from "react";
import type { MoneyFlowSignal } from "@/lib/api";
import { AiCommentary } from "@/components/ai-commentary";
import { Panel } from "@/components/panel";
import { SortableTh } from "@/components/sortable-th";
import { fmtMoney, fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";
import { runMoneyFlowScanAction } from "./actions";

type SortKey =
  | "symbol" | "sector" | "price" | "change_1d" | "cmf" | "mfi"
  | "obv_trend" | "institutional_pct" | "insider_net_pct_6m";

const OBV_RANK: Record<MoneyFlowSignal["obv_trend"], number> = { yukselis: 1, yatay: 0, dusus: -1 };

const ACCESSORS: Record<SortKey, (s: MoneyFlowSignal) => number | string> = {
  symbol: (s) => s.symbol,
  sector: (s) => s.sector,
  price: (s) => s.price,
  change_1d: (s) => s.change_1d,
  cmf: (s) => s.cmf ?? Number.NEGATIVE_INFINITY,
  mfi: (s) => s.mfi ?? Number.NEGATIVE_INFINITY,
  obv_trend: (s) => OBV_RANK[s.obv_trend],
  institutional_pct: (s) => s.institutional_pct ?? Number.NEGATIVE_INFINITY,
  insider_net_pct_6m: (s) => s.insider_net_pct_6m ?? Number.NEGATIVE_INFINITY,
};

const CMF_COLOR: Record<MoneyFlowSignal["cmf_signal"], string> = {
  accumulation: "var(--pos)",
  distribution: "var(--neg)",
  notr: "var(--text-faint)",
};

const CMF_LABEL: Record<MoneyFlowSignal["cmf_signal"], string> = {
  accumulation: "Alım Baskısı",
  distribution: "Satış Baskısı",
  notr: "Nötr",
};

const OBV_LABEL: Record<MoneyFlowSignal["obv_trend"], string> = {
  yukselis: "Yükseliş",
  dusus: "Düşüş",
  yatay: "Yatay",
};

const OBV_CLASS: Record<MoneyFlowSignal["obv_trend"], string> = {
  yukselis: "text-pos",
  dusus: "text-neg",
  yatay: "text-text-faint",
};

export function MoneyFlowPanel() {
  const [pending, startTransition] = useTransition();
  const [signals, setSignals] = useState<MoneyFlowSignal[] | null>(null);
  const [commentary, setCommentary] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleScan() {
    setError(null);
    startTransition(async () => {
      const result = await runMoneyFlowScanAction();
      if (result.error || !result.data) {
        setError(result.error ?? "Tarama başarısız oldu.");
        return;
      }
      setSignals(result.data.signals);
      setCommentary(result.data.commentary);
    });
  }

  const { sorted, sortKey, direction, toggle } = useSort(signals ?? [], ACCESSORS, "cmf", "desc");
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <Panel
      title="Sermaye Akışı"
      subtitle="Chaikin Money Flow + Money Flow Index + OBV (günlük, fiyat/hacimden) ve kurumsal sahiplik + son 6 ayda içeriden net alım/satım (SEC 13F/Form 4, Yahoo üzerinden) — bilgi amaçlıdır, yatırım tavsiyesi değildir."
    >
      <div className="flex flex-col gap-5">
        <button
          type="button"
          onClick={handleScan}
          disabled={pending}
          className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Taranıyor…" : "Sermaye Akışını Tara"}
        </button>

        {error && <p className="text-xs text-neg">{error}</p>}

        <AiCommentary text={commentary} />

        {signals !== null && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-text-faint">
                  <SortableTh label="Sembol" sortKey="symbol" {...thProps} />
                  <SortableTh label="Sektör" sortKey="sector" {...thProps} />
                  <SortableTh label="Fiyat" sortKey="price" align="right" {...thProps} />
                  <SortableTh label="1G" sortKey="change_1d" align="right" {...thProps} />
                  <SortableTh label="CMF" sortKey="cmf" {...thProps} />
                  <SortableTh label="MFI" sortKey="mfi" align="right" {...thProps} />
                  <SortableTh label="OBV" sortKey="obv_trend" {...thProps} />
                  <SortableTh label="Kurumsal %" sortKey="institutional_pct" align="right" {...thProps} />
                  <SortableTh
                    label="İçeriden Net 6A" sortKey="insider_net_pct_6m" align="right" last {...thProps}
                  />
                </tr>
              </thead>
              <tbody>
                {sorted.map((s) => (
                  <tr key={s.symbol} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4 font-medium text-text">{s.symbol}</td>
                    <td className="py-2.5 pr-4 text-text-dim">{s.sector}</td>
                    <td className="tabular py-2.5 pr-4 text-right text-text">
                      {fmtMoney(s.price, "USD")}
                    </td>
                    <td
                      className={`tabular py-2.5 pr-4 text-right ${s.change_1d >= 0 ? "text-pos" : "text-neg"}`}
                    >
                      {fmtPct(s.change_1d, 1)}
                    </td>
                    <td className="py-2.5 pr-4">
                      <span className="inline-flex items-center gap-1.5 text-text-dim">
                        <span
                          className="h-1.5 w-1.5 shrink-0 rounded-full"
                          style={{ backgroundColor: CMF_COLOR[s.cmf_signal] }}
                          aria-hidden
                        />
                        {CMF_LABEL[s.cmf_signal]}
                      </span>
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {s.mfi !== null ? s.mfi.toFixed(0) : "—"}
                    </td>
                    <td className={`py-2.5 pr-4 ${OBV_CLASS[s.obv_trend]}`}>
                      {OBV_LABEL[s.obv_trend]}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {s.institutional_pct !== null ? `%${s.institutional_pct.toFixed(0)}` : "—"}
                    </td>
                    <td
                      className={`tabular py-2.5 text-right ${
                        s.insider_net_pct_6m === null
                          ? "text-text-faint"
                          : s.insider_net_pct_6m > 0
                            ? "text-pos"
                            : s.insider_net_pct_6m < 0
                              ? "text-neg"
                              : "text-text-faint"
                      }`}
                    >
                      {s.insider_net_pct_6m !== null ? fmtPct(s.insider_net_pct_6m, 1) : "—"}
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
