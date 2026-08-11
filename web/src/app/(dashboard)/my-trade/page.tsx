import { Suspense } from "react";
import { Panel } from "@/components/panel";
import { PanelSkeleton } from "@/components/skeleton";
import { MyTradeClient } from "./my-trade-client";
import { MoneyFlowPanel } from "./money-flow-panel";
import { FundamentalPanel } from "./fundamental-panel";
import { MoversPanel } from "./movers-panel";
import { VcpScanPanel } from "./vcp-scan-panel";
import { RotationOverlapPanel } from "./rotation-overlap-panel";

export default function MyTradePage() {
  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">My Trade</h1>
        <p className="mt-1 text-sm text-text-faint">
          İndikatör bazlı hisse tarama, sermaye akışı, fundamental değerleme + stop-loss ve
          pozisyon boyutu disiplini. Mekanik kural taraması ve eğitim amaçlı hesap aracıdır —
          yatırım tavsiyesi değildir.
        </p>
      </div>

      <Panel title="Risk/Ödül ve Stop Nereye Konur?">
        <div className="flex flex-col gap-4 text-sm text-text-dim">
          <p>
            Risk (R), giriş fiyatı ile stop arasındaki mesafedir; ödül (O) ise giriş ile hedef
            arasındaki mesafedir. Örnek: giriş 100, stop 95, hedef 115 → R=5, O=15 → RR=3:1. 3:1
            RR ile çalışan bir sistem %40 isabet oranında bile pozitif beklenti üretir; 1:1
            RR&apos;de karlı olmak için %55 üzeri isabet gerekir. 2:1 altındaki kurulumlar yakından
            izlenmeli,
            1,5:1 altındakiler genelde pas geçilmelidir.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <StopMethod
              title="1. Yapısal Stop"
              body="Son swing dibinin biraz altı (long) ya da son swing tepesinin biraz üstü (short). Fiyat oraya ulaşırsa piyasa tezini yapısal olarak reddetmiş demektir."
            />
            <StopMethod
              title="2. Volatilite Tabanlı Stop"
              body="ATR (Average True Range) çarpanı ile mesafe belirlenir — yaygın seçim 14 günlük ATR × 1,5 veya × 2. Oynak hisselerde nefes payı bırakır."
            />
            <StopMethod
              title="3. Zamansal Stop"
              body='Fiyat değil süre şartı: "Bu tez N işlem gününde çalışsın, olmadıysa çıkarım." Momentum kurulumlarında fırsat maliyetini sınırlar.'
            />
          </div>
          <p className="text-xs text-text-faint">
            Stop, &quot;katlanabileceğim kadar zarar&quot;a göre değil, &quot;grafik nerede beni
            yanıltırsa&quot; sorusuna göre belirlenir — önce stop, sonra pozisyon boyutu.
          </p>
        </div>
      </Panel>

      <Panel title="Sık Yapılan 4 Hata">
        <ol className="flex flex-col gap-2.5 text-sm text-text-dim">
          <li>
            <span className="font-medium text-text">1. Stop&apos;u sonradan aşağı itmek.</span>{" "}
            Stop bir kez konduktan sonra yukarı çekilebilir (trailing), aşağı itilmez.
          </li>
          <li>
            <span className="font-medium text-text">2. Hedefe yaklaşınca erken kâr almak.</span>{" "}
            3:1 için girilip %60&apos;ta kapatmak, gerçekte 1,8:1&apos;e çalışmak demektir.
          </li>
          <li>
            <span className="font-medium text-text">3. Aynı işlemi ısrarla yeniden denemek.</span>{" "}
            Bir kurulum çalışmadıysa hemen tekrar girmek, bağımsız işlem varsayımını çürütür.
          </li>
          <li>
            <span className="font-medium text-text">4. Stop belirlemeden pozisyon büyütmek.</span>{" "}
            &quot;Ortalamayı düşürürüm&quot; mantığı risk yönetiminin tam tersidir.
          </li>
        </ol>
      </Panel>

      <Suspense fallback={<PanelSkeleton />}>
        <MoversPanel />
      </Suspense>

      <RotationOverlapPanel />

      <VcpScanPanel />

      <MyTradeClient />

      <MoneyFlowPanel />

      <FundamentalPanel />
    </>
  );
}

function StopMethod({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface-2 p-3">
      <h3 className="text-xs font-semibold text-text">{title}</h3>
      <p className="mt-1 text-xs text-text-faint">{body}</p>
    </div>
  );
}
