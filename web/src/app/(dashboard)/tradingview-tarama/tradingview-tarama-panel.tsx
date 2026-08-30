"use client";

import { useState, useTransition } from "react";
import { AiCommentary } from "@/components/ai-commentary";
import { Panel } from "@/components/panel";
import { runTrendTradeOverlapAction } from "./actions";

export function TradingViewTaramaPanel() {
  const [pending, startTransition] = useTransition();
  const [textReport, setTextReport] = useState<string | null>(null);
  const [commentary, setCommentary] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleScan() {
    setError(null);
    startTransition(async () => {
      const result = await runTrendTradeOverlapAction();
      if (result.error || !result.data) {
        setError(result.error ?? "Tarama başarısız oldu.");
        return;
      }
      setTextReport(result.data.text_report);
      setCommentary(result.data.commentary);
    });
  }

  return (
    <Panel
      title="Genel Liste"
      subtitle="S&P 500 + Nasdaq-100 evreninin tamamında (~500 hisse -- TradingView'deki 'trading' izleme listesiyle aynı evren), Trend Bulucu'nun piyasa yapısı taraması ile My Trade'in indikatör taramasının AYNI yönde (boğa+long ya da ayı+short) kesiştiği isimler, yazılı rapor olarak. Geniş evren yüzünden tarama ~25-40 saniye sürebilir. İki bağımsız mekanik taramanın aynı hisseyi işaret etmesi bir teyittir, garanti değildir -- yatırım tavsiyesi değildir."
    >
      <div className="flex flex-col gap-5">
        <button
          type="button"
          onClick={handleScan}
          disabled={pending}
          className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Taranıyor…" : "Taramayı Çalıştır"}
        </button>

        {error && <p className="text-xs text-neg">{error}</p>}

        {textReport && (
          <p className="whitespace-pre-line text-sm leading-relaxed text-text-dim">{textReport}</p>
        )}

        <AiCommentary text={commentary} />
      </div>
    </Panel>
  );
}
