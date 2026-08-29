import { Panel } from "@/components/panel";
import { TrendScanPanel } from "./trend-scan-panel";

export default function TrendPage() {
  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Trend Bulucu</h1>
        <p className="mt-1 text-sm text-text-faint">
          Piyasa yapısı (yükselen tepe/dip vs. alçalan tepe/dip) + hareketli ortalama rejimi +
          trendline teyidinden oluşan 3 katmanlı mekanik tarama. Hangi sektörlerin ve hangi
          hisselerin şu an net bir trend içinde olduğunu sıralar. Mekanik kural taraması, yatırım
          tavsiyesi değildir.
        </p>
      </div>

      <Panel title="3 Katman Nasıl Okunur?">
        <div className="grid gap-3 text-sm text-text-dim sm:grid-cols-3">
          <LayerExplainer
            step="1"
            title="Market Yapısı"
            body="Boğa: son iki tepe ve son iki dip birbirinden yüksek (HH+HL). Ayı: ikisi de birbirinden alçak (LH+LL). Bu şart sağlanmazsa hisse konsolidasyonda sayılır ve listeye hiç girmez."
          />
          <LayerExplainer
            step="2"
            title="MA Rejimi"
            body="Fiyat + hızlı EMA (21g), yavaş SMA'nın (50g) aynı tarafında mı (Golden/Death Cross rejimi). Yapıyı teyit eder, puana katkı verir."
          />
          <LayerExplainer
            step="3"
            title="Trendline"
            body="Son swing noktalarından geçen çizginin eğimi doğru yönde mi ve fiyat çizgiyi kırmamış mı. Üçü de uyumluysa skor 3/3 — 'güçlü trend'."
          />
        </div>
        <p className="mt-4 text-xs text-text-faint">
          Ayrıca beş bağımsız bağlam sinyali gösterilir (skoru değiştirmez): <strong>Hacim</strong>{" "}
          ve <strong>Para Akışı</strong> teyidi (kırılım gerçek ilgiyle mi oluyor), <strong>ADX</strong>{" "}
          (trend gücü — yüksek ADX dönmeye başlarsa trend genelde en olgun/tükenmiş noktasındadır),{" "}
          <strong>RSI diverjansı</strong> (fiyat yeni uç yaparken RSI teyit etmiyorsa erken tükenme
          uyarısı, ⚠ ile işaretlenir) ve <strong>Trend Yaşı</strong> (yapıyı onaylayan bacak kaç
          gündür sürüyor — kısa yaş &quot;YENİ&quot; rozetiyle işaretlenir).
        </p>
      </Panel>

      <TrendScanPanel />
    </>
  );
}

function LayerExplainer({ step, title, body }: { step: string; title: string; body: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface-2 p-3">
      <h3 className="text-xs font-semibold text-text">
        {step}. {title}
      </h3>
      <p className="mt-1 text-xs text-text-faint">{body}</p>
    </div>
  );
}
