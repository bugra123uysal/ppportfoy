"use client";

import { useState, useTransition } from "react";
import type { TradeSignal } from "@/lib/api";
import { Panel } from "@/components/panel";
import { SortableTh } from "@/components/sortable-th";
import { fmtMoney, fmtPct } from "@/lib/format";
import { useSort } from "@/lib/use-sort";
import { runTradeScanAction } from "./actions";

type SortKey = "symbol" | "sector" | "price" | "change_1d" | "suggested_stop";

const ACCESSORS: Record<SortKey, (s: TradeSignal) => number | string> = {
  symbol: (s) => s.symbol,
  sector: (s) => s.sector,
  price: (s) => s.price,
  change_1d: (s) => s.change_1d,
  suggested_stop: (s) => s.suggested_stop ?? Number.NEGATIVE_INFINITY,
};

const GROUP_COLOR: Record<number, string> = {
  1: "var(--pos)",
  2: "#3987e5",
  3: "var(--accent)",
};

const GROUP_TITLE: Record<number, string> = {
  1: "Grup 1 — Momentum + Hacim + Bollinger",
  2: "Grup 2 — Trend + Sapma + Stoch RSI",
  3: "Grup 3 — ATR Dönüş + Trend Rengi",
};

export function TradeScanPanel({ onUseSignal }: { onUseSignal: (signal: TradeSignal) => void }) {
  const [pending, startTransition] = useTransition();
  const [signals, setSignals] = useState<TradeSignal[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleScan() {
    setError(null);
    startTransition(async () => {
      const result = await runTradeScanAction();
      if (result.error || !result.data) {
        setError(result.error ?? "Tarama başarısız oldu.");
        return;
      }
      setSignals(result.data.signals);
    });
  }

  return (
    <Panel
      title="Hisse Tarama"
      subtitle="Grup 1/2/3 indikatör eşleşmeleri — mekanik kural taraması, yatırım tavsiyesi değildir."
    >
      <div className="flex flex-col gap-5">
        <button
          type="button"
          onClick={handleScan}
          disabled={pending}
          className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Taranıyor…" : "Hisseleri Tara"}
        </button>

        {error && <p className="text-xs text-neg">{error}</p>}

        {signals !== null && (
          <div className="flex flex-col gap-6">
            {[1, 2, 3].map((group) => (
              <GroupTable
                key={group}
                group={group}
                signals={signals.filter((s) => s.groups.includes(group))}
                onUseSignal={onUseSignal}
              />
            ))}
          </div>
        )}
      </div>
    </Panel>
  );
}

function GroupTable({
  group,
  signals,
  onUseSignal,
}: {
  group: number;
  signals: TradeSignal[];
  onUseSignal: (signal: TradeSignal) => void;
}) {
  const { sorted, sortKey, direction, toggle } = useSort(
    signals, ACCESSORS, "change_1d", "desc",
  );
  const thProps = { activeKey: sortKey, direction, onSort: toggle };

  return (
    <div className="flex flex-col gap-2">
      <h3 className="flex items-center gap-1.5 text-xs font-medium text-text-dim">
        <span
          className="h-1.5 w-1.5 shrink-0 rounded-full"
          style={{ backgroundColor: GROUP_COLOR[group] }}
          aria-hidden
        />
        {GROUP_TITLE[group]}
      </h3>
      {signals.length === 0 ? (
        <p className="text-xs text-text-faint">Şu an eşleşen hisse yok.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-text-faint">
                <SortableTh label="Sembol" sortKey="symbol" {...thProps} />
                <SortableTh label="Sektör" sortKey="sector" {...thProps} />
                <SortableTh label="Fiyat" sortKey="price" align="right" {...thProps} />
                <SortableTh label="1G" sortKey="change_1d" align="right" {...thProps} />
                <SortableTh label="Önerilen Stop" sortKey="suggested_stop" align="right" {...thProps} />
                <th className="py-2 font-medium" />
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
                  <td className="tabular py-2.5 pr-4 text-right text-text-dim">
                    {s.suggested_stop !== null ? fmtMoney(s.suggested_stop, "USD") : "—"}
                  </td>
                  <td className="py-2.5 text-right">
                    <button
                      type="button"
                      onClick={() => onUseSignal(s)}
                      className="text-xs text-accent hover:underline"
                    >
                      Bu hisseyi kullan
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
