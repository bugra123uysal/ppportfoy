// Plain HTML GET form -- no client JS needed. Submitting navigates to
// `/rapor?symbol=...`, which re-renders the server component below with the
// new searchParams, same query-param-driven pattern as karsilastirma/page.tsx
// (that page uses fixed-choice `Link` chips; this one takes free-text input).
export function SymbolSearchForm({ symbol }: { symbol: string }) {
  return (
    <form action="/rapor" method="GET" className="flex flex-wrap items-center gap-2">
      <input
        type="text"
        name="symbol"
        defaultValue={symbol}
        placeholder="Örn. AAPL"
        autoComplete="off"
        spellCheck={false}
        className="w-40 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-faint focus:border-accent focus:outline-none"
      />
      <button
        type="submit"
        className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90"
      >
        Raporu Getir
      </button>
    </form>
  );
}
