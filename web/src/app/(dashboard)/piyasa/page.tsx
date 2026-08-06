import { getBreadth, getCalendar, getRotation, getSentiment, getYieldCurve } from "@/lib/api";
import { Panel } from "@/components/panel";
import { StatTile } from "@/components/stat-tile";
import { SentimentMeter } from "@/components/sentiment-meter";
import { SENTIMENT_COMPONENT_TR } from "@/lib/sentiment";
import { eventLabel, daysLeftText } from "@/lib/calendar-text";
import { fmtPct } from "@/lib/format";

const BREADTH_HEALTHY = 60;
const BREADTH_WEAK = 40;

function breadthHealth(pctAbove200: number): { emoji: string; text: string } {
  if (pctAbove200 >= BREADTH_HEALTHY) {
    return { emoji: "🟢", text: "Katılım geniş — yükselişin tabanı sağlam." };
  }
  if (pctAbove200 <= BREADTH_WEAK) {
    return { emoji: "🔴", text: "Katılım dar — endeksi birkaç hisse taşıyor, dikkat." };
  }
  return { emoji: "🟡", text: "Katılım karışık — seçici ol." };
}

export default async function MarketCompassPage() {
  const [breadth, sentiment, rotationPayload, calendar, yieldCurve] = await Promise.all([
    getBreadth(),
    getSentiment(),
    getRotation(false),
    getCalendar(45),
    getYieldCurve(),
  ]);

  const rotation = rotationPayload.sectors;
  const leading = rotation.filter((r) => r.quadrant === "leading");
  const lagging = rotation.filter((r) => r.quadrant === "lagging");
  const today = new Date();

  return (
    <>
      <div>
        <h1 className="text-lg font-semibold text-text">Piyasa Pusulası</h1>
        <p className="mt-1 text-sm text-text-faint">
          Piyasayı okumanın 5 katmanı, artı ekonomik takvim.
        </p>
      </div>

      <Panel title="Piyasa İçi Göstergeler" subtitle="Yükseliş sağlıklı mı?">
        {breadth === null ? (
          <p className="text-sm text-text-faint">Veri alınamadı.</p>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
              <StatTile label="SMA50 Üstü" value={`%${breadth.pct_above_50.toFixed(0)}`} />
              <StatTile label="SMA200 Üstü" value={`%${breadth.pct_above_200.toFixed(0)}`} />
              <StatTile
                label="Yükselen / Düşen"
                value={`${breadth.advancers} / ${breadth.decliners}`}
              />
              <StatTile
                label="20g Zirve / Dip"
                value={`${breadth.new_high_20d} / ${breadth.new_low_20d}`}
              />
              <StatTile
                label="TRIN (Arms Index)"
                value={breadth.trin !== null ? breadth.trin.toFixed(2) : "—"}
              />
              <StatTile
                label="McClellan Osilatörü"
                value={breadth.mcclellan !== null ? breadth.mcclellan.toFixed(0) : "—"}
              />
            </div>
            <p className="text-sm text-text-dim">
              {breadthHealth(breadth.pct_above_200).emoji}{" "}
              {breadthHealth(breadth.pct_above_200).text}
              {breadth.trin !== null &&
                (breadth.trin < 1
                  ? " Hacim alıcı tarafta yoğunlaşıyor (TRIN < 1)."
                  : " Hacim satıcı tarafta yoğunlaşıyor (TRIN > 1).")}
            </p>
          </div>
        )}
      </Panel>

      <Panel
        title="Getiri Eğrisi & Kredi"
        subtitle="Resesyon ve kredi riski için erken uyarı sinyalleri"
      >
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile
              label="10 Yıllık Tahvil"
              value={yieldCurve.yield_10y !== null ? `%${yieldCurve.yield_10y.toFixed(2)}` : "—"}
            />
            <StatTile
              label="3 Aylık Bono"
              value={yieldCurve.yield_3m !== null ? `%${yieldCurve.yield_3m.toFixed(2)}` : "—"}
            />
            <StatTile
              label="Spread (10Y − 3A)"
              value={
                yieldCurve.spread_10y_3m !== null
                  ? `${yieldCurve.spread_10y_3m >= 0 ? "+" : ""}${yieldCurve.spread_10y_3m.toFixed(2)}`
                  : "—"
              }
            />
            <StatTile
              label="Kredi Spreadi (HYG/LQD, 1A)"
              value={
                yieldCurve.credit_spread_proxy_change !== null
                  ? fmtPct(yieldCurve.credit_spread_proxy_change)
                  : "—"
              }
            />
          </div>
          <p className="text-sm text-text-dim">
            {yieldCurve.inverted
              ? "🔴 Getiri eğrisi ters döndü — piyasa resesyon fiyatlıyor, tarihsel olarak güçlü bir öncü sinyal."
              : "🟢 Getiri eğrisi normal — kısa vadeli faiz uzun vadelinin altında."}
            {yieldCurve.credit_stress &&
              " Kredi spreadleri de genişliyor — risk iştahı azalıyor, dikkatli ol."}
          </p>
        </div>
      </Panel>

      <Panel title="Duygu & Volatilite" subtitle="Korku mu, iştah mı?">
        {sentiment === null ? (
          <p className="text-sm text-text-faint">Veri alınamadı.</p>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <SentimentMeter composite={sentiment.composite} />
            <div className="flex flex-col justify-center gap-2">
              {Object.entries(sentiment.components).map(([name, value]) => (
                <div key={name} className="flex items-center justify-between text-sm">
                  <span className="text-text-dim">{SENTIMENT_COMPONENT_TR[name] ?? name}</span>
                  <span className="tabular font-medium text-text">{value.toFixed(0)} / 100</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Para Akışı" subtitle="Para nereden nereye gidiyor?">
        {rotation.length === 0 ? (
          <p className="text-sm text-text-faint">Veri alınamadı.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="mb-2 text-xs font-medium text-text-dim">🟢 Lider sektörler</p>
              <p className="text-sm text-text">
                {leading.map((r) => `${r.symbol} (${r.label_tr})`).join(" · ") || "—"}
              </p>
            </div>
            <div>
              <p className="mb-2 text-xs font-medium text-text-dim">🔴 Geride kalanlar</p>
              <p className="text-sm text-text">
                {lagging.map((r) => `${r.symbol} (${r.label_tr})`).join(" · ") || "—"}
              </p>
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Ekonomik Takvim" subtitle="Önümüzdeki 45 gün">
        {calendar.length === 0 ? (
          <p className="text-sm text-text-faint">Yaklaşan önemli bir tarih yok.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {calendar.map((event, i) => (
              <li key={i} className="flex items-center justify-between text-sm">
                <span className="text-text">
                  <span className="tabular text-text-dim">
                    {new Date(event.when).toLocaleDateString("tr-TR")}
                  </span>{" "}
                  — {eventLabel(event)}
                </span>
                <span className="text-xs text-text-faint">{daysLeftText(event, today)}</span>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </>
  );
}
