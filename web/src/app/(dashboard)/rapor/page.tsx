import { getSymbolReport } from "@/lib/api";
import { SymbolSearchForm } from "./symbol-search-form";
import { ReportPanel } from "./report-panel";

export default async function RaporPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const params = await searchParams;
  const symbol = (params.symbol ?? "").trim().toUpperCase();

  const report = symbol ? await getSymbolReport(symbol) : null;

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
          Bir ABD hissesi sembolü girip raporu getir (örn. AAPL, MSFT, NVDA).
        </p>
      )}

      {symbol && !report && (
        <p className="text-sm text-neg">
          &ldquo;{symbol}&rdquo; için veri bulunamadı — sembolü kontrol et.
        </p>
      )}

      {report && <ReportPanel report={report} />}
    </>
  );
}
