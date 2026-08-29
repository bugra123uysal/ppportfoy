"use client";

import { useState, useTransition } from "react";
import type { TrendCandidate } from "@/lib/api";
import { AiCommentary } from "@/components/ai-commentary";
import { Panel } from "@/components/panel";
import { SortableTh } from "@/components/sortable-th";
import { fmtMoney, fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";
import { runTrendScanAction } from "./actions";

type SortKey =
  | "symbol" | "sector" | "direction" | "score" | "price" | "change_1d"
  | "adx" | "trend_age_days" | "structural_stop";

const ACCESSORS: Record<SortKey, (c: TrendCandidate) => number | string> = {
  symbol: (c) => c.symbol,
  sector: (c) => c.sector,
  direction: (c) => c.direction,
  score: (c) => c.score,
  price: (c) => c.price,
  change_1d: (c) => c.change_1d,
  adx: (c) => c.adx ?? Number.NEGATIVE_INFINITY,
  trend_age_days: (c) => c.trend_age_days,
  structural_stop: (c) => c.structural_stop ?? Number.NEGATIVE_INFINITY,
};

const STRENGTH_LABEL: Record<TrendCandidate["strength"], string> = {
  guclu: "Güçlü",
  olusuyor: "Oluşuyor",
  erken: "Erken",
};

const STRENGTH_CLASS: Record<TrendCandidate["strength"], string> = {
  guclu: "bg-accent-soft text-accent",
  olusuyor: "bg-surface-2 text-text-dim",
  erken: "bg-surface-2 text-text-faint",
};

const MATURITY_LABEL: Record<TrendCandidate["trend_maturity"], string> = {
  saglikli: "Sağlıklı",
  zayif: "Zayıf",
  tukenebilir: "Tükenebilir",
  belirsiz: "Belirsiz",
};

const MATURITY_CLASS: Record<TrendCandidate["trend_maturity"], string> = {
  saglikli: "text-pos",
  zayif: "text-text-faint",
  tukenebilir: "text-neg",
  belirsiz: "text-text-faint",
};

export function TrendScanPanel() {
  const [pending, startTransition] = useTransition();
  const [sectors, setSectors] = useState<TrendCandidate[] | null>(null);
  const [stocks, setStocks] = useState<TrendCandidate[] | null>(null);
  const [commentary, setCommentary] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleScan() {
    setError(null);
    startTransition(async () => {
      const result = await runTrendScanAction();
      if (result.error || !result.data) {
        setError(result.error ?? "Tarama başarısız oldu.");
        return;
      }
      setSectors(result.data.sectors);
      setStocks(result.data.stocks);
      setCommentary(result.data.commentary);
    });
  }

  return (
    <Panel
      title="Trend Taraması — Sektörler ve Hisseler"
      subtitle="SECTOR_LEADER_STOCKS evrenindeki hisseler ve 11 sektör ETF'i, aynı 3 katmanlı yönteme göre taranır. Skor 3 = her üç katman da uyumlu (güçlü), 1 = yalnızca piyasa yapısı (erken). Teyit/ADX/Yaş sütunları skoru değiştirmez — trende ne kadar güvenilebileceğine dair bağımsız bağlam sinyalleridir."
    >
      <div className="flex flex-col gap-5">
        <button
          type="button"
          onClick={handleScan}
          disabled={pending}
          className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Taranıyor…" : "Trend Taramasını Çalıştır"}
        </button>

        {error && <p className="text-xs text-neg">{error}</p>}

        <AiCommentary text={commentary} />

        {sectors !== null && (
          <TrendTable
            title="Sektörler"
            rows={sectors}
            emptyText="Şu an net bir yapı sergileyen sektör ETF'i yok — çoğu konsolidasyonda."
            symbolLabel="ETF"
          />
        )}

        {stocks !== null && (
          <TrendTable
            title="Hisseler"
            rows={stocks}
            emptyText="Şu an bu evrende net bir trend yapısı sergileyen hisse yok."
            symbolLabel="Sembol"
          />
        )}
      </div>
    </Panel>
  );
}

function TrendTable({
  title,
  rows,
  emptyText,
  symbolLabel,
}: {
  title: string;
  rows: TrendCandidate[];
  emptyText: string;
  symbolLabel: string;
}) {
  const { sorted, sortKey, direction, toggle } = useSort(rows, ACCESSORS, "score", "desc");
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  if (rows.length === 0) {
    return (
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-faint">
          {title}
        </h3>
        <p className="text-xs text-text-faint">{emptyText}</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-faint">
        {title}
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1180px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-text-faint">
              <SortableTh label={symbolLabel} sortKey="symbol" {...thProps} />
              <SortableTh label="Sektör" sortKey="sector" {...thProps} />
              <SortableTh label="Yön" sortKey="direction" {...thProps} />
              <SortableTh label="Güç" sortKey="score" {...thProps} />
              <SortableTh label="Fiyat" sortKey="price" align="right" {...thProps} />
              <SortableTh label="1G" sortKey="change_1d" align="right" {...thProps} />
              <th className="py-2 pr-4 text-left font-medium">MA Rejimi</th>
              <th className="py-2 pr-4 text-left font-medium">Trendline</th>
              <th className="py-2 pr-4 text-left font-medium" title="Hacim teyidi / Para akışı uyumu">
                Teyit
              </th>
              <SortableTh
                label="ADX" sortKey="adx" align="right" {...thProps}
              />
              <SortableTh
                label="Yaş" sortKey="trend_age_days" align="right" {...thProps}
              />
              <SortableTh
                label="Yapısal Stop" sortKey="structural_stop" align="right" last {...thProps}
              />
            </tr>
          </thead>
          <tbody>
            {sorted.map((c) => (
              <tr key={`${c.symbol}-${c.sector}`} className="border-b border-border/60 last:border-0">
                <td className="py-2.5 pr-4 font-medium text-text">{c.symbol}</td>
                <td className="py-2.5 pr-4 text-text-dim">{c.sector}</td>
                <td
                  className={`py-2.5 pr-4 font-medium ${c.direction === "boga" ? "text-pos" : "text-neg"}`}
                >
                  {c.direction === "boga" ? "▲ Boğa" : "▼ Ayı"}
                  {c.newly_triggered && (
                    <span
                      title={`Yapıyı onaylayan bacak ${c.trend_age_days} gün önce başladı`}
                      className="ml-1.5 rounded bg-accent-soft px-1 py-0.5 text-[10px] font-semibold text-accent"
                    >
                      YENİ
                    </span>
                  )}
                  {c.rsi_divergence_warning && (
                    <span title="RSI diverjansı — erken tükenme uyarısı" className="ml-1.5 text-[11px]">
                      ⚠
                    </span>
                  )}
                </td>
                <td className="py-2.5 pr-4">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${STRENGTH_CLASS[c.strength]}`}
                  >
                    {STRENGTH_LABEL[c.strength]} · {c.score}/3
                  </span>
                </td>
                <td className="tabular py-2.5 pr-4 text-right text-text">
                  {fmtMoney(c.price, "USD")}
                </td>
                <td
                  className={`tabular py-2.5 pr-4 text-right ${c.change_1d >= 0 ? "text-pos" : "text-neg"}`}
                >
                  {fmtPct(c.change_1d, 1)}
                </td>
                <td className="py-2.5 pr-4 text-text-dim">{c.ma_trend_confirmed ? "✓" : "—"}</td>
                <td className="py-2.5 pr-4 text-text-dim">
                  {c.trendline_confirmed === null ? "—" : c.trendline_confirmed ? "✓" : "✗"}
                </td>
                <td className="py-2.5 pr-4 text-xs text-text-dim">
                  <span
                    title="Son günlerin hacmi 20g ortalamasının üstünde mi"
                    className={c.volume_confirmed ? "text-pos" : "text-text-faint"}
                  >
                    H
                  </span>
                  {" · "}
                  <span
                    title={`Para akışı: ${c.money_flow_signal}`}
                    className={c.money_flow_aligned ? "text-pos" : "text-text-faint"}
                  >
                    PA
                  </span>
                </td>
                <td className="tabular py-2.5 pr-4 text-right">
                  {c.adx !== null ? (
                    <span
                      title={`Trend olgunluğu: ${MATURITY_LABEL[c.trend_maturity]}`}
                      className={MATURITY_CLASS[c.trend_maturity]}
                    >
                      {c.adx.toFixed(0)}
                      {c.adx_rising === null ? "" : c.adx_rising ? " ↑" : " ↓"}
                    </span>
                  ) : (
                    <span className="text-text-faint">—</span>
                  )}
                </td>
                <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                  {c.trend_age_days}g
                </td>
                <td className="tabular py-2.5 text-right text-text-dim">
                  {c.structural_stop !== null ? fmtMoney(c.structural_stop, "USD") : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
