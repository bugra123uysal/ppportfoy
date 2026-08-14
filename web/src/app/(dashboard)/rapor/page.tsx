import { getSymbolReport } from "@/lib/api";
import { AiCommentary } from "@/components/ai-commentary";
import { SymbolSearchForm } from "./symbol-search-form";
import { ReportPanel } from "./report-panel";
import { FibonacciPanel } from "./fibonacci-panel";
import { SymbolContextPanel } from "./symbol-context-panel";

export default async function RaporPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const params = await searchParams;
  const symbol = (params.symbol ?? "").trim().toUpperCase();

  const { report, context, commentary } = symbol
    ? await getSymbolReport(symbol)
    : { report: null, context: null, commentary: null };

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Hisse Raporu</h1>
        <p className="mt-1 text-sm text-text-faint">
          Tek bir sembol için anlık teknik durum özeti — fiyat, hacim ve indikatörlerden mekanik
          kurallarla üretilir, bir tahmin değildir.
        </p>
      </div>

      <SymbolSearchForm symbol={symbol} />

      {!symbol && (
        <p className="text-sm text-text-faint">
          Bir hisse sembolü girip raporu getir -- ABD hisseleri için AAPL, MSFT, NVDA; BIST
          hisseleri için THYAO.IS, ASELS.IS gibi &ldquo;.IS&rdquo; uzantılı semboller kullanılır.
        </p>
      )}

      {symbol && !report && (
        <p className="text-sm text-neg">
          &ldquo;{symbol}&rdquo; için veri bulunamadı — sembolü kontrol et.
        </p>
      )}

      {report && <ReportPanel report={report} />}

      {report && <AiCommentary text={commentary} />}

      {report && report.fib && <FibonacciPanel fib={report.fib} currency={report.currency} />}

      {report && !report.fib && (
        <p className="text-sm text-text-faint">
          Fibonacci seviyeleri için yeterli geçmiş veri yok.
        </p>
      )}

      {report && context && <SymbolContextPanel context={context} />}
    </>
  );
}
