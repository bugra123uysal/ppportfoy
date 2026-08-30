import { TradingViewTaramaPanel } from "./tradingview-tarama-panel";

export default function TradingViewTaramaPage() {
  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">TradingView Tarama</h1>
        <p className="mt-1 text-sm text-text-faint">
          Trend Bulucu ile My Trade&apos;in aynı hisseyi aynı yönde işaret ettiği anları bulur --
          piyasa yapısı (yükselen/alçalan tepe-dip) trend teyidi ile indikatör bazlı giriş sinyali
          bir arada. Bu ekran TradingView&apos;in masaüstünden veri çekmez, kendi ücretsiz Yahoo
          verisiyle çalışır; sonucu istersen ayrıca TradingView&apos;deki bir izleme listesine
          eklettirip hisseye oradan da bakabilirsin.
        </p>
      </div>

      <TradingViewTaramaPanel />
    </>
  );
}
