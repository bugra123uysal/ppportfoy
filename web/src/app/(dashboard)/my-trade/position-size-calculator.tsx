"use client";

import { useState } from "react";
import type { TradeSignal } from "@/lib/api";
import { Panel } from "@/components/panel";
import { fmtMoney } from "@/lib/format";

const DEFAULT_RISK_PCT = 1;

export function PositionSizeCalculator({ prefill }: { prefill: TradeSignal | null }) {
  const [portfolioValue, setPortfolioValue] = useState("100000");
  const [entry, setEntry] = useState("");
  const [stop, setStop] = useState("");
  const [riskPct, setRiskPct] = useState(String(DEFAULT_RISK_PCT));
  // Adjust entry/stop when a *new* prefill arrives, without clobbering
  // further manual edits -- tracking the last-applied symbol+direction key
  // during render (React's documented pattern for "adjust state when a
  // prop changes") instead of an effect, which would set state after an
  // extra render. Keyed on direction too: the same symbol can appear in
  // both the long and short tables, and re-picking it from the other
  // table must still refresh entry/stop.
  const [appliedKey, setAppliedKey] = useState<string | null>(null);
  if (prefill) {
    const key = `${prefill.symbol}:${prefill.direction}`;
    if (key !== appliedKey) {
      setAppliedKey(key);
      setEntry(String(prefill.price));
      if (prefill.suggested_stop !== null) {
        setStop(String(prefill.suggested_stop));
      }
    }
  }

  const portfolio = Number(portfolioValue);
  const entryPrice = Number(entry);
  const stopPrice = Number(stop);
  const risk = Number(riskPct);
  // Long: stop sits below entry. Short: stop sits above entry (the price
  // rising is the risk). The distance that matters for sizing is always
  // the absolute gap between the two, regardless of direction.
  const stopDistance = Math.abs(entryPrice - stopPrice);
  const isValid =
    Number.isFinite(portfolio) &&
    Number.isFinite(entryPrice) &&
    Number.isFinite(stopPrice) &&
    Number.isFinite(risk) &&
    portfolio > 0 &&
    risk > 0 &&
    stopDistance > 0;
  const riskAmount = isValid ? portfolio * (risk / 100) : null;
  const lots = isValid && riskAmount !== null ? Math.floor(riskAmount / stopDistance) : null;

  return (
    <Panel
      title="Pozisyon Boyutu Hesaplayıcı"
      subtitle="%1 kuralı: stop tetiklenirse kayıp, portföyün seçtiğin risk yüzdesini aşmasın."
    >
      <div className="flex flex-col gap-5">
        {prefill && (
          <p className="text-xs text-text-faint">
            <span className="font-medium text-text">{prefill.symbol}</span> (
            {prefill.direction === "short" ? "short" : "long"}) için dolduruldu — stop önerisi
            ATR(14) tabanlıdır, gerekirse elle değiştir.
            {prefill.direction === "short" &&
              " Short'ta stop girişin üzerindedir; açığa satış borç/marj uygunluğunu brokerinden kontrol et."}
          </p>
        )}
        <div className="flex flex-wrap items-end gap-3">
          <Field label="Portföy Değeri" htmlFor="portfolio">
            <input
              id="portfolio"
              value={portfolioValue}
              onChange={(e) => setPortfolioValue(e.target.value)}
              inputMode="decimal"
              className="tabular w-32 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
            />
          </Field>
          <Field label="Giriş Fiyatı" htmlFor="entry">
            <input
              id="entry"
              value={entry}
              onChange={(e) => setEntry(e.target.value)}
              inputMode="decimal"
              className="tabular w-28 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
            />
          </Field>
          <Field label="Stop Fiyatı" htmlFor="stop">
            <input
              id="stop"
              value={stop}
              onChange={(e) => setStop(e.target.value)}
              inputMode="decimal"
              className="tabular w-28 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
            />
          </Field>
          <Field label="Risk %" htmlFor="risk">
            <input
              id="risk"
              value={riskPct}
              onChange={(e) => setRiskPct(e.target.value)}
              inputMode="decimal"
              className="tabular w-20 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
            />
          </Field>
        </div>

        {isValid ? (
          <div className="flex flex-wrap gap-6">
            <Result label="Stop Mesafesi" value={fmtMoney(stopDistance, "USD")} />
            <Result label="Riske Edilen Tutar" value={fmtMoney(riskAmount ?? 0, "USD")} />
            <Result label="Uygun Lot" value={String(lots ?? 0)} emphasize />
          </div>
        ) : (
          <p className="text-xs text-text-faint">
            Giriş fiyatı stop fiyatına eşit olmamalı; tüm alanları doldur.
          </p>
        )}
      </div>
    </Panel>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="text-xs text-text-faint">
        {label}
      </label>
      {children}
    </div>
  );
}

function Result({
  label,
  value,
  emphasize,
}: {
  label: string;
  value: string;
  emphasize?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-text-faint">{label}</p>
      <p className={`tabular ${emphasize ? "text-lg font-semibold text-accent" : "text-sm text-text"}`}>
        {value}
      </p>
    </div>
  );
}
