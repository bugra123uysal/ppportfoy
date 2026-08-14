"use client";

import { useState, useTransition } from "react";
import type { RotationOverlapCandidate } from "@/lib/api";
import { AiCommentary } from "@/components/ai-commentary";
import { Panel } from "@/components/panel";
import { SortableTh } from "@/components/sortable-th";
import { fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";
import { runRotationOverlapAction } from "./actions";

type SortKey = "symbol" | "sector" | "perf_1m" | "conviction";

const ACCESSORS: Record<SortKey, (c: RotationOverlapCandidate) => number | string> = {
  symbol: (c) => c.symbol,
  sector: (c) => c.sector,
  perf_1m: (c) => c.perf_1m,
  conviction: (c) => c.signals.length,
};

const SIGNAL_LABEL: Record<string, string> = {
  trade_scan_long: "Teknik AL",
  vcp: "VCP",
  money_flow_accumulation: "Para Girişi",
};

const SIGNAL_COLOR: Record<string, string> = {
  trade_scan_long: "var(--accent)",
  vcp: "#c084fc",
  money_flow_accumulation: "var(--pos)",
};

export function RotationOverlapPanel() {
  const [pending, startTransition] = useTransition();
  const [candidates, setCandidates] = useState<RotationOverlapCandidate[] | null>(null);
  const [commentary, setCommentary] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleScan() {
    setError(null);
    startTransition(async () => {
      const result = await runRotationOverlapAction();
      if (result.error || !result.data) {
        setError(result.error ?? "Tarama başarısız oldu.");
        return;
      }
      setCandidates(result.data.candidates);
      setCommentary(result.data.commentary);
    });
  }

  const { sorted, sortKey, direction, toggle } = useSort(
    candidates ?? [], ACCESSORS, "conviction", "desc",
  );
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <Panel
      title="Rotasyon + My Trade Kesişimi"
      subtitle="Şu an lider/iyileşen kadrandaki bir sektörün en güçlü hisseleri arasından, My Trade'in kendi taramalarından (teknik AL sinyali, VCP kırılımı, para girişi) en az biriyle de örtüşenler. İki bağımsız yöntemin aynı hisseyi işaret etmesi bir teyittir, garanti değildir — mekanik kural taraması, yatırım tavsiyesi değildir."
    >
      <div className="flex flex-col gap-5">
        <button
          type="button"
          onClick={handleScan}
          disabled={pending}
          className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Taranıyor…" : "Kesişimi Bul"}
        </button>

        {error && <p className="text-xs text-neg">{error}</p>}

        <AiCommentary text={commentary} />

        {candidates !== null && candidates.length === 0 && (
          <p className="text-xs text-text-faint">
            Şu an rotasyon adayları ile My Trade sinyalleri arasında ortak bir hisse yok.
          </p>
        )}

        {candidates !== null && candidates.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-text-faint">
                  <SortableTh label="Sembol" sortKey="symbol" {...thProps} />
                  <SortableTh label="Sektör" sortKey="sector" {...thProps} />
                  <SortableTh label="1 Ay" sortKey="perf_1m" align="right" {...thProps} />
                  <SortableTh label="Sinyaller" sortKey="conviction" last {...thProps} />
                </tr>
              </thead>
              <tbody>
                {sorted.map((c) => (
                  <tr key={c.symbol} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4 font-medium text-text">{c.symbol}</td>
                    <td className="py-2.5 pr-4 text-text-dim">{c.sector}</td>
                    <td
                      className={`tabular py-2.5 pr-4 text-right ${c.perf_1m >= 0 ? "text-pos" : "text-neg"}`}
                    >
                      {fmtPct(c.perf_1m, 1)}
                    </td>
                    <td className="py-2.5">
                      <div className="flex flex-wrap gap-1.5">
                        {c.signals.map((signal) => (
                          <span
                            key={signal}
                            className="rounded-full px-2 py-0.5 text-[11px] font-medium text-black"
                            style={{ backgroundColor: SIGNAL_COLOR[signal] ?? "var(--accent)" }}
                          >
                            {SIGNAL_LABEL[signal] ?? signal}
                          </span>
                        ))}
                      </div>
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
