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
  4: "#c084fc",
};

const GROUP_TITLE: Record<number, string> = {
  1: "Grup 1 — Momentum + Hacim + Bollinger",
  2: "Grup 2 — Trend + Sapma + Stoch RSI",
  3: "Grup 3 — ATR Dönüş + Trend Rengi",
  4: "Grup 4 — Stoch RSI + EMA + Medyan",
};

const GROUP_DESCRIPTION: Record<"long" | "short", Record<number, string>> = {
  long: {
    1: "Stochastic Momentum Index sıfırın altındayken yukarı dönüyor (aşırı satımdan çıkış); ortalamanın üzerinde hacimle gelen yeşil mum bunu doğruluyor; fiyat Bollinger alt bandına değip sıçramış ya da orta banda geri dönmüş.",
    2: "21 günlük EMA yükseliyor (ana trend yukarı); fiyat bu ortalamanın en az %5 altına sarkmış — trend içi ucuz bir sapma/dip; Stoch RSI %K çizgisi %D'yi yukarı kesiyor (momentum dönüşü).",
    3: "ATR tabanlı takip-stop çizgisi (UT Bot) alım yönüne dönüyor; CCI tabanlı trend rengi (Trend Magic) pozitif — yani trend rengi de alımı destekliyor.",
    4: "14 günlük Stoch RSI %K çizgisi kendi 14 günlük EMA'sını yukarı kesiyor; TradingView'in yerleşik Medyan indikatörü (hl2'nin kendi EMA'sına göre) yeşil — momentum dönüşü medyan trendiyle doğrulanmış.",
  },
  short: {
    1: "Stochastic Momentum Index sıfırın üzerindeyken aşağı dönüyor (aşırı alımdan çıkış); ortalamanın üzerinde hacimle gelen kırmızı mum bunu doğruluyor; fiyat Bollinger üst bandına değip gerilemiş ya da orta bandın altına inmiş.",
    2: "21 günlük EMA düşüyor (ana trend aşağı); fiyat bu ortalamanın en az %5 üzerine sıçramış — trend içi pahalı bir tepki/rally; Stoch RSI %K çizgisi %D'yi aşağı kesiyor (momentum dönüşü).",
    3: "ATR tabanlı takip-stop çizgisi (UT Bot) satış yönüne dönüyor; CCI tabanlı trend rengi (Trend Magic) negatif — yani trend rengi de satışı destekliyor.",
    4: "14 günlük Stoch RSI %K çizgisi kendi 14 günlük EMA'sını aşağı kesiyor. (Notlarda satış tarafı yalnızca bu çaprazlamayla tanımlı — Medyan teyidi alım tarafına özgü.)",
  },
};

const GROUPS = [1, 2, 3, 4];

export function TradeScanPanel({ onUseSignal }: { onUseSignal: (signal: TradeSignal) => void }) {
  const [pending, startTransition] = useTransition();
  const [signals, setSignals] = useState<TradeSignal[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [direction, setDirection] = useState<"long" | "short">("long");

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

  const directionSignals = signals?.filter((s) => s.direction === direction) ?? null;

  return (
    <Panel
      title="Hisse Tarama"
      subtitle={
        direction === "long"
          ? "Grup 1-4 bullish indikatör eşleşmeleri — mekanik kural taraması, yatırım tavsiyesi değildir."
          : "Grup 1-4 bearish eşleşmeleri — açığa satış borç/marj/squeeze riski taşır, yatırım tavsiyesi değildir."
      }
    >
      <div className="flex flex-col gap-5">
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleScan}
            disabled={pending}
            className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {pending ? "Taranıyor…" : "Hisseleri Tara"}
          </button>
          <div className="flex rounded-lg border border-border p-0.5 text-xs">
            <DirectionButton
              label="Long"
              active={direction === "long"}
              onClick={() => setDirection("long")}
            />
            <DirectionButton
              label="Short"
              active={direction === "short"}
              onClick={() => setDirection("short")}
            />
          </div>
        </div>

        {error && <p className="text-xs text-neg">{error}</p>}

        {directionSignals !== null && (
          <div className="flex flex-col gap-6">
            {GROUPS.map((group) => (
              <GroupTable
                key={group}
                group={group}
                direction={direction}
                signals={directionSignals.filter((s) => s.groups.includes(group))}
                onUseSignal={onUseSignal}
              />
            ))}
          </div>
        )}
      </div>
    </Panel>
  );
}

function DirectionButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
        active ? "bg-accent text-black" : "text-text-dim hover:text-text"
      }`}
    >
      {label}
    </button>
  );
}

function GroupTable({
  group,
  direction,
  signals,
  onUseSignal,
}: {
  group: number;
  direction: "long" | "short";
  signals: TradeSignal[];
  onUseSignal: (signal: TradeSignal) => void;
}) {
  const { sorted, sortKey, direction: sortDirection, toggle } = useSort(
    signals, ACCESSORS, "change_1d", "desc",
  );
  const thProps = { activeKey: sortKey, direction: sortDirection, onSort: toggle };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col gap-1">
        <h3 className="flex items-center gap-1.5 text-xs font-medium text-text-dim">
          <span
            className="h-1.5 w-1.5 shrink-0 rounded-full"
            style={{ backgroundColor: GROUP_COLOR[group] }}
            aria-hidden
          />
          {GROUP_TITLE[group]}
        </h3>
        <p className="pl-3 text-xs text-text-faint">{GROUP_DESCRIPTION[direction][group]}</p>
      </div>
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
