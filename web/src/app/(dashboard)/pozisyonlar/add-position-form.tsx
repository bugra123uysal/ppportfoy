"use client";

import { useActionState, useEffect, useRef, useState } from "react";
import type { SymbolQuote } from "@/lib/api";
import { addPositionAction, lookupSymbolAction, type FormState } from "./actions";

// Mirrors portfoy/security.py's normalize_symbol regex -- catches an
// obviously-malformed ticker before it ever reaches the network, and gates
// the live lookup below so we don't fire a request per keystroke on input
// that clearly isn't a finished symbol yet.
const SYMBOL_PATTERN = /^\^?[A-Z0-9][A-Z0-9.\-=]{0,14}$/;
const LOOKUP_DEBOUNCE_MS = 400;

const initialState: FormState = { error: null };

export function AddPositionForm() {
  const [state, action, pending] = useActionState(addPositionAction, initialState);
  const formRef = useRef<HTMLFormElement>(null);
  const wasPending = useRef(false);

  const [symbol, setSymbol] = useState("");
  const [avgCost, setAvgCost] = useState("");
  // Keyed by the symbol it was fetched for, so a result for a since-edited
  // symbol is simply never shown (`hasFreshResult` below) instead of being
  // eagerly cleared -- avoids a setState call that runs synchronously on
  // every symbol edit.
  const [result, setResult] = useState<{
    symbol: string;
    quote: SymbolQuote | null;
    notFound: boolean;
    error: string | null;
  } | null>(null);

  const normalizedSymbol = symbol.trim().toUpperCase();
  const symbolFormatValid = SYMBOL_PATTERN.test(normalizedSymbol);
  const hasFreshResult = result !== null && result.symbol === normalizedSymbol;
  const quote = hasFreshResult ? result.quote : null;
  const notFound = hasFreshResult ? result.notFound : false;
  const lookupError = hasFreshResult ? result.error : null;
  const looking = symbolFormatValid && !hasFreshResult;
  // Only block submission on a *confirmed* miss -- a transient lookup
  // failure must never stop an otherwise-valid submit (the server re-checks
  // existence authoritatively either way, see api/index.py's add_position).
  const knownInvalidSymbol = symbolFormatValid && notFound;

  useEffect(() => {
    if (!symbolFormatValid) return;
    let ignore = false;
    const timer = setTimeout(() => {
      lookupSymbolAction(normalizedSymbol).then((r) => {
        if (ignore) return;
        setResult({ symbol: normalizedSymbol, quote: r.quote, notFound: r.notFound, error: r.error });
      });
    }, LOOKUP_DEBOUNCE_MS);
    return () => {
      ignore = true;
      clearTimeout(timer);
    };
  }, [normalizedSymbol, symbolFormatValid]);

  // Resets the form only after a submit that just succeeded (pending flips
  // true -> false with no error) -- not on mount, where state also starts
  // out as {error: null}.
  useEffect(() => {
    if (wasPending.current && !pending && state.error === null) {
      formRef.current?.reset();
      setSymbol("");
      setAvgCost("");
      setResult(null);
    }
    wasPending.current = pending;
  }, [pending, state]);

  return (
    <form ref={formRef} action={action} className="flex flex-wrap items-end gap-3">
      <Field label="Sembol" htmlFor="symbol">
        <input
          id="symbol"
          name="symbol"
          required
          placeholder="AAPL"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          autoComplete="off"
          spellCheck={false}
          className="tabular w-28 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm uppercase text-text outline-none transition-colors focus:border-accent"
        />
      </Field>
      <Field label="Adet" htmlFor="quantity">
        <input
          id="quantity"
          name="quantity"
          type="number"
          step="any"
          min={0}
          required
          className="tabular w-24 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
        />
      </Field>
      <Field label="Ort. Maliyet" htmlFor="avg_cost">
        <div className="flex items-center gap-1.5">
          <input
            id="avg_cost"
            name="avg_cost"
            type="number"
            step="any"
            min={0}
            required
            value={avgCost}
            onChange={(e) => setAvgCost(e.target.value)}
            className="tabular w-28 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
          />
          {quote && (
            <button
              type="button"
              title={`Şu anki fiyatı kullan: ${quote.price.toFixed(2)}`}
              onClick={() => setAvgCost(quote.price.toFixed(2))}
              className="rounded-lg border border-border px-2 py-2 text-xs text-text-faint transition-colors hover:border-accent hover:text-accent"
            >
              Şu anki fiyat
            </button>
          )}
        </div>
      </Field>
      <Field label="Not (opsiyonel)" htmlFor="notes">
        <input
          id="notes"
          name="notes"
          className="w-40 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none transition-colors focus:border-accent"
        />
      </Field>
      <button
        type="submit"
        disabled={pending || knownInvalidSymbol}
        className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Ekleniyor…" : "Ekle"}
      </button>

      <div className="w-full text-xs">
        {looking && <p className="text-text-faint">Sembol kontrol ediliyor…</p>}
        {!looking && quote && (
          <p className="text-pos">
            ✓ {quote.symbol} bulundu — {quote.currency === "TRY" ? "₺" : "$"}
            {quote.price.toLocaleString("tr-TR", { maximumFractionDigits: 2 })}
            {" "}({quote.change_pct >= 0 ? "+" : ""}
            {quote.change_pct.toFixed(1)}%)
          </p>
        )}
        {!looking && lookupError && <p className="text-neg">{lookupError}</p>}
      </div>

      {state.error && <p className="w-full text-xs text-neg">{state.error}</p>}
    </form>
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
