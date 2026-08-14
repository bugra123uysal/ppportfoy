"use client";

import { useState, useTransition } from "react";
import type { VcpCandidate } from "@/lib/api";
import { AiCommentary } from "@/components/ai-commentary";
import { Panel } from "@/components/panel";
import { SortableTh } from "@/components/sortable-th";
import { fmtMoney, fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";
import { runVcpScanAction } from "./actions";

type SortKey =
  | "symbol" | "sector" | "price" | "change_1d" | "adr_pct" | "trailing_return_pct"
  | "range_contraction_pct" | "volume_contraction_pct" | "pct_from_52w_high" | "suggested_stop";

const ACCESSORS: Record<SortKey, (c: VcpCandidate) => number | string> = {
  symbol: (c) => c.symbol,
  sector: (c) => c.sector,
  price: (c) => c.price,
  change_1d: (c) => c.change_1d,
  adr_pct: (c) => c.adr_pct,
  trailing_return_pct: (c) => c.trailing_return_pct,
  range_contraction_pct: (c) => c.range_contraction_pct,
  volume_contraction_pct: (c) => c.volume_contraction_pct,
  pct_from_52w_high: (c) => c.pct_from_52w_high,
  suggested_stop: (c) => c.suggested_stop ?? Number.NEGATIVE_INFINITY,
};

export function VcpScanPanel() {
  const [pending, startTransition] = useTransition();
  const [candidates, setCandidates] = useState<VcpCandidate[] | null>(null);
  const [commentary, setCommentary] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleScan() {
    setError(null);
    startTransition(async () => {
      const result = await runVcpScanAction();
      if (result.error || !result.data) {
        setError(result.error ?? "Tarama başarısız oldu.");
        return;
      }
      setCandidates(result.data.candidates);
      setCommentary(result.data.commentary);
    });
  }

  const { sorted, sortKey, direction, toggle } = useSort(
    candidates ?? [], ACCESSORS, "range_contraction_pct", "asc",
  );
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <Panel
      title="VCP Taraması — Patlamaya Kurulu Adaylar"
      subtitle="Qullamaggie/Minervini tarzı gece taraması: son ~3 ayda güçlü yükselmiş, şimdi range'i daralan + hacmi kuruyan + 10/20 EMA üstünde + 52h zirveye yakın isimler. Küçük/orta ölçekli, yüksek beta'lı isimler için tasarlanmış bir yöntem — bu tanıdık büyük şirket havuzunda aday sayısı az, hatta bazı günler sıfır olabilir. Mekanik kural taraması, yatırım tavsiyesi değildir."
    >
      <div className="flex flex-col gap-5">
        <button
          type="button"
          onClick={handleScan}
          disabled={pending}
          className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Taranıyor…" : "VCP Taramasını Çalıştır"}
        </button>

        {error && <p className="text-xs text-neg">{error}</p>}

        <AiCommentary text={commentary} />

        {candidates !== null && candidates.length === 0 && (
          <p className="text-xs text-text-faint">
            Şu an bu evrende beş kriteri de karşılayan bir aday yok.
          </p>
        )}

        {candidates !== null && candidates.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-text-faint">
                  <SortableTh label="Sembol" sortKey="symbol" {...thProps} />
                  <SortableTh label="Sektör" sortKey="sector" {...thProps} />
                  <SortableTh label="Fiyat" sortKey="price" align="right" {...thProps} />
                  <SortableTh label="1G" sortKey="change_1d" align="right" {...thProps} />
                  <SortableTh
                    label="ADR%" sortKey="adr_pct" align="right" {...thProps}
                  />
                  <SortableTh
                    label="Öncü Rally" sortKey="trailing_return_pct" align="right" {...thProps}
                  />
                  <SortableTh
                    label="Range Daralması" sortKey="range_contraction_pct" align="right" {...thProps}
                  />
                  <SortableTh
                    label="Hacim Daralması" sortKey="volume_contraction_pct" align="right" {...thProps}
                  />
                  <SortableTh
                    label="52h Zirveye Uzaklık" sortKey="pct_from_52w_high" align="right" {...thProps}
                  />
                  <SortableTh
                    label="Önerilen Stop" sortKey="suggested_stop" align="right" last {...thProps}
                  />
                </tr>
              </thead>
              <tbody>
                {sorted.map((c) => (
                  <tr key={c.symbol} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4 font-medium text-text">{c.symbol}</td>
                    <td className="py-2.5 pr-4 text-text-dim">{c.sector}</td>
                    <td className="tabular py-2.5 pr-4 text-right text-text">
                      {fmtMoney(c.price, "USD")}
                    </td>
                    <td
                      className={`tabular py-2.5 pr-4 text-right ${c.change_1d >= 0 ? "text-pos" : "text-neg"}`}
                    >
                      {fmtPct(c.change_1d, 1)}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      %{c.adr_pct.toFixed(1)}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-pos">
                      {fmtPct(c.trailing_return_pct, 1)}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      %{c.range_contraction_pct.toFixed(0)}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      %{c.volume_contraction_pct.toFixed(0)}
                    </td>
                    <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                      {fmtPct(c.pct_from_52w_high, 1)}
                    </td>
                    <td className="tabular py-2.5 text-right text-text-dim">
                      {c.suggested_stop !== null ? fmtMoney(c.suggested_stop, "USD") : "—"}
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
